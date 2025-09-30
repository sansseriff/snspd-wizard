from lib.instruments.general.prologix_gpib import PrologixGPIBParams
from lib.instruments.sim900.modules.sim928 import Sim928Params
from lib.instruments.sim900.sim900 import Sim900Params
from snspd_measure.lib.instruments.dbay.dbay import DBayParams
from snspd_measure.lib.instruments.dbay.modules.dac4d import Dac4DChannelParams, Dac4DParams


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


dac4d = (
    DBayParams(server_address="FAKE")
    .create_inst()
    .add_child(Dac4DParams(), "1")
    .add_child(Dac4DChannelParams(), "2")
)

dac4d.set_voltage(1.0)


inst1 = (
    Inst("/dev/ttyUSB0", PrologixGPIBParams())
    .add_child(Sim900Params(), "3")
    .add_child(Sim928Params(), "1")
)


inst2 = (
    Inst("Prologix", PrologixGPIBParams())
    .add_child(Sim900Params(), "sim900")
    .add_child(Sim928Params(), "1")
)


inst3 = (
    Inst("Prologix", PrologixGPIBParams())
    .add_child(Sim900Params(), "sim900_2")
    .add_child(Sim928Params(), "1")
)

Inst(PrologixGPIBParams).add_child(Sim900Params).add_child(Sim928Params)




dac4d.set_voltage(1)
print(dac4d.channel_index)




sim928.set_voltage(3.0)


#    .add_child("3", Sim900Params())
#    .add_child("1", Sim928Params())
# )

# sim928.set_voltage(3.0)
