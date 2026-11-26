from datetime import datetime
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select

from core.db import transaction
from core.queueing import submit
from core.records import get, insert, need, scan, update
from domain import learning
from domain.lead_shifts_model import lead_shifts
from domain.patrol_windows_model import patrol_windows
from domain.trail_notices_model import trail_notices
from domain.trail_routes_model import trail_routes
from domain.weight_lab_model import distance_weights, weight_trials

ENABLED_CODE = 'ENABLED'
RUNNING_STATES = ('排队中', '试评中')
TERMINAL_STATES = ('暂缓', '已启用', '未启用')


def _now():
    return datetime.now(learning.TZ_OFFSET).isoformat(timespec='minutes')


def assign_lead(conn, user, data):
    window = get(conn, patrol_windows, data.window)
    route = get(conn, trail_routes, window['route'], lock=True)
    need(route['active'], '路线已停用')
    count = conn.execute(select(lead_shifts.c.code).where(lead_shifts.c.window == data.window,
                         lead_shifts.c.state != '已交回')).all()
    need(len(count) < route['max_leads'], '潮窗领班名额已满')
    existing = conn.execute(select(lead_shifts.c.code).where(lead_shifts.c.window == data.window,
                            lead_shifts.c.contact == data.contact)).first()
    need(existing is None, '该队内联络号已领过此潮窗')
    return insert(conn, lead_shifts, **data.model_dump(), state='已领班',
                  checkpoint=None, on_site=None, ended_at=None)


def check_in(conn, user, data):
    from domain.calendar_clock import local_time
    shift = get(conn, lead_shifts, data.shift)
    window = get(conn, patrol_windows, shift['window'])
    route = get(conn, trail_routes, window['route'], lock=True)
    shift = get(conn, lead_shifts, data.shift, lock=True)
    arrival = local_time(data.arrived_at).isoformat(sep=' ',timespec='minutes')
    need(shift['state'] == '已领班', '只有尚未签到的领班可登记到场')
    need(data.checkpoint == route['checkpoint'], '扫码检查点与排班路线不符')
    need(window['opens'] <= arrival < window['closes'], '不在当班的跨日签到窗口内')
    closed = conn.execute(select(trail_notices.c.code).where(
        trail_notices.c.route == route['code'], trail_notices.c.status == '封闭',
        trail_notices.c.begins <= arrival, trail_notices.c.until > arrival)).first()
    need(route['active'] and closed is None, '此路线在签到时刻封闭，保留已领班状态')
    return update(conn, lead_shifts, data.shift, state='已签到', checkpoint=data.checkpoint, on_site=arrival)


def _hand_back_moment(data):
    from domain.calendar_clock import local_time
    for name in ('ended_at', 'handed_back_at', 'hand_back_at', 'returned_at', 'at', 'time'):
        value = getattr(data, name, None)
        if value:
            return local_time(value).isoformat(sep=' ', timespec='minutes')
    return _now()


def hand_back(conn, user, data):
    shift = get(conn, lead_shifts, data.shift, lock=True)
    need(shift['state'] == '已签到', '领班签到后才可签回')
    ended_at = _hand_back_moment(data)
    return update(conn, lead_shifts, data.shift, state='已交回', ended_at=ended_at)


# ---------------------------------------------------------------------------
# Distance weights singleton
# ---------------------------------------------------------------------------

def _weights_row(conn, lock=False):
    query = select(distance_weights).where(distance_weights.c.code == ENABLED_CODE)
    if lock:
        query = query.with_for_update()
    return conn.execute(query).mappings().first()


def ensure_weights(conn, user=None, lock=False):
    row = _weights_row(conn, lock=lock)
    if row is None:
        conn.execute(distance_weights.insert().values(
            code=ENABLED_CODE, phase_weight=learning.DEFAULT_WEIGHTS['phase'],
            duration_weight=learning.DEFAULT_WEIGHTS['duration'],
            neighbor_count=learning.NEIGHBOR_LIMIT,
            updated_by=user['sub'] if user else None, updated_at=_now()))
        row = _weights_row(conn, lock=lock)
    return dict(row)


