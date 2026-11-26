from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import patrol_windows_service as service
from domain.patrol_windows_model import patrol_windows
from domain.patrol_windows_schemas import RegisterWindow, ComparePhase

router = APIRouter()

@router.get('/patrol_windows')
def list_patrol_windows(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, patrol_windows)


@router.post('/patrol_windows/register-window')
def register_window(data: RegisterWindow, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.register_window(conn, user, data)
        record(conn, user, 'patrol_windows.register_window')
        return output


@router.post('/patrol_windows/compare-phase')
def compare_phase(data: ComparePhase, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.compare_phase(conn, user, data)
        record(conn, user, 'patrol_windows.compare_phase')
        return output
