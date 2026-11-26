from typing import Annotated

from pydantic import BaseModel, ConfigDict, FiniteFloat, StringConstraints

class RegisterRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    checkpoint: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
    max_leads: int


class PauseRoute(BaseModel):
    model_config = ConfigDict(extra="forbid")
    route: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
