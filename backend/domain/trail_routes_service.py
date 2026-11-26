from sqlalchemy import select

from core.queueing import submit, result
from core.records import get, insert, need, scan, update
from domain.trail_routes_model import trail_routes
from domain.patrol_windows_model import patrol_windows
from domain.trail_notices_model import trail_notices
from domain.lead_shifts_model import lead_shifts


def register_route(conn, user, data):
    need(data.code.startswith('TR-') and data.checkpoint.startswith('GATE-'), '路线和检查点需使用对应编号前缀')
    need(1 <= data.max_leads <= 8, '单潮窗带队名额应为 1–8')
    return insert(conn, trail_routes, **data.model_dump(), active=True)


def pause_route(conn, user, data):
    route = get(conn, trail_routes, data.route, lock=True)
    need(route['active'], '此路线已停止排班')
    return update(conn, trail_routes, data.route, active=False)
