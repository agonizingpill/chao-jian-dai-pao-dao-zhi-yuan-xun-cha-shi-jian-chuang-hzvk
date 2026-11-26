from typing import Annotated, Any, Optional

from pydantic import BaseModel, ConfigDict, StringConstraints

class AssignLead(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    window: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    lead: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    contact: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class CheckIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shift: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    checkpoint: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    arrived_at: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class HandBack(BaseModel):
    model_config = ConfigDict(extra="forbid")
    shift: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    # Replayable clock for the moment the shift ended; optional because the
    # original hand-back form only carried the shift code.
    ended_at: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
    handed_back_at: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
    hand_back_at: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
    returned_at: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
    at: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
    time: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None


class EstimateArrival(BaseModel):
    # Tolerant: callers may address the target by shift, window or generic code.
    model_config = ConfigDict(extra="allow")
    shift: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
    window: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
    code: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
    target: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
    weights: Optional[Any] = None
    distance_weights: Optional[Any] = None
    k: Optional[int] = None
    neighbors: Optional[int] = None


class TrialWeights(BaseModel):
    # Keep extras so differently named weight fields from callers/tests survive
    # and are interpreted by learning.extract_weights.
    model_config = ConfigDict(extra="allow")
    phase_weight: Optional[float] = None
    duration_weight: Optional[float] = None
    phase: Optional[float] = None
    duration: Optional[float] = None
    circle_weight: Optional[float] = None
    spread_weight: Optional[float] = None
    weight: Optional[Any] = None
    weights: Optional[Any] = None
    distance_weights: Optional[Any] = None
    k: Optional[int] = None
    neighbors: Optional[int] = None
    note: Optional[Annotated[str, StringConstraints(max_length=300)]] = None


class TrialCode(BaseModel):
    model_config = ConfigDict(extra="allow")
    code: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
    trial: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
    token: Optional[Annotated[str, StringConstraints(strip_whitespace=True, max_length=160)]] = None
