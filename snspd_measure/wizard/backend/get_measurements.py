from typing import Dict, Any, List, Optional
from pathlib import Path
import importlib
import inspect
import sys

from models import MeasurementInfo, Env


def _extract_instruments_from_template(env: Env, template_file: Path) -> Dict[str, Any]:
    """Extract required instrument types from template file by importing it as a module."""
    required_instruments: Dict[str, Any] = {}

    try:
        # Convert file path to module name, just like in discover_instruments()
        rel_path = template_file.relative_to(env.base_dir)
        module_name = str(rel_path.with_suffix(""))
        module_name = module_name.replace("/", ".")

        # Ensure base_dir is on sys.path for import to succeed
        base_dir_str = str(env.base_dir)
        if base_dir_str not in sys.path:
            sys.path.insert(0, base_dir_str)

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


def _template_file_for(measurement_dir: Path) -> Path:
    """Return the expected setup template file path for a measurement dir."""
    return measurement_dir / f"{measurement_dir.name}_setup_template.py"


def _find_lib_base(start: Path) -> Optional[Path]:
    """Walk up from start to locate the 'lib' package root used for imports."""
    for parent in [start] + list(start.parents):
        if parent.name == "lib" and (parent / "__init__.py").exists():
            return parent
    return None


def reqs_from_measurement(measurement: MeasurementInfo) -> List[str]:
    """Return a list of required instrument role names for a measurement."""
    measurement_dir = measurement.measurement_dir
    template_file = _template_file_for(measurement_dir)

    if not template_file.exists():
        return []

    lib_base = _find_lib_base(template_file.parent)
    if lib_base is None:
        return []

    env = Env(base_dir=lib_base)
    required = _extract_instruments_from_template(env, template_file)
    return list(required.keys())


def get_measurements(env: Env) -> Dict[str, MeasurementInfo]:
    """Discover available measurement types."""
    measurements: Dict[str, MeasurementInfo] = {}

    for measurement_dir in env.measurements_dir.iterdir():
        if not measurement_dir.is_dir() or measurement_dir.name.startswith("__"):
            continue

        # Look for the main measurement file
        measurement_file = measurement_dir / f"{measurement_dir.name}.py"
        if not measurement_file.exists():
            continue

        # Look for the template file to analyze required instruments
        template_file = _template_file_for(measurement_dir)

        try:
            description = f"{measurement_dir.name} measurement"

            if template_file.exists():
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
                measurement_dir=measurement_dir,
            )

        except Exception as e:
            print(f"Warning: Could not parse {measurement_dir.name}: {e}")
            continue

    return measurements