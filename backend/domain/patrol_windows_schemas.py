from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class RegisterWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    route: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    starts_at: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    ends_at: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    phase: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    tag: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class ComparePhase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    window: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
