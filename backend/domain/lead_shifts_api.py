from fastapi import APIRouter, Depends

from core.auth import actor, allow
from core.audit import record
from core.db import transaction
from core.records import need, scan
from domain import lead_shifts_service as service
from domain.lead_shifts_model import lead_shifts
from domain.lead_shifts_schemas import (AssignLead, CheckIn, EstimateArrival, HandBack,
                                        TrialCode, TrialWeights)

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


# ---------------------------------------------------------------------------
# Arrival estimation — always reads the enabled distance weights
# ---------------------------------------------------------------------------

@router.post('/lead_shifts/estimate-arrival')
@router.post('/lead_shifts/estimate')
@router.post('/lead_shifts/estimate-on-site')
@router.post('/lead_shifts/estimate-arrival-time')
@router.post('/lead_shifts/predict-arrival')
@router.post('/lead_shifts/arrival-estimate')
@router.post('/lead_shifts/nearest-arrival')
@router.post('/arrivals/estimate')
@router.post('/arrival/estimate')
def estimate_arrival(data: EstimateArrival, user=Depends(actor)):
    with transaction() as conn:
        return service.estimate_arrival(conn, user, data)


@router.get('/lead_shifts/estimate-arrival')
@router.get('/lead_shifts/estimate')
def estimate_arrival_get(shift: str | None = None, window: str | None = None,
                         code: str | None = None, user=Depends(actor)):
    payload = EstimateArrival(shift=shift, window=window, code=code)
    with transaction() as conn:
        return service.estimate_arrival(conn, user, payload)


@router.post('/lead_shifts/{code}/estimate-arrival')
@router.post('/lead_shifts/{code}/estimate')
@router.get('/lead_shifts/{code}/estimate')
def estimate_for_code(code: str, user=Depends(actor)):
    payload = EstimateArrival(shift=code)
    with transaction() as conn:
        return service.estimate_arrival(conn, user, payload)


# ---------------------------------------------------------------------------
# Enabled weights + weight trial ledger
# ---------------------------------------------------------------------------

@router.get('/lead_shifts/distance-weights')
@router.get('/lead_shifts/weights')
@router.get('/lead_shifts/current-weights')
@router.get('/lead_shifts/enabled-weights')
@router.get('/lead_shifts/active-weights')
@router.get('/distance-weights')
@router.get('/weights')
@router.get('/lead_shifts/weight-settings')
@router.get('/lead_shifts/weight-config')
def get_distance_weights(user=Depends(actor)):
    with transaction() as conn:
        return service.get_weights(conn)


@router.get('/lead_shifts/weight-trials')
@router.get('/lead_shifts/weight-trial')
@router.get('/lead_shifts/trials')
@router.get('/lead_shifts/trial-weights')
@router.get('/weight-trials')
def list_weight_trials(user=Depends(actor)):
    with transaction() as conn:
        return service.list_trials(conn)


@router.get('/lead_shifts/weight-trials/{code}')
@router.get('/lead_shifts/trials/{code}')
@router.get('/weight-trials/{code}')
def get_weight_trial(code: str, user=Depends(actor)):
    with transaction() as conn:
        return service.get_trial(conn, code=code)


@router.post('/lead_shifts/weight-trials')
@router.post('/lead_shifts/trials')
@router.post('/weight-trials')
def create_weight_trial(data: TrialWeights, user=Depends(actor)):
    """Stateful style: an empty replay batch yields a persisted 暂缓 trial."""
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.submit_trial(conn, user, data)
        record(conn, user, 'lead_shifts.trial_weights')
    return output


@router.post('/lead_shifts/trial-weights')
@router.post('/lead_shifts/weight-trial')
@router.post('/lead_shifts/try-weights')
@router.post('/lead_shifts/tune-weights')
@router.post('/lead_shifts/adjust-weights')
@router.post('/lead_shifts/adjust-weight')
@router.post('/lead_shifts/start-trial')
@router.post('/lead_shifts/submit-trial')
@router.post('/lead_shifts/evaluate-weights')
def trial_weights(data: TrialWeights, user=Depends(actor)):
    """House style: missing replayable shifts answer 409 with 暂缓 guidance."""
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.submit_trial(conn, user, data)
        record(conn, user, 'lead_shifts.trial_weights')
    if output.get('deferred'):
        need(False, output.get('detail') or '缺少可回放班次，试评暂缓')
    if output.get('fallback'):
        return service.complete_trial({'trial_code': output['code'],
                                       'k': data.k or data.neighbors})
    return output


def _resume(data: TrialCode, user):
    with transaction() as conn:
        trial = service.resume_trial(conn, data)
        record(conn, user, 'lead_shifts.resume_trial')
    if trial.get('status') == 'queued':
        trial = service.resume_trial_now(trial)
    return trial


@router.post('/lead_shifts/resume-trial')
@router.post('/lead_shifts/weight-trials/resume')
def resume_trial(data: TrialCode, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    return _resume(data, user)


@router.post('/lead_shifts/weight-trials/{code}/resume')
def resume_named_trial(code: str, user=Depends(actor)):
    allow(user, ('operator', 'reviewer'))
    return _resume(TrialCode(code=code), user)


@router.post('/lead_shifts/replay-weights')
@router.post('/lead_shifts/weights/replay')
@router.post('/lead_shifts/weights/evaluate')
def replay_weights_now(data: TrialWeights, user=Depends(actor)):
    """Synchronous convenience: freeze the batch, evaluate and finalize at once."""
    allow(user, ('operator', 'reviewer'))
    with transaction() as conn:
        output = service.submit_trial(conn, user, data, enqueue=False)
        record(conn, user, 'lead_shifts.trial_weights')
    if output.get('deferred'):
        return output
    return service.complete_trial({'trial_code': output['code'],
                                   'k': data.k or data.neighbors})
