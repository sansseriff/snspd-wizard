from pydantic import BaseModel
from typing import Literal


class Core(BaseModel):
    slot: int
    type: str
    name: str


class IModule(BaseModel):
    core: Core


class Empty(IModule):
    module_type: Literal["empty"] = "empty"
    core: Core
