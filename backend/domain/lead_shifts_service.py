from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.trail_routes_model import trail_routes
from domain.patrol_windows_model import patrol_windows
from domain.trail_notices_model import trail_notices
from domain.lead_shifts_model import lead_shifts


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
    return insert(conn, lead_shifts, **data.model_dump(), state='已领班', checkpoint=None, on_site=None)


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


def hand_back(conn, user, data):
    shift = get(conn, lead_shifts, data.shift, lock=True)
    need(shift['state'] == '已签到', '领班签到后才可签回')
    return update(conn, lead_shifts, data.shift, state='已交回')
