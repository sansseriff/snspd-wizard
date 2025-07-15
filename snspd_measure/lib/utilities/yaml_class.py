from pydantic import BaseModel
from typing import Union, List


class Config(BaseModel):
    measurement: Measurement
    instruments: List[Union[InstrumentParams, MainframeParams]] = Field(
        discriminator="type"
    )
