from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

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
