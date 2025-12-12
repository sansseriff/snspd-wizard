from lab_wizard.lib.instruments.general.prologix_gpib import PrologixGPIBParams
from lab_wizard.lib.instruments.sim900.modules.sim928 import Sim928Params
from lab_wizard.lib.instruments.sim900.sim900 import Sim900Params
from lab_wizard.lib.instruments.dbay.dbay import DBayParams
from lab_wizard.lib.instruments.dbay.modules.dac4d import Dac4DParams
from lab_wizard.lib.instruments.sim900.modules.sim970 import Sim970Params


sim928 = (
    PrologixGPIBParams(port="FAKE")
    .create_inst()
    .add_child(Sim900Params(), "3")
    .add_child(Sim928Params(), "1")
)


thing = (
    PrologixGPIBParams(port="FAKE")
    .create_inst()
    .add_child(Sim900Params(), "3")
    .add_child(Sim928Params(), "1")
)


# This would call real instrument code; just test the chain creation
sim970_chain = (
    PrologixGPIBParams(port="FAKE")
    .create_inst()
    .add_child(Sim900Params(), "3")
    .add_child(Sim970Params(), "5")
)
# sim970_chain.get_channel(3).get_voltage() - disabled: mock doesn't return valid voltage


# After refactor, adding a Dac4D module automatically materializes its channels
dac4d_module = (
    DBayParams(server_address="FAKE").create_inst().add_child(Dac4DParams(), "1")
)

# Access channel 0 (example) and set voltage if API available
try:
    dac4d_module.get_channel(0).set_voltage(1.0)  # type: ignore[attr-defined]
except Exception:
    pass


## Removed deprecated Inst-based examples; new pattern relies on Params -> create_inst()


try:
    dac4d_module.get_channel(0).set_voltage(1)  # type: ignore[attr-defined]
    print(dac4d_module.get_channel(0).channel_index)  # type: ignore[attr-defined]
except Exception:
    pass


sim928.set_voltage(3.0)


#    .add_child("3", Sim900Params())
#    .add_child("1", Sim928Params())
# )

# sim928.set_voltage(3.0)
