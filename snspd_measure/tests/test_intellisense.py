from lib.instruments.general.prologix import PrologixControllerParams
from lib.instruments.sim900.modules.sim928 import Sim928Params
from lib.instruments.sim900.sim900 import Sim900Params


sim928 = (
    PrologixControllerParams(port="FAKE")
    .corresponding_inst()
    .add_child("3", Sim900Params())
    .add_child("1", Sim928Params())
)


sim928.set_voltage(3.0)
