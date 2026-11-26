from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import scan
from domain import lead_shifts_service as service
from domain.lead_shifts_model import lead_shifts
from domain.lead_shifts_schemas import AssignLead, CheckIn, HandBack

router = APIRouter()

@router.get('/lead_shifts')
def list_lead_shifts(user=Depends(actor)):
    with transaction() as conn:
        return scan(conn, lead_shifts)


@router.post('/lead_shifts/assign-lead')
def assign_lead(data: AssignLead, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.assign_lead(conn, user, data)
        record(conn, user, 'lead_shifts.assign_lead')
        return output


@router.post('/lead_shifts/check-in')
def check_in(data: CheckIn, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.check_in(conn, user, data)
        record(conn, user, 'lead_shifts.check_in')
        return output


@router.post('/lead_shifts/hand-back')
def hand_back(data: HandBack, user=Depends(actor)):
    allow(user, ('reviewer',))
    with transaction() as conn:
        output = service.hand_back(conn, user, data)
        record(conn, user, 'lead_shifts.hand_back')
        return output
