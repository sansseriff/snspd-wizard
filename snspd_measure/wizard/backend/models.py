from typing import Required
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