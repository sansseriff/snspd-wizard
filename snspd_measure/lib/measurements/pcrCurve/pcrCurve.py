#!/usr/bin/env python3
"""
PCR Curve Measurement Module
author: GitHub Copilot
date: 2024

This module implements photon count rate (PCR) versus bias voltage measurements for SNSPDs.
It provides a modern, type-safe implementation with flexible threshold and triggering options.
"""

import time
import traceback
import numpy as np
from dataclasses import dataclass
from typing import Optional, Generator, Tuple, Dict, Any
from pathlib import Path

from ...utilities.plotter import PlotManager
from ...utilities.data_handler import DataHandler
from ...instruments.general.genericSource import GenericSource
from ...instruments.general.genericSense import GenericSense, GenericCounter


class PCRCurve:
    """
    Photon Count Rate vs Bias Voltage measurement class.

    This class implements PCR measurements with support for various threshold
    configurations, external triggering, and real-time plotting.
    """

    def __init__(self, params: PCRCurveParams, output_dir: Optional[Path] = None):
        """
        Initialize PCR curve measurement.

        Args:
            params: Measurement parameters
            output_dir: Directory for saving data and plots
        """
        self.params = params
        self.output_dir = output_dir or Path.cwd()

        # Initialize data handler and plotter
        self.data_handler = DataHandler(self.output_dir)
        self.plot_manager = PlotManager() if params.real_time_plot else None

        # Store for current measurement data
        self.current_data = []
        self.photon_rate = params.photon_rate

        # Initialize instruments (will be set via dependency injection)
        self.voltage_source: Optional[GenericSource] = None
        self.voltmeter: Optional[GenericSense] = None
        self.counter: Optional[GenericCounter] = None

    def set_instruments(
        self,
        voltage_source: GenericSource,
        voltmeter: GenericSense,
        counter: GenericCounter,
    ):
        """Set the instruments for this measurement."""
        self.voltage_source = voltage_source
        self.voltmeter = voltmeter
        self.counter = counter

    def bias_generator(self) -> Generator[float, None, None]:
        """Generate bias voltage values for the sweep."""
        if np.isclose(self.params.bias_start_V, self.params.bias_end_V):
            yield self.params.bias_start_V
            return

        bias_values = np.arange(
            self.params.bias_start_V,
            self.params.bias_end_V + self.params.bias_step_V / 2,
            self.params.bias_step_V,
        )

        # Ensure end point is included
        if not np.isclose(bias_values[-1], self.params.bias_end_V):
            bias_values = np.append(bias_values, self.params.bias_end_V)

        # Start from 0V if not already included
        if not np.isclose(bias_values[0], 0.0):
            bias_values = np.insert(bias_values, 0, 0.0)

        for voltage in bias_values:
            yield voltage

    def threshold_generator(self) -> Generator[Tuple[float, float, float], None, None]:
        """
        Generate threshold values based on configuration.

        Yields:
            Tuple of (threshold_mV, max_voltage_mV, peak_to_peak_mV)
        """
        if not self.counter:
            raise ValueError("Counter not set")

        # Get pulse characteristics from counter
        # Note: This is a simplified version - real implementation would
        # query the counter for actual pulse characteristics
        is_negative_pulse = self.params.slope.lower() == "neg"

        if is_negative_pulse:
            max_v = -100.0  # Assume -100mV max for negative pulses
            ptp_v = 200.0  # Assume 200mV peak-to-peak
        else:
            max_v = 100.0  # Assume +100mV max for positive pulses
            ptp_v = 200.0  # Assume 200mV peak-to-peak

        if self.params.threshold_type.lower() == "absolute":
            yield self.params.threshold_value, max_v, ptp_v

        elif self.params.threshold_type.lower() == "auto":
            if is_negative_pulse:
                threshold = max_v + (1.0 - self.params.threshold_relative) * ptp_v
            else:
                threshold = max_v - self.params.threshold_relative * ptp_v
            yield threshold, max_v, ptp_v

        elif self.params.threshold_type.lower() == "sweep":
            thresh_array = np.arange(
                self.params.threshold_sweep_start,
                self.params.threshold_sweep_end + self.params.threshold_sweep_step / 2,
                self.params.threshold_sweep_step,
            )

            # Ensure end point is included
            if not np.isclose(thresh_array[-1], self.params.threshold_sweep_end):
                thresh_array = np.append(thresh_array, self.params.threshold_sweep_end)

            # Round to nearest 2.5mV and remove duplicates
            thresh_array = np.round(thresh_array / 2.5) * 2.5
            thresh_array = np.unique(thresh_array)

            # Reverse for negative pulses (sweep from high to low)
            if is_negative_pulse:
                thresh_array = thresh_array[::-1]

            for threshold in thresh_array:
                yield threshold, max_v, ptp_v
        else:
            raise ValueError(f"Unknown threshold type: {self.params.threshold_type}")

    def setup_counter(self):
        """Configure the counter for PCR measurements."""
        if not self.counter:
            raise ValueError("Counter not set")

        # Reset and configure counter
        self.counter.reset()

        # Set basic parameters
        self.counter.configure_input(
            impedance=self.params.impedance,
            coupling=self.params.coupling,
            threshold_mv=self.params.threshold_value,
        )

        self.counter.configure_trigger(
            slope=self.params.slope, noise_rejection=self.params.nrej
        )

        # Configure measurement mode
        if self.params.ext_trigger:
            self.counter.configure_external_trigger(
                trigger_slope=self.params.trigger_slope,
                trigger_count=self.params.trigger_count,
                sample_count=self.params.sample_count,
                delay=self.params.trigger_delay,
                period=self.params.trigger_period,
            )
        else:
            self.counter.configure_totalize_mode(self.params.gate_time)

        time.sleep(0.1)  # Allow settings to stabilize

    def calibrate_photon_rate(self) -> float:
        """
        Calibrate the total photon rate.

        Returns:
            Calibrated photon rate in photons/sec
        """
        # Simplified calibration - in practice this would involve
        # measuring with known light sources or using calibrated detectors
        print("Calibrating photon rate...")
        print("Note: This is a simplified calibration routine")

        if self.photon_rate is None:
            # Default calibration value
            self.photon_rate = 100000.0  # 100k photons/sec
            print(f"Using default photon rate: {self.photon_rate} photons/sec")

        return self.photon_rate

    def take_measurement(self, bias_voltage: float, threshold: float) -> Dict[str, Any]:
        """
        Take a single PCR measurement at specified bias and threshold.

        Args:
            bias_voltage: Bias voltage in volts
            threshold: Threshold in mV

        Returns:
            Dictionary containing measurement results
        """
        if not all([self.voltage_source, self.voltmeter, self.counter]):
            raise ValueError("All instruments must be set before measurement")

        # Set bias voltage
        self.voltage_source.set_voltage(bias_voltage)
        time.sleep(self.params.settling_time)

        # Read actual voltage
        sense_voltage = self.voltmeter.read_voltage()

        # Set threshold
        self.counter.set_threshold_mv(threshold)

        # Take measurement
        measurement_time = time.time()
        print(
            f"Measuring: Bias={bias_voltage:.3f}V, Sense={sense_voltage:.3f}V, "
            f"Threshold={threshold:.1f}mV, Gate={self.params.gate_time}s"
        )

        # Get counts
        if self.params.ext_trigger:
            raw_counts = self.counter.get_triggered_counts()
            # Process triggered data if needed
            counts = np.array(raw_counts).flatten()
        else:
            counts = self.counter.get_totalized_counts()
            if isinstance(counts, (int, float)):
                counts = [counts]

        # Calculate count rate
        total_counts = np.sum(counts)
        count_rate = total_counts / self.params.gate_time
        count_error = np.sqrt(total_counts) / self.params.gate_time

        return {
            "timestamp": measurement_time,
            "bias_voltage": bias_voltage,
            "sense_voltage": sense_voltage,
            "threshold_mv": threshold,
            "total_counts": total_counts,
            "count_rate": count_rate,
            "count_error": count_error,
            "gate_time": self.params.gate_time,
            "raw_counts": counts,
        }

    def run_measurement(self) -> str:
        """
        Execute the complete PCR curve measurement.

        Returns:
            Path to saved data file
        """
        if not all([self.voltage_source, self.voltmeter, self.counter]):
            raise ValueError("All instruments must be set before measurement")

        print("Starting PCR Curve Measurement")
        print("=" * 50)

        # Calibrate if requested
        if self.params.auto_calibrate:
            self.calibrate_photon_rate()
        elif self.photon_rate is not None:
            print(f"Using specified photon rate: {self.photon_rate} photons/sec")

        # Initialize plot
        if self.plot_manager:
            self.plot_manager.create_plot(
                title="PCR Curve",
                xlabel="Bias Voltage (V)",
                ylabel="Count Rate (counts/sec)",
            )

        # Connect instruments
        try:
            print("Connecting instruments...")
            self.voltage_source.connect()
            self.voltmeter.connect()
            self.counter.connect()

            # Turn on voltage source and set to 0V
            self.voltage_source.set_output_state(True)
            self.voltage_source.set_voltage(0.0)

            # Setup counter
            self.setup_counter()

        except Exception as e:
            print(f"Error during instrument setup: {e}")
            self._cleanup_instruments()
            raise

        # Main measurement loop
        all_data = []

        try:
            for sweep_num in range(self.params.num_sweeps):
                if self.params.num_sweeps > 1:
                    print(f"\nSweep {sweep_num + 1} of {self.params.num_sweeps}")

                for bias in self.bias_generator():
                    threshold_measurements = []

                    for threshold, max_v, ptp_v in self.threshold_generator():
                        try:
                            measurement = self.take_measurement(bias, threshold)
                            threshold_measurements.append(measurement)

                            # Update real-time plot with average for this bias
                            if self.plot_manager and len(threshold_measurements) == 1:
                                # Plot first threshold measurement for each bias
                                self.plot_manager.update_plot(
                                    bias,
                                    measurement["count_rate"],
                                    yerr=measurement["count_error"],
                                )

                            # Check for zero counts (possible threshold too high)
                            if measurement["total_counts"] == 0:
                                print(
                                    "  Zero counts detected - threshold may be too high"
                                )
                                break

                        except Exception as e:
                            print(
                                f"Error in measurement at bias={bias}V, threshold={threshold}mV: {e}"
                            )
                            continue

                    # Store all threshold measurements for this bias
                    all_data.extend(threshold_measurements)

        except KeyboardInterrupt:
            print("\nMeasurement interrupted by user")
        except Exception as e:
            print(f"Error during measurement: {e}")
            traceback.print_exc()
        finally:
            self._cleanup_instruments()

        # Save data
        if self.params.save_data and all_data:
            filename = self._save_data(all_data)
            print(f"\nData saved to: {filename}")

            if self.plot_manager:
                plot_file = self.output_dir / f"{filename.stem}_plot.png"
                self.plot_manager.save_plot(plot_file)
                print(f"Plot saved to: {plot_file}")

            return str(filename)
        else:
            print("No data to save or saving disabled")
            return ""

    def _cleanup_instruments(self):
        """Safely disconnect and turn off instruments."""
        try:
            if self.voltage_source:
                self.voltage_source.set_voltage(0.0)
                self.voltage_source.set_output_state(False)
                self.voltage_source.disconnect()
        except Exception as e:
            print(f"Error cleaning up voltage source: {e}")

        try:
            if self.voltmeter:
                self.voltmeter.disconnect()
        except Exception as e:
            print(f"Error cleaning up voltmeter: {e}")

        try:
            if self.counter:
                self.counter.disconnect()
        except Exception as e:
            print(f"Error cleaning up counter: {e}")

        if self.plot_manager:
            self.plot_manager.show_plot()

    def _save_data(self, data_list) -> Path:
        """Save measurement data to file."""
        # Create structured data for saving
        structured_data = {
            "measurement_type": "pcr_curve",
            "parameters": self.params.__dict__,
            "data": data_list,
            "columns": [
                "timestamp",
                "bias_voltage",
                "sense_voltage",
                "threshold_mv",
                "total_counts",
                "count_rate",
                "count_error",
                "gate_time",
            ],
        }

        # Generate filename with timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = self.output_dir / f"pcr_curve_{timestamp}"

        return self.data_handler.save_data(structured_data, filename)


def main():
    """Example usage of the PCR curve measurement."""
    # Example parameters
    params = PCRCurveParams(
        bias_start_V=0.0,
        bias_end_V=2.0,
        bias_step_V=0.1,
        threshold_type="auto",
        threshold_relative=0.5,
        gate_time=1.0,
        real_time_plot=True,
    )

    # Create measurement instance
    pcr_measurement = PCRCurve(params)

    print("PCR Curve measurement module loaded successfully")
    print("Use with appropriate instruments via the CLI tool")


if __name__ == "__main__":
    main()
