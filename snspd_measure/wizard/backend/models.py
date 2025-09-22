from dataclasses import dataclass
from pydantic import BaseModel
from pathlib import Path
from typing import Any



class MeasurementInfo(BaseModel):
    """Information about available measurements"""

    name: str
    description: str
    # required_instruments: dict[str, Any]
    measurement_dir: Path


class Env(BaseModel):

    base_dir: Path = Path(__file__).parent.parent.parent / "lib"
    instruments_dir: Path = base_dir / "instruments"
    measurements_dir: Path = base_dir / "measurements"
    projects_dir: Path = base_dir / "projects"



class MatchingReq(BaseModel):
    """A concrete instrument class that matches a required base type.

    Returned by discovery to populate UI choices.
    """

    module: str               # e.g., "lib.instruments.sim900.modules.sim928"
    class_name: str           # e.g., "Sim928"
    qualname: str             # e.g., "lib.instruments.sim900.modules.sim928.Sim928"
    file_path: Path           # absolute path to the defining file
    friendly_name: str        # short human label (defaults to class_name)



@dataclass
class FilledReq:

    variable_name: str
    base_type: Any
    matching_instruments: list[MatchingReq]


class OutputReq(BaseModel):

    variable_name: str
    base_type: str
    matching_instruments: list[MatchingReq]