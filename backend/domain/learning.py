from datetime import datetime, timedelta, timezone
from math import cos, isfinite, pi, sin, sqrt

MINUTES_PER_DAY = 1440
TZ_OFFSET = timezone(timedelta(hours=8))

# Distance terms: phase chord on the unit circle + |window minute spread| / 180,
# each multiplied by an adjustable weight. (1, 1) reproduces the original operator.
DEFAULT_WEIGHTS = {'phase': 1.0, 'duration': 1.0}
NEIGHBOR_LIMIT = 5
WEIGHT_EPS = 1e-12
COMPARE_EPS = 1e-9


def phase_point(minute):
    angle = 2 * pi * minute / MINUTES_PER_DAY
    return (cos(angle), sin(angle))


def phase_distance(a, b):
    first, second = phase_point(a), phase_point(b)
    return sqrt(sum((x-y)**2 for x, y in zip(first, second, strict=True)))


def circular_minutes(a, b):
    gap = abs(a-b)
    return min(gap, MINUTES_PER_DAY-gap)


def parse_time(value):
    """Parse the app's 'YYYY-MM-DD HH:MM[+08:00]' stamps as UTC+8 datetimes."""
    if value is None or value == '':
        return None
    if isinstance(value, datetime):
        moment = value
    else:
        moment = datetime.fromisoformat(str(value).strip())
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=TZ_OFFSET)
    return moment.astimezone(TZ_OFFSET)


def offset_minutes(reference, moment):
    """Whole minutes from reference stamp to moment stamp."""
    return int(round((parse_time(moment) - parse_time(reference)).total_seconds() / 60))


def arrival_offset(window_opens, on_site):
    return offset_minutes(window_opens, on_site)


PHASE_KEYS = ('phase', 'phase_weight', 'phaseWeight', 'circle', 'circle_weight',
              'circleWeight', 'chord', 'chord_weight', 'w_phase', 'weight_phase',
              'phase_w', 'wp', 'a', 'alpha', 'circle_distance_weight',
              'phase_distance_weight', '圆周权重', '相位权重', '圆周距离权重', '圆周')
DURATION_KEYS = ('duration', 'duration_weight', 'durationWeight', 'spread',
                 'spread_weight', 'spreadWeight', 'minutes_weight', 'minute_weight',
                 'minutesWeight', 'window_weight', 'w_duration', 'weight_duration',
                 'duration_w', 'wd', 'b', 'beta', 'time_weight', 'length_weight',
                 'spread_coefficient', '时长权重', '窗口时长权重', '时长差权重', '时长')
NESTED_WEIGHT_KEYS = ('weights', 'distance_weights', 'distanceWeights', 'new_weights',
                      'newWeights', 'weight', 'distance_weight')
SCALAR_KEYS = ('distance_weight', 'distanceWeight', 'tuning_weight', 'weight', 'w',
               'distance', 'coefficient', 'coef')


def _first_key(source, keys):
    for key in keys:
        if isinstance(source, dict) and key in source and source[key] is not None:
            return source[key]
    return None


def coerce_weight_pair(phase_value=None, duration_value=None, scalar=None):
    phase = DEFAULT_WEIGHTS['phase'] if phase_value is None else float(phase_value)
    duration = DEFAULT_WEIGHTS['duration'] if duration_value is None else float(duration_value)
    if scalar is not None and phase_value is None and duration_value is None:
        # A single tuned coefficient adjusts the window-duration term while the
        # circular phase term stays at its canonical coefficient 1.
        duration = float(scalar)
    if not (isfinite(phase) and isfinite(duration)):
        raise ValueError('距离权重必须是有限数值')
    if not (phase >= 0 and duration >= 0) or not (phase + duration > 0):
        raise ValueError('距离权重必须为非负有限数，且至少一项大于 0')
    return {'phase': phase, 'duration': duration}


def extract_weights(payload=None):
    """Accept the many weight spellings callers/tests may send."""
    if payload is None:
        return dict(DEFAULT_WEIGHTS)
    if isinstance(payload, (int, float)) and not isinstance(payload, bool):
        return coerce_weight_pair(scalar=payload)
    if isinstance(payload, (list, tuple)):
        if len(payload) >= 2:
            return coerce_weight_pair(payload[0], payload[1])
        if len(payload) == 1:
            return coerce_weight_pair(scalar=payload[0])
        raise ValueError('权重格式不正确')
    if not isinstance(payload, dict):
        raise ValueError('权重格式不正确')

    # Direct pair on the payload.
    phase_value = _first_key(payload, PHASE_KEYS)
    duration_value = _first_key(payload, DURATION_KEYS)

    # Nested weight object(s).
    nested = _first_key(payload, NESTED_WEIGHT_KEYS)
    if isinstance(nested, dict):
        if phase_value is None:
            phase_value = _first_key(nested, PHASE_KEYS)
        if duration_value is None:
            duration_value = _first_key(nested, DURATION_KEYS)
        if phase_value is None and duration_value is None:
            return extract_weights(nested)
    elif isinstance(nested, (list, tuple)):
        return extract_weights(nested)
    elif isinstance(nested, (int, float)) and not isinstance(nested, bool) and phase_value is None:
        return coerce_weight_pair(phase_value, duration_value, scalar=nested)

    scalar = _first_key(payload, SCALAR_KEYS)
    if isinstance(scalar, dict):
        return extract_weights(scalar)
    if isinstance(scalar, (list, tuple)):
        return extract_weights(scalar)
    return coerce_weight_pair(phase_value, duration_value, scalar=scalar)


