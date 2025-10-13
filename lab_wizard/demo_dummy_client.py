import os
import sys
from lib.instruments.general.computer import ComputerParams
from lib.instruments.dummy_volt import DummyVoltParams


def main():
	# Accept URI via CLI arg or environment variable LAB_WIZARD_BROKER_URI
	uri = None
	if len(sys.argv) > 1:
		uri = sys.argv[1]
	if uri is None:
		uri = os.environ.get("LAB_WIZARD_BROKER_URI")
	if not uri:
		print(
			"Usage: uv run demo_dummy_client.py <PYRO_URI>\n"
			"Or set LAB_WIZARD_BROKER_URI in the environment.\n"
			"Example: PYRO:obj_xxx@127.0.0.1:9100"
		)
		sys.exit(2)

	comp_params = ComputerParams(mode="remote", server_uri=uri)
	comp = comp_params.create_inst()

	# Add dummy instrument (key becomes resource name -> dummy:demo1)
	dummy = comp.add_child(DummyVoltParams(resource_name="demo1"), "demo1")
	print("[client] Querying dummy volt...")
	print("Voltage:", dummy.get_voltage())


if __name__ == "__main__":
	main()