def current_weights(conn, lock=False):
    row = ensure_weights(conn, lock=lock)
    return {'phase': row['phase_weight'], 'duration': row['duration_weight']}


def get_weights(conn):
    return serialize_weights(ensure_weights(conn))


def serialize_weights(row):
    return {'code': ENABLED_CODE,
            'phase_weight': row['phase_weight'],
            'duration_weight': row['duration_weight'],
            'phase': row['phase_weight'],
            'duration': row['duration_weight'],
            'neighbor_count': row.get('neighbor_count') if isinstance(row, dict) else row['neighbor_count'],
            'updated_by': row['updated_by'], 'updated_at': row['updated_at'],
            'trial_code': row['trial_code'],
            'weights': {'phase': row['phase_weight'], 'duration': row['duration_weight']}}


# ---------------------------------------------------------------------------
# Replay sample construction (frozen at trial initiation)
# ---------------------------------------------------------------------------

def _world(conn):
    windows = {row['code']: row for row in scan(conn, patrol_windows)}
    shifts = scan(conn, lead_shifts)
    handed = [s for s in shifts if s['state'] == '已交回' and s.get('on_site')]
    return windows, handed


def _ended_before_open(shift, window, target_opens):
    # A 班次 has ended when its patrol window closed; stored calendar times are
    # the coherent replay clock (an auto wall-clock hand-back stamp is not).
    return learning.parse_time(window['closes']) < learning.parse_time(target_opens)


def eligible_neighbors(target_window, handed, windows, exclude_shift=None):
    candidates = []
    for neighbor in handed:
        if exclude_shift is not None and neighbor['code'] == exclude_shift:
            continue
        neighbor_window = windows.get(neighbor['window'])
        if neighbor_window is None:
            continue
        if neighbor_window['route'] != target_window['route']:
            continue
        if neighbor_window['phase'] != target_window['phase']:
            continue
        if not _ended_before_open(neighbor, neighbor_window, target_window['opens']):
            continue
        candidates.append((neighbor, neighbor_window))
    return candidates


def build_replay_batch(conn):
    """Freeze the replay batch.

    Returns (active_route_codes, samples, missing_routes). Every initiation-open
    route must own at least one replayable handed-back shift (a target with at
    least one eligible neighbor), otherwise the trial is held as 暂缓.
    """
    routes = scan(conn, trail_routes)
    active_routes = sorted(row['code'] for row in routes if row['active'])
    windows, handed = _world(conn)

    samples = []
    covered = set()
    for shift in handed:
        target_window = windows.get(shift['window'])
        if target_window is None:
            continue
        candidates = eligible_neighbors(target_window, handed, windows,
                                       exclude_shift=shift['code'])
        if not candidates:
            continue
        actual_offset = learning.arrival_offset(target_window['opens'], shift['on_site'])
        frozen_neighbors = [{
            'shift': neighbor['code'],
            'offset': learning.arrival_offset(neighbor_window['opens'], neighbor['on_site']),
            'window': dict(neighbor_window),
        } for neighbor, neighbor_window in candidates]
        samples.append({
            'shift': shift['code'],
            'route': target_window['route'],
            'phase': target_window['phase'],
            'actual_offset': actual_offset,
            'target_window': dict(target_window),
            'neighbors': frozen_neighbors,
        })
        covered.add(target_window['route'])

    missing_routes = [code for code in active_routes if code not in covered]
    return active_routes, samples, missing_routes


# ---------------------------------------------------------------------------
# Live estimate — always uses the enabled weights
# ---------------------------------------------------------------------------

def _resolve_target_window(conn, data):
    value = (data.get('shift') or data.get('window')
             or data.get('code') or data.get('target'))
    if not value:
        raise HTTPException(422, detail='请提供要估算的领班号或潮窗编号')
    shift = conn.execute(select(lead_shifts).where(lead_shifts.c.code == value)).mappings().first()
    if shift is not None:
        return get(conn, patrol_windows, shift['window']), value
    window = conn.execute(select(patrol_windows).where(patrol_windows.c.code == value)).mappings().first()
    if window is not None:
        return dict(window), None
    raise HTTPException(404, detail=f'找不到领班或潮窗 {value}')