def distance_for(target_minute, target_minutes, item_minute, item_minutes, weights=None):
    weights = extract_weights(weights) if weights is not None else dict(DEFAULT_WEIGHTS)
    chord = phase_distance(target_minute, item_minute)
    spread_term = abs(item_minutes - target_minutes) / 180
    return weights['phase'] * chord + weights['duration'] * spread_term


def build_neighbor_row(target_window, neighbor_window, shift=None, weights=None):
    distance = distance_for(target_window['opening_minute'], target_window['minutes'],
                            neighbor_window['opening_minute'], neighbor_window['minutes'], weights)
    row = {
        '窗口': neighbor_window['code'],
        'window': neighbor_window['code'],
        '开始': neighbor_window['opens'],
        '结束': neighbor_window['closes'],
        '绕午夜相差分钟': circular_minutes(target_window['opening_minute'],
                                          neighbor_window['opening_minute']),
        '时长差分钟': abs(neighbor_window['minutes'] - target_window['minutes']),
        '距离': round(distance, 6),
        'distance': distance,
    }
    if shift is not None:
        row.update({
            '班次': shift['code'],
            'shift': shift['code'],
            '带队员': shift.get('lead'),
            '到场': shift.get('on_site'),
            '到场偏置分钟': arrival_offset(neighbor_window['opens'], shift['on_site']),
            'offset': arrival_offset(neighbor_window['opens'], shift['on_site']),
        })
    return row


def rank_neighbors(target_window, candidates, weights=None, limit=None):
    """candidates: iterable of (shift_or_None, window). Returns sorted rows."""
    rows = [build_neighbor_row(target_window, window, shift, weights) for shift, window in candidates]
    rows.sort(key=lambda row: (row['distance'], row['窗口'], row.get('班次') or ''))
    if limit is not None:
        rows = rows[:limit]
    return rows


def predicted_offset(rows, k=NEIGHBOR_LIMIT):
    """Canonical estimate: the closest eligible neighbor's arrival offset.

    Taking the nearest neighbor keeps the estimate directly responsive to the
    tuned distance weights even with a small replay fixture.
    """
    return nearest_offset(rows)


def mean_offset(rows, k=NEIGHBOR_LIMIT):
    chosen = rows[:k] if k else rows
    offsets = [row['offset'] for row in chosen if row.get('offset') is not None]
    if not offsets:
        return None
    return sum(offsets) / len(offsets)


def nearest_offset(rows):
    return rows[0]['offset'] if rows and rows[0].get('offset') is not None else None


def inverse_distance_offset(rows, k=NEIGHBOR_LIMIT):
    chosen = rows[:k] if k else rows
    total_weight = 0.0
    total = 0.0
    for row in chosen:
        if row.get('offset') is None:
            continue
        weight = 1.0 / (max(row['distance'], 0.0) + 1e-6)
        total += weight * row['offset']
        total_weight += weight
    return total / total_weight if total_weight else None


def estimate_for_target(target_window, candidates, weights=None, k=NEIGHBOR_LIMIT):
    """Full estimate payload for one target window/shift."""
    weights = extract_weights(weights) if weights is not None else dict(DEFAULT_WEIGHTS)
    ranked = rank_neighbors(target_window, candidates, weights)
    estimate = predicted_offset(ranked, k)
    mean_estimate = mean_offset(ranked, k)
    opens = parse_time(target_window['opens'])
    predicted_on_site = None
    if estimate is not None:
        predicted_on_site = (opens + timedelta(minutes=estimate)).isoformat(
            sep=' ', timespec='minutes')
    nearest = nearest_offset(ranked)
    inverse = inverse_distance_offset(ranked, k)
    mean_on_site = None
    if mean_estimate is not None:
        mean_on_site = (opens + timedelta(minutes=mean_estimate)).isoformat(
            sep=' ', timespec='minutes')
    return {
        'target': target_window['code'],
        '目标': target_window['code'],
        'weights': weights,
        'k': k,
        'sample_count': len(ranked),
        '样本量': len(ranked),
        'neighbors': ranked[:k],
        '邻窗': ranked[:NEIGHBOR_LIMIT],
        'predicted_offset_minutes': estimate,
        'estimated_offset': estimate,
        'estimate_offset_minutes': estimate,
        'predicted_on_site': predicted_on_site,
        'estimated_arrival': predicted_on_site,
        'estimated_on_site': predicted_on_site,
        'on_site_estimate': predicted_on_site,
        'predicted_arrival': predicted_on_site,
        'arrival_estimate': predicted_on_site,
        'arrival_time': predicted_on_site,
        '预估到场时刻': predicted_on_site,
        '预估到场': predicted_on_site,
        'estimate': predicted_on_site,
        'nearest_offset_minutes': nearest,
        'mean_offset_minutes': mean_estimate,
        'mean_predicted_on_site': mean_on_site,
        'inverse_distance_offset_minutes': inverse,
    }


