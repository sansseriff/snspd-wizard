from pydantic_yaml import to_yaml_file


from lib.utilities.model_tree import (
    Device,
    Exp,
    FileSaver,
    IVCurveParams,
    MplPlotter,
)

from lib.instruments.dbay.dbay import DBayParams
from lib.instruments.dbay.modules.dac4d import Dac4DParams

from lib.instruments.general.prologix_gpib import PrologixGPIBParams
from lib.instruments.sim900.modules.sim928 import Sim928Params
from lib.instruments.sim900.modules.sim970 import Sim970Params
from lib.instruments.sim900.sim900 import Sim900Params

from ruamel.yaml import YAML


def create_example_exp() -> Exp:

    return Exp(
        exp=IVCurveParams(
            start_voltage=-2.0, stop_voltage=2.0, step_voltage=0.1, num_points=41
        ),
        device=Device(name="MyDevice", model="R1C3", description="My first device"),
        saver={
            "default": FileSaver(
                file_path="data/my_data.csv",
                include_timestamp=True,
                include_metadata=True,
            )
        },
        plotter={"default": MplPlotter(figure_size=[8, 6], dpi=100)},
        instruments={
            "10.7.0.88": DBayParams(
                server_address="10.7.0.88",
                port=8345,
                children={"1": Dac4DParams()},
            ),
            "/dev/ttyUSB0": PrologixGPIBParams(
                port="/dev/ttyUSB0",
                baudrate=115200,
                children={
                    "5": Sim900Params(
                        children={
                            "1": Sim928Params(),
                            # SIM970 module in slot 5 with one active channel (channel 0)
                            "5": Sim970Params(),
                        }
                    )
                },
            ),
        },
    )


if __name__ == "__main__":

    # YAML writer configuration
    my_writer = YAML(
        typ="safe",
    )
    my_writer.default_flow_style = True
    my_writer.sort_base_mapping_type_on_output = False  # type: ignore[attr-defined]

    exp = create_example_exp()
    to_yaml_file("custom_setup.yaml", exp, custom_yaml_writer=my_writer)
    print("Wrote example setup to custom_setup.yaml")
