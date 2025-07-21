from pydantic import BaseModel, Field, ConfigDict
from typing import Union, List


# Measurement configuration
class MeasurementConfig(BaseModel):
    start_V: float = Field(alias="start_V")
    end_V: float = Field(alias="end_V")
    step_V: float = Field(alias="step_V")
    bias_resistance: float = Field(alias="bias_resistance")
    voltage_source_1: str = Field(alias="voltage_source_1")
    voltage_source_2: str = Field(alias="voltage_source_2")
    voltage_sense_1: str = Field(alias="voltage_sense_1")
    voltage_sense_2: str = Field(alias="voltage_sense_2")


# SIM900 Module Types
class Sim900ModuleType(str, Enum):
    SIM928 = "sim928"
    SIM970 = "sim970"


class Sim900ModuleBase(BaseModel):
    slot: int
    attribute: str
    offline: bool = False


class SIM928Module(Sim900ModuleBase):
    type: Sim900ModuleType = Sim900ModuleType.SIM928
    settling_time: float = Field(alias="settlingTime")


class SIM970Module(Sim900ModuleBase):
    type: Sim900ModuleType = Sim900ModuleType.SIM970
    channel: int


# Discriminated union for SIM900 modules
Sim900Module = Annotated[Union[SIM928Module, SIM970Module], Field(discriminator="type")]


# DBay Module Types
class DBayModuleType(str, Enum):
    DAC4D = "dac4D"
    ACD4D = "acd4D"


class DBayModuleBase(BaseModel):
    slot: int
    attribute: str
    offline: bool = False


class DAC4DModule(DBayModuleBase):
    type: DBayModuleType = DBayModuleType.DAC4D
    channel: int


class ACD4DModule(DBayModuleBase):
    type: DBayModuleType = DBayModuleType.ACD4D
    channel: int


# Discriminated union for DBay modules
DBayModule = Annotated[Union[DAC4DModule, ACD4DModule], Field(discriminator="type")]


# Instrument Types
class InstrumentType(str, Enum):
    SIM900 = "sim900-mainframe"
    DBAY = "dbay-mainframe"


class InstrumentBase(BaseModel):
    pass


class SIM900Instrument(InstrumentBase):
    type: InstrumentType = InstrumentType.SIM900
    port: str
    gpib_addr: int = Field(alias="gpibAddr")
    modules: List[Sim900Module] = []


class DBayInstrument(InstrumentBase):
    type: InstrumentType = InstrumentType.DBAY
    ip_address: str = Field(alias="ip_address")
    port: int
    modules: List[DBayModule] = []


# Discriminated union for instruments
Instrument = Annotated[
    Union[SIM900Instrument, DBayInstrument], Field(discriminator="type")
]


# Saver Types
class SaverType(str, Enum):
    JSON = "json"
    CSV = "csv"
    DATABASE = "database"


class SaverBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class JSONFileSaver(SaverBase):
    type: SaverType = SaverType.JSON
    file_path: str = Field(alias="file_path")
    include_timestamp: bool = Field(default=True, alias="include_timestamp")
    include_metadata: bool = Field(default=True, alias="include_metadata")


class CSVFileSaver(SaverBase):
    type: SaverType = SaverType.CSV
    file_path: str = Field(alias="file_path")
    include_timestamp: bool = Field(default=True, alias="include_timestamp")


class DatabaseSaver(SaverBase):
    type: SaverType = SaverType.DATABASE
    connection_string: str = Field(alias="connection_string")
    table_name: str = Field(alias="table_name")


# Discriminated union for savers
FileSaver = Annotated[
    Union[JSONFileSaver, CSVFileSaver, DatabaseSaver], Field(discriminator="type")
]


class SaverConfig(BaseModel):
    file_saver: FileSaver = Field(alias="file_saver")


# Plotter Types
class PlotterType(str, Enum):
    WEB = "web"
    DESKTOP = "desktop"
    FILE = "file"


class PlotterBase(BaseModel):
    model_config = ConfigDict(extra="forbid")


class WebPlotter(PlotterBase):
    type: PlotterType = PlotterType.WEB
    address: str


class DesktopPlotter(PlotterBase):
    type: PlotterType = PlotterType.DESKTOP
    refresh_rate: float = 1.0
    window_title: str = "Measurement Plot"


class FilePlotter(PlotterBase):
    type: PlotterType = PlotterType.FILE
    output_path: str = Field(alias="output_path")
    format: str = "png"
    dpi: int = 300


# Discriminated union for plotters
Plotter = Annotated[
    Union[WebPlotter, DesktopPlotter, FilePlotter], Field(discriminator="type")
]


class PlotterConfig(BaseModel):
    web_plotter: Plotter = Field(alias="web_plotter")


# Main configuration model
class MeasurementConfiguration(BaseModel):
    measurement: MeasurementConfig
    instruments: List[Instrument]
    saver: SaverConfig
    plotter: PlotterConfig