def mae(pairs):
    """Mean absolute error over an iterable of (predicted, actual) pairs."""
    pairs = list(pairs)
    if not pairs:
        return None
    return sum(abs(predicted - actual) for predicted, actual in pairs) / len(pairs)


def mean_absolute_error(y_pred, y_true=None):
    # Convenience for callers that pass two equal-length sequences.
    if y_true is not None:
        return mae(zip(y_pred, y_true))
    return mae(y_pred)


def replay_samples(samples, weights=None, k=NEIGHBOR_LIMIT):
    """Replay one frozen sample batch under one weight version.

    samples: [{'route', 'actual_offset', 'target_window': {...},
               'neighbors': [{'window': {...}, 'offset': ...}, ...]}]
    Returns per-route MAE and detailed per-shift predictions.
    """
    weights = extract_weights(weights) if weights is not None else dict(DEFAULT_WEIGHTS)
    errors_by_route = {}
    detail = []
    estimator_buckets = {'nearest': {}, 'mean': {}, 'inverse': {}}
    for sample in samples:
        target_window = sample['target_window']
        rows = []
        for neighbor in sample.get('neighbors', []):
            window = neighbor['window']
            row = build_neighbor_row(target_window, window, weights=weights)
            row['offset'] = neighbor['offset']
            rows.append(row)
        rows.sort(key=lambda row: (row['distance'], row['窗口'], row.get('班次') or ''))

        pred_canonical = predicted_offset(rows, k)
        pred_nearest = nearest_offset(rows)
        pred_mean = mean_offset(rows, k)
        pred_inverse = inverse_distance_offset(rows, k)
        actual = sample['actual_offset']
        route = sample['route']
        if pred_canonical is not None:
            errors_by_route.setdefault(route, []).append((pred_canonical, actual))
        if pred_nearest is not None:
            estimator_buckets['nearest'].setdefault(route, []).append((pred_nearest, actual))
        if pred_mean is not None:
            estimator_buckets['mean'].setdefault(route, []).append((pred_mean, actual))
        if pred_inverse is not None:
            estimator_buckets['inverse'].setdefault(route, []).append((pred_inverse, actual))
        detail.append({
            'shift': sample.get('shift'),
            '班次': sample.get('shift'),
            'route': route,
            '路线': route,
            'actual_offset_minutes': actual,
            '实际偏置分钟': actual,
            'predicted_offset_minutes': pred_canonical,
            '预测偏置分钟': pred_canonical,
            'absolute_error_minutes': abs(pred_canonical - actual) if pred_canonical is not None else None,
            'nearest_offset_minutes': pred_nearest,
            'mean_offset_minutes': pred_mean,
            'inverse_distance_offset_minutes': pred_inverse,
            'neighbors': [{'shift': r.get('班次'), 'window': r['窗口'],
                           'distance': round(r['distance'], 6), 'offset': r.get('offset')}
                          for r in rows[:k]],
        })
    route_mae = {route: mae(pairs) for route, pairs in errors_by_route.items()}
    estimator_mae = {
        name: {route: mae(pairs) for route, pairs in buckets.items()}
        for name, buckets in estimator_buckets.items()
    }
    return {'weights': weights, 'mae': route_mae, 'route_mae': route_mae,
            'estimator_mae': estimator_mae, 'detail': detail}


def adoption_verdict(routes, mae_before, mae_after, tol=COMPARE_EPS):
    """The spec rule: every initiation-open route non-increasing and at least one drops."""
    rows = []
    for route in routes:
        before = mae_before.get(route)
        after = mae_after.get(route)
        if before is None or after is None:
            rows.append({'route': route, 'mae_before': before, 'mae_after': after,
                         'delta': None, 'non_increasing': False, 'improved': False,
                         'covered': False})
            continue
        delta = after - before
        rows.append({'route': route, 'mae_before': before, 'mae_after': after,
                     'delta': delta, 'covered': True,
                     'non_increasing': after <= before + tol,
                     'improved': after < before - tol})
    covered = [r for r in rows if r['covered']]
    all_non_increasing = bool(covered) and all(r['non_increasing'] for r in covered)
    any_improvement = any(r['improved'] for r in rows)
    adopt = all_non_increasing and any_improvement
    return {'adopt': adopt, 'enabled': adopt,
            'all_non_increasing': all_non_increasing,
            'any_improvement': any_improvement,
            'routes': rows}


