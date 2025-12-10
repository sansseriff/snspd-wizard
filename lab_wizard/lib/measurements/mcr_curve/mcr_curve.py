"""
MCR (Maximum Count Rate) Curve Measurement

This module implements maximum count rate measurements for SNSPD devices.
It sweeps optical attenuation while measuring photon count rates to determine
the maximum count rate vs efficiency trade-off.
"""

import time
import traceback
import numpy as np
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from pathlib import Path

from lab_wizard.lib.utilities.plotter import RealTimePlotter
from lab_wizard.lib.instruments.general.vsource import VSource
from lab_wizard.lib.instruments.general.vsense import VSense


class MCRCurveMeasurement:
    """MCR curve measurement class"""

    def __init__(
        self,
        params: MCRCurveParams,
        voltage_source: VSource,
        voltage_sense: VSense,
        attenuator: Attenuator,  # Attenuator acts as optical source
        counter: Counter,
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize MCR curve measurement

        Args:
            params: Measurement parameters
            voltage_source: Bias voltage source
            voltage_sense: Voltage sensing instrument
            attenuator: Variable optical attenuator
            counter: Photon counter
            output_dir: Output directory for data files
        """
        self.params = params
        self.voltage_source = voltage_source
        self.voltage_sense = voltage_sense
        self.attenuator = attenuator
        self.counter = counter
        self.output_dir = output_dir or Path.cwd()

        # Data storage
        self.data_handler = DataHandler(self.output_dir)
        self.measurement_data: List[Dict[str, Any]] = []

        # Plotting
        self.plotter = None
        self.efficiency_plotter = None
        if params.plot_realtime:
            self.plotter = RealTimePlotter(
                title="MCR Curve",
                xlabel="Optical Attenuation (dB)",
                ylabel="Photon Count Rate (#/sec)",
                log_y=True,
            )
            self.efficiency_plotter = RealTimePlotter(
                title="Normalized Efficiency vs Count Rate",
                xlabel="Count Rate (#/sec)",
                ylabel="Normalized Efficiency",
                log_x=True,
                log_y=True,
            )

        self._setup_complete = False
        self._measurement_running = False

    def setup_counter(self):
        """Configure the counter for MCR measurements"""
        try:
            self.counter.reset()
            time.sleep(0.1)

            # Configure counter parameters
            if hasattr(self.counter, "set_impedance"):
                self.counter.set_impedance(self.params.impedance)
            if hasattr(self.counter, "set_coupling"):
                self.counter.set_coupling(self.params.coupling)
            if hasattr(self.counter, "set_trigger_level"):
                self.counter.set_trigger_level(self.params.trigger_level)
            if hasattr(self.counter, "set_slope"):
                self.counter.set_slope(self.params.slope)
            if hasattr(self.counter, "disable_noise_rejection"):
                self.counter.disable_noise_rejection()

            # Set up totalize mode
            if hasattr(self.counter, "set_totalize_time"):
                self.counter.set_totalize_time(self.params.gate_time)

            time.sleep(1)
            print("Counter setup complete")

        except Exception as e:
            raise RuntimeError(f"Counter setup failed: {e}")

    def setup_instruments(self):
        """Initialize and configure all instruments"""
        try:
            print("Setting up instruments...")

            # Connect voltage source
            if not self.voltage_source.is_connected():
                self.voltage_source.connect()

            # Connect voltage sense
            if not self.voltage_sense.is_connected():
                self.voltage_sense.connect()

            # Connect attenuator
            if not self.attenuator.is_connected():
                self.attenuator.connect()

            # Connect counter
            if not self.counter.is_connected():
                self.counter.connect()

            # Setup counter
            self.setup_counter()

            # Set attenuator wavelength if supported
            if hasattr(self.attenuator, "set_wavelength"):
                self.attenuator.set_wavelength(self.params.atten_wavelength)

            # Set bias voltage
            bias_voltage = (
                (self.params.bias_current - self.params.bias_offset)
                * self.params.bias_resistance
                * 1e-6
            )

            self.voltage_source.set_output(bias_voltage)
            self.voltage_source.enable_output()

            print(f"Set bias voltage: {bias_voltage:.6f} V")
            time.sleep(1)

            self._setup_complete = True
            print("Instrument setup complete")

        except Exception as e:
            self.cleanup_instruments()
            raise RuntimeError(f"Instrument setup failed: {e}")

    def cleanup_instruments(self):
        """Safely disconnect all instruments"""
        print("Cleaning up instruments...")

        # Turn off voltage source
        try:
            if self.voltage_source.is_connected():
                self.voltage_source.disable_output()
                self.voltage_source.disconnect()
        except Exception as e:
            print(f"Error disconnecting voltage source: {e}")

        # Disconnect voltage sense
        try:
            if self.voltage_sense.is_connected():
                self.voltage_sense.disconnect()
        except Exception as e:
            print(f"Error disconnecting voltage sense: {e}")

        # Close attenuator shutters and disconnect
        try:
            if self.attenuator.is_connected():
                if hasattr(self.attenuator, "close_shutters"):
                    self.attenuator.close_shutters()
                self.attenuator.disconnect()
        except Exception as e:
            print(f"Error disconnecting attenuator: {e}")

        # Disconnect counter
        try:
            if self.counter.is_connected():
                self.counter.disconnect()
        except Exception as e:
            print(f"Error disconnecting counter: {e}")

    def measure_background_count_rate(self) -> float:
        """Measure background count rate with shutters closed"""
        try:
            print("Measuring background count rate...")

            # Close shutters
            if hasattr(self.attenuator, "close_shutters"):
                self.attenuator.close_shutters()
            time.sleep(1)

            # Get background counts
            background_counts = self.counter.get_counts()
            background_rate = background_counts / self.params.gate_time

            print(f"Background count rate: {background_rate:.2f} counts/sec")
            return background_rate

        except Exception as e:
            raise RuntimeError(f"Background measurement failed: {e}")

    def measure_reference_count_rate(self, background_rate: float) -> float:
        """Measure reference count rate with shutters open"""
        try:
            print("Measuring reference count rate...")

            # Open shutters
            if hasattr(self.attenuator, "open_shutters"):
                self.attenuator.open_shutters()
            time.sleep(1)

            # Get reference counts
            reference_counts = self.counter.get_counts()
            reference_rate = (
                reference_counts / self.params.gate_time
            ) - background_rate

            print(f"Reference count rate: {reference_rate:.2f} counts/sec")
            return reference_rate

        except Exception as e:
            raise RuntimeError(f"Reference measurement failed: {e}")

    def set_attenuator_values(self, a1: float, a2: float, a3: float, a4: float):
        """Set attenuation values for all four attenuator ports"""
        try:
            # Set attenuator values (based on original port mapping)
            if hasattr(self.attenuator, "set_attenuation"):
                self.attenuator.set_attenuation(1, a1)  # Port 1
                self.attenuator.set_attenuation(3, a2)  # Port 3
                self.attenuator.set_attenuation(5, a3)  # Port 5
                self.attenuator.set_attenuation(7, a4)  # Port 7
            else:
                # Fallback to generic source interface
                total_attenuation = a1 + a2 + a3 + a4
                self.attenuator.set_output(
                    -total_attenuation
                )  # Negative for attenuation

        except Exception as e:
            raise RuntimeError(f"Setting attenuator failed: {e}")

    def run_measurement(self) -> Dict[str, Any]:
        """Execute the complete MCR curve measurement"""
        if not self._setup_complete:
            raise RuntimeError(
                "Instruments not set up. Call setup_instruments() first."
            )

        self._measurement_running = True
        measurement_results = {
            "success": False,
            "data": [],
            "metadata": {},
            "error": None,
        }

        try:
            print("Starting MCR curve measurement...")

            # Calculate initial attenuation values
            step = self.params.atten_step
            range_val = self.params.atten_range / 2
            atten_max = self.params.atten_max

            A1 = step + range_val
            A2 = step + range_val
            A3 = atten_max - 2 * step - 2 * range_val
            A4 = self.params.atten4_fixed

            # Set initial attenuation
            self.set_attenuator_values(A1, A2, A3, A4)

            # Measure background and reference count rates
            background_rate = self.measure_background_count_rate()
            reference_rate = self.measure_reference_count_rate(background_rate)

            # Start measurement sweep
            current_atten = -(A1 + A2 + A3)

            print(f"Starting sweep from {current_atten:.2f} dB")

            while current_atten < (-atten_max + 2 * range_val):
                if not self._measurement_running:
                    break

                time.sleep(1)

                # Read voltage and counts
                sense_voltage = self.voltage_sense.get_value()
                raw_counts = self.counter.get_counts()
                count_rate = raw_counts / self.params.gate_time

                # Calculate corrected photon count rate
                photon_count_rate = count_rate - background_rate

                # Calculate relative attenuation and normalized efficiency
                relative_atten = current_atten + atten_max
                normalization = reference_rate * (10 ** (relative_atten / 10))
                normalized_efficiency = (
                    photon_count_rate / normalization if normalization > 0 else 0
                )

                # Store data point
                data_point = {
                    "attenuation_total": current_atten,
                    "attenuation_1": -A1,
                    "attenuation_2": -A2,
                    "attenuation_3": -A3,
                    "attenuation_4": -A4,
                    "count_rate": count_rate,
                    "photon_count_rate": photon_count_rate,
                    "sense_voltage": sense_voltage,
                    "normalized_efficiency": normalized_efficiency,
                    "timestamp": time.time(),
                }

                self.measurement_data.append(data_point)

                # Update plots
                if self.plotter:
                    self.plotter.add_point(current_atten, count_rate)
                if self.efficiency_plotter and photon_count_rate > 0:
                    self.efficiency_plotter.add_point(
                        photon_count_rate, normalized_efficiency
                    )

                print(
                    f"Atten: {current_atten:.2f} dB, PCR: {photon_count_rate:.2f} counts/sec"
                )

                # Adjust attenuation for next point
                if A1 > step:
                    A1 -= step
                    self.set_attenuator_values(A1, A2, A3, A4)
                else:
                    A2 -= step
                    self.set_attenuator_values(A1, A2, A3, A4)

                current_atten = -(A1 + A2 + A3)

            # Add background measurement to data
            background_point = {
                "attenuation_total": 0,
                "attenuation_1": 0,
                "attenuation_2": 0,
                "attenuation_3": 0,
                "attenuation_4": 0,
                "count_rate": background_rate,
                "photon_count_rate": 0,
                "sense_voltage": 0,
                "normalized_efficiency": 0,
                "timestamp": time.time(),
            }
            self.measurement_data.append(background_point)

            measurement_results["success"] = True
            measurement_results["data"] = self.measurement_data
            measurement_results["metadata"] = {
                "measurement_type": "mcr_curve",
                "background_rate": background_rate,
                "reference_rate": reference_rate,
                "parameters": self.params.__dict__,
            }

            print(
                f"MCR curve measurement completed. {len(self.measurement_data)} data points collected."
            )

        except Exception as e:
            error_msg = f"MCR measurement failed: {e}"
            print(error_msg)
            print(traceback.format_exc())
            measurement_results["error"] = error_msg

        finally:
            self._measurement_running = False

            # Save data if requested
            if self.params.save_data and self.measurement_data:
                try:
                    self.save_data(measurement_results)
                except Exception as e:
                    print(f"Error saving data: {e}")

            # Keep plots open if requested
            if self.plotter:
                self.plotter.show()

        return measurement_results

    def save_data(self, results: Dict[str, Any]):
        """Save measurement data to files"""
        if not results["data"]:
            print("No data to save")
            return

        # Create metadata
        metadata = MeasurementMetadata(
            measurement_type="mcr_curve",
            timestamp=time.time(),
            parameters=self.params.__dict__,
            instrument_info={
                "voltage_source": str(type(self.voltage_source).__name__),
                "voltage_sense": str(type(self.voltage_sense).__name__),
                "attenuator": str(type(self.attenuator).__name__),
                "counter": str(type(self.counter).__name__),
            },
            additional_info=results.get("metadata", {}),
        )

        # Save data
        filename = f"mcr_curve_{int(time.time())}"
        saved_files = self.data_handler.save_data(
            results["data"], filename, metadata, formats=["csv", "hdf5"]
        )

        print(f"Data saved to: {', '.join(saved_files)}")

    def stop_measurement(self):
        """Stop the measurement if running"""
        self._measurement_running = False
        print("Stopping MCR measurement...")


def main():
    """Example usage of MCR curve measurement"""
    # This would be called with actual instrument instances
    # The CLI tool will handle the proper instantiation
    print("MCR Curve Measurement Module")
    print("Use the setup_measurement.py CLI tool to run measurements")


if __name__ == "__main__":
    main()
