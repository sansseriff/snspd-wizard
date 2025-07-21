# SNSPD Measurement Library - AI Assistant Instructions

## Architecture Overview

This is a **scientific instrument control library** for Superconducting Nanowire Single-Photon Detectors (SNSPDs) at Caltech/JPL. The library follows a **plugin-based architecture** where:

- **Instruments** are abstract base classes (`VSource`, `VSense`, `Mainframe`) with concrete implementations
- **Measurements** combine multiple instruments to perform scientific experiments (IV curves, photon counting, etc.)
- **Configuration** is YAML-based with Pydantic validation for type safety
- **Projects** are auto-generated working directories with instrument configs and measurement scripts

## Key Architectural Patterns

### 1. Composition Over Inheritance

Instruments use **composition** for communication objects rather than inheritance.

Since only ABCs are inherited, you should NOT need to do things like

```python
super().__init__(...)
```

### 2. Abstract Base Classes with Type Safety

Instruments inherit from role-based ABCs:

```python
# lib/instruments/general/vsource.py - Abstract voltage source
# lib/instruments/general/vsense.py - Abstract sensing instrument
# lib/instruments/general/mainframe.py - Abstract module chassis
```

### 3. Configuration-Driven Instrument Discovery

- `config/instruments/*.yml` defines lab hardware configurations
- `setup_measurement.py` dynamically discovers compatible instruments via reflection
- Each instrument class has a `Config` Pydantic model for validation

### 4. Measurement as Resource Bundles

```python
@dataclass
class IVCurveResources:
    params: IVCurveParams
    voltage_source: VSource
    voltage_sense: VSense
```

## Critical Developer Workflows

### Setting Up New Measurements

```bash
# Interactive CLI for creating measurement projects
uv run python setup_measurement.py
```

This tool:

1. Scans `lib/measurements/` for available measurement types
2. Discovers compatible instruments in `lib/instruments/`
3. Creates timestamped project directory in `projects/`
4. Copies measurement templates and generates configs

### Running Measurements

Projects are self-contained with:

- `measurement.yml` - Instrument configuration
- `measurementParams.py` - Generated parameter class
- `measurement.py` - Executable measurement script

### Adding New Instruments

1. Inherit from appropriate ABC (`VSource`, `VSense`, `Mainframe`)
2. Create `Config` class using Pydantic
3. Add to `config/instruments/` directory
4. Follow the composition pattern with communication objects as internal components

## Project-Specific Conventions

### Module Structure

```
lib/
├── instruments/
│   ├── general/          # Abstract base classes
│   │   ├── visa_inst.py  # VISA communication base
│   │   └── vsource.py    # Voltage source ABC
│   └── keysight53220A.py # Concrete instrument
├── measurements/
│   └── ivCurve/          # Measurement type
│       ├── ivCurve.py    # Main measurement class
│       └── ivcurve_setup_template.py # Config template
└── utilities/
    └── model_spec.py     # Pydantic validation models
```

### YAML Configuration Pattern

Instruments use nested YAML configs with numeric slot addressing:

```yaml
# Project measurement.yml - Mainframe with modules
instruments:
  - type: Sim900
    port: /dev/ttyUSB0
    gpibAddr: 2
    modules:
      3: # slot number (numeric key)
        type: sim928
        offline: false
        settlingTime: 0.4
        attribute: vsource_1 # Links to measurement params
```

### Measurement-Instrument Linking

Measurements reference instruments by attribute names:

```yaml
measurement:
  ivCurve:
    voltage_source_1: vsource_1 # References instrument attribute
    voltage_source_2: vsource_2

instruments:
  - type: Sim900
    modules:
      3:
        attribute: vsource_1 # Matches measurement reference
```

### Error Handling Strategy

- Instruments have `offline` mode for development/testing
- Failed instrument discovery shows warnings but continues
- VISA connection failures are raised, not silently ignored

## Integration Points

### VISA Communication

- Uses `pyvisa` with `@py` backend (pure Python)
- TCP/IP SOCKET connections for network instruments
- Serial connections for legacy equipment

### Mainframe/Module Architecture

- `Mainframe` base class manages chassis with plug-in modules
- SIM900 (Stanford Research) and DBay systems supported
- Modules are addressable by slot number in YAML config

### Data Flow

1. `setup_measurement.py` → Project generation
2. Project `measurement.yml` → Instrument instantiation
3. Measurement script → Data collection
4. Results → Plotting/saving utilities

## Environment Setup

- Uses `uv` for dependency management
- Python 3.12+ required (uses modern type hints like `str | None`)
- Run with: `uv run python <script.py>`

## Common Pitfalls

- Don't inherit from communication classes - use composition with internal comm objects
- Abstract base classes are in `lib/instruments/general/`
- Config validation happens via Pydantic models, not manual checking
- Use `offline=True` for development without hardware