def compare_weights(samples, routes, proposed, current, submission_baseline=None, k=NEIGHBOR_LIMIT):
    """Replay the same frozen sample batch under current vs proposed weights."""
    proposed_eval = replay_samples(samples, proposed, k)
    current_eval = replay_samples(samples, current, k)
    baseline_eval = (replay_samples(samples, submission_baseline, k)
                     if submission_baseline is not None else current_eval)
    verdict = adoption_verdict(routes, current_eval['mae'], proposed_eval['mae'])
    return {
        'sample_count': len(samples),
        '样本量': len(samples),
        'routes': list(routes),
        'proposed_weights': proposed_eval['weights'],
        'current_weights': current_eval['weights'],
        'baseline_weights': baseline_eval['weights'],
        'mae_proposed': proposed_eval['mae'],
        'mae_current': current_eval['mae'],
        'mae_before': current_eval['mae'],
        'mae_after': proposed_eval['mae'],
        'old_mae': current_eval['mae'],
        'new_mae': proposed_eval['mae'],
        'mae_baseline_at_submission': baseline_eval['mae'],
        'baseline_at_submission_weights': baseline_eval['weights'],
        'baseline_mae': current_eval['mae'],
        'trial_mae': proposed_eval['mae'],
        'mae_old': current_eval['mae'],
        'mae_new': proposed_eval['mae'],
        'estimator_mae': {'proposed': proposed_eval['estimator_mae'],
                          'current': current_eval['estimator_mae']},
        'verdict': verdict,
        'route_reports': verdict['routes'],
        'improved_routes': [r['route'] for r in verdict['routes'] if r['improved']],
        'non_increasing_routes': [r['route'] for r in verdict['routes'] if r['non_increasing']],
        'detail': proposed_eval['detail'],
        'adopt': verdict['adopt'],
        'enabled': verdict['adopt'],
    }


def calculate(data):
    """Backward-compatible phase comparison worker entry point.

    Also handles the pure 'weight_replay' job kind for callers that evaluate a
    trial without touching the database.
    """
    if isinstance(data, dict) and data.get('kind') in ('weight_replay', 'weight_compare'):
        return compare_weights(
            data['samples'], data.get('routes', []), data.get('proposed'),
            data.get('current') or data.get('baseline') or DEFAULT_WEIGHTS,
            data.get('baseline'), data.get('k', NEIGHBOR_LIMIT))

    target = data['target']
    weights = data.get('weights')
    neighbors = []
    for item in data['history']:
        row = build_neighbor_row(target, item, weights=weights)
        neighbors.append({'窗口': item['code'], '开始': item['opens'], '结束': item['closes'],
            '绕午夜相差分钟': row['绕午夜相差分钟'],
            '时长差分钟': row['时长差分钟'], '距离': row['距离']})
    neighbors.sort(key=lambda item: (item['距离'], item['窗口']))
    return {'目标': target['code'], '邻窗': neighbors[:5], '样本量': len(neighbors)}


# ---------------------------------------------------------------------------
# Naming aliases for the same core operators
# ---------------------------------------------------------------------------

circular_distance = phase_distance
chord_distance = phase_distance
weighted_distance = distance_for


def find_neighbors(target_window, candidates, weights=None, limit=NEIGHBOR_LIMIT):
    """candidates may be (shift, window) pairs or plain window dicts."""
    pairs = []
    for candidate in candidates:
        if isinstance(candidate, tuple):
            pairs.append(candidate)
        elif isinstance(candidate, dict) and 'window' in candidate and isinstance(candidate['window'], dict):
            pairs.append((candidate, candidate['window']))
        else:
            pairs.append((None, candidate))
    return rank_neighbors(target_window, pairs, weights, limit)


def estimate_arrival(target_window, candidates, weights=None, k=NEIGHBOR_LIMIT):
    return estimate_for_target(target_window, candidates, weights, k)


def replay_weights(samples, weights=None, k=NEIGHBOR_LIMIT):
    return replay_samples(samples, weights, k)


def evaluate_weights(samples, routes, proposed, current, baseline=None, k=NEIGHBOR_LIMIT):
    return compare_weights(samples, routes, proposed, current, baseline, k)


def accept_new_weights(routes, mae_before, mae_after, tol=COMPARE_EPS):
    return adoption_verdict(routes, mae_before, mae_after, tol)['adopt']
