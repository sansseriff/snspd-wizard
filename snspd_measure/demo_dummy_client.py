from lib.instruments.general.computer import ComputerParams
from lib.instruments.dummy_volt import DummyVoltParams, DummyVolt

# Substitute URI from broker output:
URI = "PYRO:obj_c92b23260d43433c9235a4d43d747b03@127.0.0.1:9100"

comp_params = ComputerParams(mode="remote", server_uri=URI)
comp = comp_params.create_inst()

# Add dummy instrument (key becomes resource name -> dummy:demo1)
dummy = comp.add_child(DummyVoltParams(resource_name="demo1"), "demo1")
print("Voltage:", dummy.get_voltage())
