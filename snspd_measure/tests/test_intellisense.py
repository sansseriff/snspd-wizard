from lib.instruments.general.prologix import PrologixGPIBParams
from lib.instruments.sim900.modules.sim928 import Sim928Params
from lib.instruments.sim900.sim900 import Sim900Params


sim928 = (
    PrologixGPIBParams(port="FAKE")
    .create_inst()
    .add_child("3", Sim900Params())
    .add_child("1", Sim928Params())
)


sim928.set_voltage(3.0)


#    .add_child("3", Sim900Params())
#    .add_child("1", Sim928Params())
# )

# sim928.set_voltage(3.0)
