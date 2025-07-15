#!/usr/bin/env python3
"""
setup_measurement.py - CLI tool for setting up SNSPD measurement experiments

This tool provides an interactive CLI for:
1. Selecting measurement types
2. Choosing compatible instruments
3. Copying necessary files to a working directory
4. Generating measurement configuration

Author: Generated for SNSPD Library Restructure
Date: June 2025
"""

import os
import sys
import shutil
import importlib
import inspect
import argparse
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Type, List, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod


# Import the actual base classes from the instrument modules
from instruments.general.genericSource import GenericSource
from instruments.general.genericSense import GenericSense, GenericCounter


@dataclass
class MeasurementInfo:
    """Information about available measurements"""

    name: str
    description: str
    required_instruments: Dict[str, Type]
    measurement_dir: Path


@dataclass
class InstrumentInfo:
    """Information about available instruments"""

    display_name: str
    class_name: str
    module_name: str
    file_path: Path
    class_obj: Type[Any]


class MeasurementSetup:
    """Main CLI class for setting up measurements"""

    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.instruments_dir = self.base_dir / "instruments"
        self.measurements_dir = self.base_dir / "measurements"
        self.projects_dir = self.base_dir / "projects"

        # Ensure projects directory exists
        self.projects_dir.mkdir(exist_ok=True)

        # Add the new library to Python path
        sys.path.insert(0, str(self.base_dir))

    def discover_instruments(
        self, instrument_dir: Path, base_class: Type
    ) -> Dict[str, InstrumentInfo]:
        """Discover instruments that inherit from the given base class."""
        instruments = {}
        errors = []

        ######### HERE July 9th EOD

        # Look for Python files in the directory and subdirectories
        for py_file in instrument_dir.rglob("*.py"):
            if py_file.name.startswith("__") or py_file.name in [
                "visaInst.py",
                "serialInst.py",
            ]:
                continue

            try:
                # Convert file path to module name
                rel_path = py_file.relative_to(self.base_dir)
                module_name = str(rel_path.with_suffix("")).replace("/", ".")

                # Import the module
                module = importlib.import_module(module_name)

                # Find subclasses in this module
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (
                        issubclass(obj, base_class)
                        and obj != base_class
                        and obj.__module__ == module.__name__
                    ):
                        display_name = getattr(obj, "DISPLAY_NAME", name)

                        instruments[display_name] = InstrumentInfo(
                            display_name=display_name,
                            class_name=name,
                            module_name=module_name,
                            file_path=py_file,
                            class_obj=obj,
                        )

            except Exception as e:
                error_msg = f"Could not load {py_file.name}: {str(e)}"
                errors.append(error_msg)
                print(f"Warning: {error_msg}")

        if errors:
            print(f"\n⚠️  {len(errors)} instrument(s) failed to load.")
            print("Other instruments are still available.\n")

        return instruments

    def discover_measurements(self) -> Dict[str, MeasurementInfo]:
        """Discover available measurement types."""
        measurements = {}

        for measurement_dir in self.measurements_dir.iterdir():
            if not measurement_dir.is_dir() or measurement_dir.name.startswith("__"):
                continue

            # Look for the main measurement file
            measurement_file = measurement_dir / f"{measurement_dir.name}.py"
            if not measurement_file.exists():
                continue

            # Look for the template file to analyze required instruments
            template_file = (
                measurement_dir / f"{measurement_dir.name}Params.template.py"
            )

            try:
                required_instruments = {}
                description = f"{measurement_dir.name} measurement"

                if template_file.exists():
                    # Parse the template file to extract required instruments
                    # Try to import the template directly like we do with instruments
                    required_instruments = self._extract_instruments_from_template(
                        template_file
                    )

                    # Also read the file for docstring extraction
                    with open(template_file, "r") as f:
                        template_content = f.read()

                    # Try to extract description from docstring
                    if '"""' in template_content:
                        doc_start = template_content.find('"""')
                        doc_end = template_content.find('"""', doc_start + 3)
                        if doc_end > doc_start:
                            doc_content = template_content[doc_start + 3 : doc_end]
                            first_line = doc_content.strip().split("\n")[0]
                            if first_line and "Parameters" not in first_line:
                                description = first_line

                measurements[measurement_dir.name] = MeasurementInfo(
                    name=measurement_dir.name,
                    description=description,
                    required_instruments=required_instruments,
                    measurement_dir=measurement_dir,
                )

            except Exception as e:
                print(f"Warning: Could not parse {measurement_dir.name}: {e}")
                continue

        return measurements

    def select_instrument(
        self, instrument_type: str, available_instruments: Dict[str, InstrumentInfo]
    ) -> InstrumentInfo:
        """Interactive instrument selection."""
        print(f"\nAvailable {instrument_type}s:")

        instruments_list = list(available_instruments.items())
        for i, (display_name, info) in enumerate(instruments_list, 1):
            # Show description from class docstring if available
            if info.class_obj and hasattr(info.class_obj, "__doc__"):
                doc = info.class_obj.__doc__
                doc_line = doc.split("\n")[0] if doc else "No description"
            else:
                doc_line = "No description"
            print(f"{i}. {display_name} - {doc_line}")

        while True:
            try:
                choice = (
                    int(
                        input(
                            f"\nChoose {instrument_type} (1-{len(instruments_list)}): "
                        )
                    )
                    - 1
                )
                if 0 <= choice < len(instruments_list):
                    break
                print("Invalid choice, try again.")
            except (ValueError, KeyboardInterrupt):
                print("Please enter a number or Ctrl+C to exit.")

        return instruments_list[choice][1]

    def copy_files_to_project(
        self,
        project_dir: Path,
        selected_instruments: Dict[str, InstrumentInfo],
        measurement_info: MeasurementInfo,
    ):
        """Copy necessary files to the project directory."""

        # Create subdirectories
        instruments_subdir = project_dir / "instruments"
        instruments_subdir.mkdir(exist_ok=True)

        # Copy instrument files and their dependencies
        for role, instrument in selected_instruments.items():
            # Copy Python file
            dst_py = instruments_subdir / instrument.file_path.name
            shutil.copy2(instrument.file_path, dst_py)

            # Copy YAML file if it exists
            if instrument.yaml_path and instrument.yaml_path.exists():
                dst_yaml = instruments_subdir / instrument.yaml_path.name
                shutil.copy2(instrument.yaml_path, dst_yaml)
                print(
                    f"✓ Copied {instrument.file_path.name} + {instrument.yaml_path.name}"
                )
            else:
                print(f"✓ Copied {instrument.file_path.name} (no YAML found)")

        # Copy base classes and dependencies
        self._copy_instrument_dependencies(instruments_subdir, selected_instruments)

        # Copy measurement script
        measurement_script = (
            measurement_info.measurement_dir / f"{measurement_info.name}.py"
        )
        if measurement_script.exists():
            dst_script = project_dir / measurement_script.name
            shutil.copy2(measurement_script, dst_script)
            print(f"✓ Copied {measurement_script.name}")

        # Generate measurement parameters file
        self.generate_measurement_params(
            project_dir, selected_instruments, measurement_info
        )

    def generate_measurement_params(
        self,
        project_dir: Path,
        selected_instruments: Dict[str, InstrumentInfo],
        measurement_info: MeasurementInfo,
    ):
        """Generate the measurement parameters file from template."""

        template_path = (
            measurement_info.measurement_dir
            / f"{measurement_info.name}Params.template.py"
        )
        if not template_path.exists():
            # Create a basic template if none exists
            self.create_basic_template(
                project_dir, selected_instruments, measurement_info
            )
            return

        # Read template and substitute instrument information
        with open(template_path, "r") as f:
            template_content = f.read()

        # Prepare substitution variables
        substitutions = {"date": datetime.now().strftime("%B %d, %Y")}

        # Add instrument-specific substitutions for each role
        for role, instrument in selected_instruments.items():
            # Get the module name (without .py extension)
            module_name = instrument.file_path.stem
            class_name = instrument.class_name
            class_name_lower = class_name.lower()

            # Add substitutions for each instrument role
            substitutions[f"{role}_module"] = module_name
            substitutions[f"{role}_class"] = class_name
            substitutions[f"{role}_class_lower"] = class_name_lower

        # Perform substitution using double-brace template syntax
        try:
            filled_content = template_content
            for key, value in substitutions.items():
                filled_content = filled_content.replace(f"{{{{{key}}}}}", str(value))
        except Exception as e:
            print(
                f"Warning: Template substitution failed for {e}. Creating basic template."
            )
            self.create_basic_template(
                project_dir, selected_instruments, measurement_info
            )
            return

        # Write the filled template
        output_path = project_dir / f"{measurement_info.name}Params.py"
        with open(output_path, "w") as f:
            f.write(filled_content)

        print(f"✓ Generated {output_path.name}")
        print(
            f"📝 Edit {output_path.name} to configure measurement and instrument parameters"
        )

    def create_basic_template(
        self,
        project_dir: Path,
        selected_instruments: Dict[str, InstrumentInfo],
        measurement_info: MeasurementInfo,
    ):
        """Create a basic measurement parameters file."""

        content = f'''"""
Generated measurement parameters for {measurement_info.name}
"""

from dataclasses import dataclass
'''

        # Add imports for selected instruments
        for role, instrument in selected_instruments.items():
            content += f"from instruments.{instrument.file_path.stem} import {instrument.class_name}\n"

        content += f'''

@dataclass
class MeasurementConfig:
    """Configuration for {measurement_info.name} measurement"""
'''

        # Add instrument instances
        for role, instrument in selected_instruments.items():
            content += f"    {role}: {instrument.class_name} = None\n"

        content += '''
    def __post_init__(self):
        """Initialize instruments with their configurations"""
'''

        for role, instrument in selected_instruments.items():
            if instrument.yaml_path:
                content += f"        # Load {role} configuration from YAML\n"
                content += f"        self.{role} = {instrument.class_name}()\n"
            else:
                content += f"        self.{role} = {instrument.class_name}()\n"

        # Write the file
        output_path = project_dir / f"{measurement_info.name}Params.py"
        with open(output_path, "w") as f:
            f.write(content)

        print(f"✓ Generated {output_path.name}")

    def setup_measurement(self, measurement_name: str = None):
        """Main setup workflow."""
        print("🔬 SNSPD Measurement Setup Tool")
        print("=" * 40)

        # Discover available measurements
        measurements = self.discover_measurements()

        if not measurements:
            print("❌ No measurements found in the measurements directory.")
            return

        # Select measurement if not provided
        if measurement_name and measurement_name in measurements:
            selected_measurement = measurements[measurement_name]
        else:
            print("\nAvailable measurements:")
            measurement_list: list[tuple[str, MeasurementInfo]] = list(
                measurements.items()
            )
            for i, (name, info) in enumerate(measurement_list, 1):
                print(f"{i}. {name} - {info.description}")

            while True:
                try:
                    choice = (
                        int(
                            input(f"\nChoose measurement (1-{len(measurement_list)}): ")
                        )
                        - 1
                    )
                    if 0 <= choice < len(measurement_list):
                        break
                    print("Invalid choice, try again.")
                except (ValueError, KeyboardInterrupt):
                    print("Please enter a number or Ctrl+C to exit.")
                    return

            selected_measurement: MeasurementInfo = measurement_list[choice][1]

        print(f"\n📋 Setting up: {selected_measurement.name}")
        print(f"Description: {selected_measurement.description}")

        # Discover and select instruments
        selected_instruments = {}
        for role, base_class in selected_measurement.required_instruments.items():
            print(f"\n🔍 Discovering {role} instruments...")
            available = self.discover_instruments(self.instruments_dir, base_class)

            if not available:
                print(f"❌ No compatible {role} instruments found.")
                return

            selected_instruments[role] = self.select_instrument(role, available)

        # Create project directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = f"{selected_measurement.name}_{timestamp}"
        project_dir = self.projects_dir / project_name
        project_dir.mkdir(exist_ok=True)

        print(f"\n📁 Creating project directory: {project_dir}")

        self.combine_yaml_files(selected_measurement, selected_instruments, project_dir)

        # Copy files and generate config
        print("\n📄 Copying files...")
        self.copy_files_to_project(
            project_dir, selected_instruments, selected_measurement
        )

        print(f"\n✅ Measurement setup complete!")
        print(f"📁 Working directory: {project_dir}")
        print(f"\n🚀 You can now run your measurement from: {project_dir}")

        return project_dir

    def combine_yaml_files(
        self,
        selected_measurement: MeasurementInfo,
        selected_instruments: Dict[str, InstrumentInfo],
        project_dir: Path,
    ):
        """Combine measurement and instrument YAML files into a complete configuration."""

        # Load measurement YAML
        measurement_yaml_path = (
            selected_measurement.measurement_dir / f"{selected_measurement.name}.yml"
        )
        combined_config = {}

        if measurement_yaml_path.exists():
            with open(measurement_yaml_path, "r") as f:
                combined_config = yaml.safe_load(f) or {}

        # Add instruments section
        combined_config["instruments"] = {}

        # Track mainframes and their required sub-instruments
        mainframes = {}
        standalone_instruments = {}

        for role, instrument_info in selected_instruments.items():
            if instrument_info.yaml_path and instrument_info.yaml_path.exists():
                with open(instrument_info.yaml_path, "r") as f:
                    instrument_config = yaml.safe_load(f) or {}

                # Check if this is a SRS sub-instrument
                if (
                    instrument_info.class_name.startswith("SIM")
                    and instrument_info.class_name != "SIM900"
                ):
                    # This is a sub-instrument, add it to mainframe
                    mainframe_key = "sim900"

                    if mainframe_key not in mainframes:
                        # Initialize mainframe with base config
                        if "sim900" in instrument_config:
                            mainframes[mainframe_key] = instrument_config[
                                "sim900"
                            ].copy()
                            mainframes[mainframe_key]["sub-instruments"] = []
                        else:
                            # Default mainframe config if not found
                            mainframes[mainframe_key] = {
                                "port": "/dev/ttyUSB0",
                                "gpibAddr": 2,
                                "sub-instruments": [],
                            }

                    # Add this specific sub-instrument
                    sub_instrument_name = instrument_info.class_name.lower()
                    if sub_instrument_name in instrument_config:
                        sub_config = {
                            sub_instrument_name: instrument_config[sub_instrument_name]
                        }
                        mainframes[mainframe_key]["sub-instruments"].append(sub_config)
                    else:
                        print(
                            f"Warning: {sub_instrument_name} config not found in YAML"
                        )

                else:
                    # Standalone instrument (like Keysight counter)

                    for instrument_name, config in instrument_config.items():
                        # More flexible matching for instrument names
                        if (
                            instrument_name.lower()
                            == instrument_info.class_name.lower()
                            or instrument_name.lower().replace("_", "").replace("-", "")
                            == instrument_info.class_name.lower()
                            .replace("_", "")
                            .replace("-", "")
                        ):
                            standalone_instruments[instrument_name] = config
                            break
                    else:
                        # If no exact match found, try the first instrument in the YAML
                        if len(instrument_config) == 1:
                            instrument_name, config = next(
                                iter(instrument_config.items())
                            )
                            standalone_instruments[instrument_name] = config

        # Add mainframes to combined config
        for mainframe_name, mainframe_config in mainframes.items():
            combined_config["instruments"][mainframe_name] = mainframe_config

        # Add standalone instruments
        for instrument_name, config in standalone_instruments.items():
            combined_config["instruments"][instrument_name] = config

        # Save combined configuration
        output_path = project_dir / f"{selected_measurement.name}_complete.yml"
        with open(output_path, "w") as f:
            yaml.dump(combined_config, f, default_flow_style=False, indent=2)

        print(f"✓ Generated {output_path.name}")
        return output_path

    def _extract_instruments_from_template(
        self, template_file: Path
    ) -> Dict[str, Type[Any]]:
        """Extract required instrument types from template file by importing it as a module."""
        required_instruments = {}

        try:
            # Convert file path to module name, just like in discover_instruments()
            rel_path = template_file.relative_to(self.base_dir)
            module_name = str(rel_path.with_suffix("")).replace("/", ".")

            # Import the module
            module = importlib.import_module(module_name)

            # Find the Resources dataclass
            resources_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (
                    name.endswith("Resources")
                    and hasattr(obj, "__annotations__")
                    and obj.__module__ == module.__name__
                ):
                    resources_class = obj
                    break

            if not resources_class:
                print(f"Warning: No Resources class found in {template_file}")
                return required_instruments

            # Extract type hints from the dataclass
            for field_name, field_type in resources_class.__annotations__.items():
                # Skip non-instrument fields
                if field_name in ["saver", "plotter", "params"]:
                    continue

                required_instruments[field_name] = field_type

        except Exception as e:
            print(f"Warning: Failed to import template as module: {e}")

        return required_instruments

    def _copy_instrument_dependencies(
        self, target_dir: Path, selected_instruments: Dict[str, InstrumentInfo]
    ):
        """Copy base classes and dependencies for selected instruments."""
        copied_files = set()

        def copy_class_dependencies(class_obj: Type, file_path: Path):
            """Recursively copy dependencies for a class."""
            if file_path in copied_files:
                return

            # Get all base classes
            for base_class in inspect.getmro(class_obj)[1:]:  # Skip the class itself
                if base_class.__module__ == "builtins":
                    continue

                # Convert module name to file path
                module_parts = base_class.__module__.split(".")
                if module_parts[0] == "instruments":
                    # This is one of our instrument modules
                    base_file_path = self.instruments_dir
                    for part in module_parts[1:]:
                        base_file_path = base_file_path / part
                    base_file_path = base_file_path.with_suffix(".py")

                    if base_file_path.exists() and base_file_path not in copied_files:
                        # Create subdirectory structure if needed
                        rel_path = base_file_path.relative_to(self.instruments_dir)
                        target_file = target_dir / rel_path
                        target_file.parent.mkdir(parents=True, exist_ok=True)

                        shutil.copy2(base_file_path, target_file)
                        copied_files.add(base_file_path)
                        print(f"✓ Copied dependency {rel_path}")

                        # Recursively copy dependencies of this base class
                        try:
                            copy_class_dependencies(base_class, base_file_path)
                        except Exception:
                            pass  # Skip if we can't analyze this class

        # Copy dependencies for each selected instrument
        for instrument_info in selected_instruments.values():
            copy_class_dependencies(
                instrument_info.class_obj, instrument_info.file_path
            )

        # Also copy common __init__.py files
        for root, dirs, files in os.walk(self.instruments_dir):
            if "__init__.py" in files:
                init_file = Path(root) / "__init__.py"
                rel_path = init_file.relative_to(self.instruments_dir)
                target_file = target_dir / rel_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                if not target_file.exists():
                    shutil.copy2(init_file, target_file)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Setup SNSPD measurement experiments")
    parser.add_argument("measurement", nargs="?", help="Measurement type to setup")

    args = parser.parse_args()

    setup = MeasurementSetup()

    try:
        setup.setup_measurement(args.measurement)
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error during setup: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
