from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import trail_notices_service as service
from domain.trail_notices_model import trail_notices
from domain.trail_notices_schemas import PostClosure, LiftClosure

router = APIRouter()

@router.get('/trail_notices')
def list_trail_notices(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, trail_notices)


@router.post('/trail_notices/post-closure')
def post_closure(data: PostClosure, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.post_closure(conn, user, data)
        record(conn, user, 'trail_notices.post_closure')
        return output


@router.post('/trail_notices/lift-closure')
def lift_closure(data: LiftClosure, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.lift_closure(conn, user, data)
        record(conn, user, 'trail_notices.lift_closure')
        return output