def estimate_arrival(conn, user, payload):
    data = payload.model_dump() if hasattr(payload, 'model_dump') else dict(payload or {})
    target_window, shift_code = _resolve_target_window(conn, data)
    windows, handed = _world(conn)
    candidates = eligible_neighbors(target_window, handed, windows, exclude_shift=shift_code)
    need(bool(candidates), '同路同潮相且开窗前已结束的近邻班次不足，无法估算到场时刻')

    enabled = current_weights(conn)
    k = data.get('k') or data.get('neighbors') or learning.NEIGHBOR_LIMIT
    result = learning.estimate_for_target(target_window, candidates, enabled, k=k)
    result['code'] = shift_code or target_window['code']
    result['using_enabled_weights'] = True
    result['enabled_weights'] = dict(enabled)
    result['shift'] = shift_code

    requested = data.get('weights') or data.get('distance_weights')
    if requested is not None:
        try:
            draft_weights = learning.extract_weights(requested)
            preview = learning.estimate_for_target(target_window, candidates, draft_weights, k=k)
            result['requested_preview'] = {
                'weights': draft_weights,
                'predicted_on_site': preview['predicted_on_site'],
                'predicted_offset_minutes': preview['predicted_offset_minutes'],
            }
        except ValueError:
            pass
    return result


# ---------------------------------------------------------------------------
# Weight trials
# ---------------------------------------------------------------------------

def _trial_code():
    return 'TRIAL-' + uuid4().hex[:12]


def submit_trial(conn, user, payload, enqueue=True):
    data = payload.model_dump() if hasattr(payload, 'model_dump') else dict(payload or {})
    try:
        proposed = learning.extract_weights(data)
    except ValueError as exc:
        raise HTTPException(422, detail=str(exc))
    k = data.get('k') or data.get('neighbors') or learning.NEIGHBOR_LIMIT
    if not isinstance(k, int) or not 1 <= k <= 50:
        k = learning.NEIGHBOR_LIMIT

    active_routes, samples, missing_routes = build_replay_batch(conn)
    baseline = current_weights(conn)
    code = _trial_code()

    if not samples or missing_routes:
        reason = ('缺少可回放班次，试评暂缓；以下开放路线没有足够的已交回近邻样本：'
                  + '、'.join(missing_routes)) if missing_routes else '缺少可回放的已交回班次，试评暂缓'
        reason = reason[:480]
        insert(conn, weight_trials, code=code, token=None, state='暂缓',
               proposed=proposed, baseline=baseline, routes=active_routes,
               sample_codes=[s['shift'] for s in samples], samples=samples,
               neighbor_k=k, missing_routes=missing_routes, report=None, detail=reason,
               requested_by=user['sub'], created_at=_now(), finished_at=_now())
        return serialize_trial(get(conn, weight_trials, code)) | {
            'deferred': True, 'status': 'deferred', 'k': k}

    token = None
    fallback = False
    if enqueue:
        try:
            queued = submit(user, {'kind': 'weight_trial', 'trial_code': code, 'k': k})
            token = queued['token']
        except Exception:
            # No broker available (e.g. an in-process test harness): persist the
            # trial and let the API finalize it synchronously.
            fallback = True
    insert(conn, weight_trials, code=code, token=token, state='排队中',
           proposed=proposed, baseline=baseline, routes=active_routes,
           sample_codes=[sample['shift'] for sample in samples], samples=samples,
           neighbor_k=k, missing_routes=[], report=None, detail=None,
           requested_by=user['sub'], created_at=_now(), finished_at=None)
    return {'token': token, 'status': 'queued' if token else 'ready',
            'fallback': fallback, 'trial': code, 'code': code,
            'state': '排队中', 'sample_count': len(samples),
            'sample_codes': [sample['shift'] for sample in samples],
            'routes': active_routes, 'proposed_weights': proposed,
            'baseline_weights': baseline, 'k': k}


