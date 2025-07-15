"""
visaInst.py - General utility class for VISA instruments

Based on the original visaInst.py from the SNSPD library but cleaned up for the new structure.
"""

import pyvisa as visa


class visaInst:
    """
    Generic base class for instruments connected via VISA (TCP/IP, USB, etc.)
    """

    def __init__(self, ipAddress, port=5025, offline=False):
        """
        :param ipAddress: The IP address (e.g., '10.7.0.114')
        :param port: The port on the host computer
        :param offline: If True, simulate instrument communication for testing
        """
        self.ipAddress = ipAddress
        self.port = port
        self.offline = offline
        self.inst = None

    def connect(self):
        """Connect to the instrument"""
        if self.offline:
            print(f"Connected to offline instrument {self.__class__}")
            return True

        try:
            rm = visa.ResourceManager("@py")
            resource_string = f"TCPIP::{self.ipAddress}::{self.port}::SOCKET"
            print(f"Opening resource: {resource_string}")

            self.inst = rm.open_resource(resource_string)
            self.inst.read_termination = "\n"
            self.inst.timeout = max(10000, getattr(self.inst, "timeout", 5000))

            # Try to get instrument ID
            try:
                idn = self.query("*IDN?")
                print(f"Connected to: {idn}")
            except:
                print("Connected (no IDN response)")

            return self.inst

        except Exception as e:
            print(f"Failed to connect to {self.ipAddress}:{self.port} - {e}")
            raise

    def disconnect(self):
        """Disconnect from the instrument"""
        if self.offline:
            print(f"Disconnected from offline instrument {self.__class__}")
            return True

        if self.inst:
            return self.inst.close()
        return True

    def write(self, cmd):
        """Write command to instrument"""
        if self.offline:
            return True
        if not self.inst:
            raise RuntimeError("Not connected to instrument")
        return self.inst.write(cmd)

    def read(self):
        """Read response from instrument"""
        if self.offline:
            return ""
        if not self.inst:
            raise RuntimeError("Not connected to instrument")
        return self.inst.read()

    def query(self, cmd):
        """Send command and read response"""
        if self.offline:
            return ""
        if not self.inst:
            raise RuntimeError("Not connected to instrument")
        return self.inst.query(cmd)

    def write_binary_values(self, cmd, values):
        """Write binary values to instrument"""
        if self.offline:
            return True
        if not self.inst:
            raise RuntimeError("Not connected to instrument")
        return self.inst.write_binary_values(cmd, values)
