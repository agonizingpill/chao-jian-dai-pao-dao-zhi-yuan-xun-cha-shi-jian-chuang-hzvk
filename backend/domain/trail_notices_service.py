from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.trail_routes_model import trail_routes
from domain.patrol_windows_model import patrol_windows
from domain.trail_notices_model import trail_notices
from domain.lead_shifts_model import lead_shifts


def post_closure(conn, user, data):
    from domain.calendar_clock import local_time, minutes_between
    get(conn, trail_routes, data.route, lock=True)
    begins, until = local_time(data.begins), local_time(data.until)
    need(5 <= minutes_between(begins, until) <= 17280, '限制时段必须至少 5 分钟且不超过 12 天')
    return insert(conn, trail_notices, code=data.code, route=data.route,
        begins=begins.isoformat(sep=' ', timespec='minutes'), until=until.isoformat(sep=' ', timespec='minutes'),
        reason=data.reason, status='封闭')


def lift_closure(conn, user, data):
    notice = get(conn, trail_notices, data.notice)
    get(conn, trail_routes, notice['route'], lock=True)
    notice = get(conn, trail_notices, data.notice, lock=True)
    need(notice['status'] == '封闭', '此限制已经解除')
    need(len(data.witness) >= 4, '请填写解封见证')
    return update(conn, trail_notices, data.notice, status='已解除', reason=notice['reason'][:90]+' / '+data.witness[:60])