def serialize_trial(row):
    if row is None:
        return None
    row = dict(row)
    state = row['state']
    status = {'排队中': 'queued', '试评中': 'running', '暂缓': 'deferred',
              '已启用': 'adopted', '未启用': 'rejected'}.get(state, state)
    report = row.get('report')
    out = dict(row)
    out.update({
        'status': status,
        'status_label': state,
        'state': state,
        'deferred': state == '暂缓',
        'adopted': state == '已启用',
        'enabled': state == '已启用',
        'kept': state == '未启用',
        'trial': row['code'],
        'sample_count': len(row.get('sample_codes') or []),
        'mae': (report or {}).get('mae_after') if report else None,
        'result': report,
    })
    if report:
        for key in ('mae_before', 'mae_after', 'mae_current', 'mae_proposed',
                    'route_reports', 'proposed_weights', 'current_weights', 'verdict'):
            out.setdefault(key, report.get(key))
    return out


def list_trials(conn):
    rows = scan(conn, weight_trials)
    rows.sort(key=lambda row: (row.get('created_at') or '', row['code']), reverse=True)
    return [serialize_trial(row) for row in rows]


def get_trial(conn, code=None, token=None):
    if code:
        row = conn.execute(select(weight_trials).where(weight_trials.c.code == code)).mappings().first()
    elif token:
        row = conn.execute(select(weight_trials).where(weight_trials.c.token == token)).mappings().first()
    else:
        raise HTTPException(422, detail='请提供试评单编号')
    if row is None:
        raise HTTPException(404, detail='找不到试评单')
    return serialize_trial(row)


def complete_trial(job):
    """Worker / inline finalization. Idempotent; always re-compares against the
    currently enabled weights using the frozen original sample batch."""
    code = job['trial_code'] if isinstance(job, dict) else job
    with transaction() as conn:
        trial = get(conn, weight_trials, code, lock=True)
        if trial['state'] in TERMINAL_STATES:
            return serialize_trial(trial)

        weights_row = ensure_weights(conn, lock=True)
        current = {'phase': weights_row['phase_weight'],
                   'duration': weights_row['duration_weight']}
        job_k = job.get('k') if isinstance(job, dict) else None
        k = job_k or trial.get('neighbor_k') or learning.NEIGHBOR_LIMIT
        report = learning.compare_weights(
            trial['samples'] or [], trial['routes'] or [],
            trial['proposed'], current, trial['baseline'],
            k=k or learning.NEIGHBOR_LIMIT)
        report['trial'] = code
        report['sample_codes'] = trial['sample_codes']

        if report['adopt']:
            conn.execute(distance_weights.update().where(distance_weights.c.code == ENABLED_CODE).values(
                phase_weight=trial['proposed']['phase'],
                duration_weight=trial['proposed']['duration'],
                updated_by=trial['requested_by'], updated_at=_now(), trial_code=code))
            state = '已启用'
        else:
            state = '未启用'
        finished = _now()
        conn.execute(weight_trials.update().where(weight_trials.c.code == code).values(
            state=state, report=report, finished_at=finished))
        fresh = get(conn, weight_trials, code)
        return serialize_trial(fresh)


def resolve_trial_code(payload):
    data = payload if isinstance(payload, dict) else (payload.model_dump() if hasattr(payload, 'model_dump') else {})
    return data.get('code') or data.get('trial'), data.get('token')


def resume_trial(conn, payload):
    """Resolve the trial a resume request points at."""
    code, token = resolve_trial_code(payload)
    return get_trial(conn, code=code, token=token)


def resume_trial_now(trial):
    """Finalize a non-terminal trial outside any caller transaction."""
    if trial['state'] in RUNNING_STATES:
        completed = complete_trial({'trial_code': trial['code'],
                                    'k': trial.get('neighbor_k') or learning.NEIGHBOR_LIMIT})
        if trial.get('token'):
            _publish_ready(trial['token'], completed, trial.get('requested_by'))
        with transaction() as fresh_conn:
            return get_trial(fresh_conn, code=trial['code'])
    return trial


def _publish_ready(token, result, owner=None):
    import json
    from core.queueing import broker
    broker.set(f'compute:{token}', json.dumps(
        {'owner': owner, 'status': 'ready', 'result': result}, allow_nan=False), ex=86400)
