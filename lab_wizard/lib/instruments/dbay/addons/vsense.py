from pydantic import BaseModel
from typing import List


class ChSenseState(BaseModel):
    index: int
    voltage: float
    measuring: bool
    name: str

class IVsenseAddon(BaseModel):
    channels: List[ChSenseState]



class VsenseChange(BaseModel):
    module_index: int
    index: int
    voltage: float
    measuring: bool
    name: str