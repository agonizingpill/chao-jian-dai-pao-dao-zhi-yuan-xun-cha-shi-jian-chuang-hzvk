from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import trail_routes_service as service
from domain.trail_routes_model import trail_routes
from domain.trail_routes_schemas import RegisterRoute, PauseRoute

router = APIRouter()

@router.get('/trail_routes')
def list_trail_routes(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, trail_routes)


@router.post('/trail_routes/register-route')
def register_route(data: RegisterRoute, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.register_route(conn, user, data)
        record(conn, user, 'trail_routes.register_route')
        return output


@router.post('/trail_routes/pause-route')
def pause_route(data: PauseRoute, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.pause_route(conn, user, data)
        record(conn, user, 'trail_routes.pause_route')
        return output
