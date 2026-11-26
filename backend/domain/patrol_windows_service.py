from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.trail_routes_model import trail_routes
from domain.patrol_windows_model import patrol_windows
from domain.trail_notices_model import trail_notices
from domain.lead_shifts_model import lead_shifts


def register_window(conn, user, data):
    from domain.calendar_clock import local_time, minutes_between
    route = get(conn, trail_routes, data.route, lock=True)
    need(route['active'], '路线已停止，不能登记潮窗')
    starts_at, ends_at = local_time(data.starts_at), local_time(data.ends_at)
    duration = minutes_between(starts_at, ends_at)
    need(10 <= duration <= 180, '结束时间必须给出正确的日期且窗口为 10–180 分钟')
    need(data.phase in {'涨潮','落潮','平潮'}, '日历相位只接受涨潮、落潮和平潮')
    start, end = starts_at.isoformat(sep=' ',timespec='minutes'), ends_at.isoformat(sep=' ',timespec='minutes')
    existing = conn.execute(select(patrol_windows.c.code).where(
        patrol_windows.c.route == data.route, patrol_windows.c.opens < end,
        patrol_windows.c.closes > start)).first()
    need(existing is None, '同一堤线的两个潮窗不能重叠')
    return insert(conn, patrol_windows, code=data.code, route=data.route, opens=start, closes=end,
        opening_minute=starts_at.hour*60+starts_at.minute, minutes=duration, phase=data.phase, tag=data.tag)


def compare_phase(conn, user, data):
    window = get(conn, patrol_windows, data.window)
    history = [item for item in scan(conn, patrol_windows)
               if item['code'] != window['code'] and item['route'] == window['route']
               and item['phase'] == window['phase'] and item['opens'] < window['opens']]
    need(bool(history), '这条路线的同相位历史不足')
    return submit(user, {'target': window, 'history': history})
