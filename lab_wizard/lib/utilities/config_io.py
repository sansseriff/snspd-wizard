from __future__ import annotations

"""
Config I/O utilities for loading, merging, and saving the multi-file instruments config
into a single in-memory pydantic Params tree rooted at instruments (no ComputerParams).

Directory layout expected under a given config_dir:

config/
  instruments/
    prologix_gpib.yml
    dbay/
      dbay.yml
      modules/
        dac4D.yml
        dac16D.yml
    sim900/
      sim900.yml
      modules/
        sim928.yml
        sim970.yml
    keysight_whatever.yml

Notes:
- Parents express children as a list of refs with fields: kind, ref, key
- Leaf Params may carry an 'attribute' string to serve as a user-facing identifier

Provided functions:
- load_instruments(config_dir) -> dict[str, InstrumentParams]
- merge_parent_params(base, delta) -> base (mutated) for tree-union semantics
- merge_instruments(base_dict, delta_dict) -> merged dict (mutates base)
- save_instruments_to_config(instruments, config_dir) -> writes files back using stable paths
- load_merge_save_instruments(config_dir, subset_instruments) -> merged dict
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type, List, cast

from ruamel.yaml import YAML

# Import Params classes
from lib.instruments.general.prologix_gpib import PrologixGPIBParams
from lib.instruments.sim900.sim900 import Sim900Params
from lib.instruments.sim900.modules.sim928 import Sim928Params
from lib.instruments.sim900.modules.sim970 import Sim970Params
from lib.instruments.sim900.modules.sim921 import Sim921Params
from lib.instruments.dbay.dbay import DBayParams
from lib.instruments.dbay.modules.dac4d import Dac4DParams
from lib.instruments.dbay.modules.dac16d import Dac16DParams


# ---------------------------- YAML helpers ----------------------------

_yaml: Any = YAML(typ="safe")
_yaml.default_flow_style = False


def _read_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        loaded: Any = _yaml.load(f)
        return cast(Dict[str, Any], loaded or {})


def _write_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        _yaml.dump(data, f)


# ---------------------------- Type registry ----------------------------

@dataclass(frozen=True)
class TypeInfo:
    params_cls: Type[Any]
    folder: Optional[str]  # subfolder under instruments for parent types


TYPE_REGISTRY: Dict[str, TypeInfo] = {
    # top-level instruments
    "prologix_gpib": TypeInfo(PrologixGPIBParams, None),
    "dbay": TypeInfo(DBayParams, "dbay"),
    "sim900": TypeInfo(Sim900Params, "sim900"),
    # sim900 modules
    "sim928": TypeInfo(Sim928Params, "sim900/modules"),
    "sim970": TypeInfo(Sim970Params, "sim900/modules"),
    "sim921": TypeInfo(Sim921Params, "sim900/modules"),
    # dbay modules
    "dac4D": TypeInfo(Dac4DParams, "dbay/modules"),
    "dac16D": TypeInfo(Dac16DParams, "dbay/modules"),
}


def _params_from_dict(type_str: str, data: Dict[str, Any]) -> Any:
    info = TYPE_REGISTRY.get(type_str)
    if info is None:
        raise ValueError(f"Unknown instrument type '{type_str}' in config")
    return info.params_cls(**data)


# ---------------------------- Loading ----------------------------

def _resolve_child_file(base_dir: Path, ref: str) -> Path:
    # ref is relative to instruments dir
    return (base_dir / "instruments" / ref).resolve()


def _load_node(base_dir: Path, node_path: Path) -> Tuple[Any, Dict[str, Any]]:
    """Load a node YAML file and return (Params instance, raw dict). Does not load children yet."""
    data = _read_yaml(node_path)
    type_str = data.get("type")
    if not isinstance(type_str, str):
        raise ValueError(f"Missing/invalid 'type' in {node_path}")
    # Copy without children for instantiation; children processed separately
    shallow = {k: v for k, v in data.items() if k != "children"}
    params = _params_from_dict(type_str, shallow)
    return params, data


def _attach_children(base_dir: Path, parent_params: Any, raw_dict: Dict[str, Any]) -> None:
    children: List[Dict[str, Any]] = cast(List[Dict[str, Any]], raw_dict.get("children") or [])
    if not children:
        return
    for entry in children:
        kind = cast(Optional[str], entry.get("kind"))
        ref = cast(Optional[str], entry.get("ref"))
        key = cast(Optional[str], entry.get("key"))
        if not (isinstance(kind, str) and isinstance(ref, str) and isinstance(key, str)):
            raise ValueError("child entry requires string fields: kind, ref, key")
        child_path = _resolve_child_file(base_dir, ref)
        child_params, child_raw = _load_node(base_dir, child_path)

        if getattr(child_params, "enabled", True) is False:
            continue

        # recursively attach grandchildren
        _attach_children(base_dir, child_params, child_raw)
        # add to parent
        if not hasattr(parent_params, "children"):
            raise ValueError(f"Parent type {type(parent_params).__name__} has no children field")
        parent_params.children[key] = child_params  # type: ignore[attr-defined]


def load_instruments(config_dir: str | Path) -> Dict[str, Any]:
    """Load the instruments config into a top-level instruments dict mapping keys to Params.

    Heuristic: Any top-level instrument YAML directly under instruments/ is considered a top-level entry.
    Its key is inferred as:
      - prologix_gpib: params.port
      - dbay: f"{server_address}:{port}" (port optional if default)
      - sim900: key must be provided by a parent (not typical at top-level)
      - other leaf instruments: use an attribute or fallback to type name
    """
    base_dir = Path(config_dir)
    inst_dir = (base_dir / "instruments").resolve()
    instruments: Dict[str, Any] = {}

    if not inst_dir.exists():
        return instruments

    # Top-level files (exclude known folders)
    for p in sorted(inst_dir.glob("*.yml")):
        params, raw = _load_node(base_dir, p)

        if getattr(params, "enabled", True) is False:
            continue

        _attach_children(base_dir, params, raw)
        type_str = str(raw.get("type") or "")
        if type_str == "prologix_gpib":
            key = getattr(params, "port", None) or "<unknown>"
        elif type_str == "dbay":
            host = getattr(params, "server_address", None) or "localhost"
            port = getattr(params, "port", 8345)
            key = f"{host}:{port}"
        else:
            # Generic fallback using type
            key = type_str
        instruments[key] = params

    # Known parent folders
    for folder, filename in [("dbay", "dbay.yml"), ("sim900", "sim900.yml")]:
        folder_path = inst_dir / folder / filename
        if folder_path.exists():
            params, raw = _load_node(base_dir, folder_path)

            if getattr(params, "enabled", True) is False:
                continue

            _attach_children(base_dir, params, raw)
            type_name = str(raw.get("type") or "")
            if type_name == "dbay":
                host = getattr(params, "server_address", None) or "localhost"
                port = getattr(params, "port", 8345)
                key = f"{host}:{port}"
            elif type_name == "sim900":
                # sim900 at top-level has no natural dict key; default to "sim900"
                key = "sim900"
            else:
                key = type_name or folder
            instruments[key] = params

    return instruments


# ---------------------------- Merging ----------------------------

def merge_parent_params(base_parent: Any, delta_parent: Any) -> Any:
    """Merge delta_parent into base_parent in-place, unioning children by key.

    - For simple fields present in delta (excluding children), overwrite base fields.
    - For children dicts, recursively merge when both are parents; otherwise replace child.
    """
    # Merge simple fields
    for name in getattr(base_parent, "model_fields", {}).keys():  # pydantic v2
        if name == "children":
            continue
        if hasattr(delta_parent, name):
            setattr(base_parent, name, getattr(delta_parent, name))

    # Merge children
    base_children: Dict[str, Any] = getattr(base_parent, "children", {})
    delta_children: Dict[str, Any] = getattr(delta_parent, "children", {})
    for key, dchild in (delta_children or {}).items():
        if key not in base_children:
            base_children[key] = dchild
            continue
        bchild = base_children[key]
        # If both have children attribute, treat as parent and merge recursively
        if hasattr(bchild, "children") and hasattr(dchild, "children"):
            merge_parent_params(bchild, dchild)
        else:
            base_children[key] = dchild
    # write back possibly new dict
    if hasattr(base_parent, "children"):
        base_parent.children = base_children  # type: ignore[attr-defined]
    return base_parent


# ---------------------------- Saving ----------------------------

def _choose_node_path(inst_dir: Path, type_str: str, parent_type: Optional[str], key: Optional[str], attribute: Optional[str]) -> Path:
    """Compute target YAML path for a node based on type and context."""
    info = TYPE_REGISTRY.get(type_str)
    if info is None:
        # unknown types directly under instruments
        name = f"{type_str}.yml"
        return inst_dir / name
    sub = info.folder
    # Filename preference: use attribute if provided, else type+key
    base_name = None
    if attribute:
        base_name = f"{type_str}_{attribute}.yml"
    elif key:
        # For modules in a rack/mainframe (known via info.folder), append _SlotX for clarity
        if sub and ("sim900" in sub or "dbay" in sub) and key.isdigit():
            base_name = f"{type_str}_Slot{key}.yml"
        else:
            base_name = f"{type_str}_{key}.yml"
    else:
        base_name = f"{type_str}.yml"
    if sub:
        return inst_dir / sub / base_name
    else:
        # top-level instrument
        # Special-case: standard filenames for known parents
        if type_str == "prologix_gpib":
            return inst_dir / "prologix_gpib.yml"
        if type_str == "dbay":
            return inst_dir / "dbay" / "dbay.yml"
        if type_str == "sim900":
            return inst_dir / "sim900" / "sim900.yml"
        return inst_dir / base_name


def _dump_parent_to_dict(params: Any, child_refs: List[Dict[str, str]]) -> Dict[str, Any]:
    data: Dict[str, Any] = params.model_dump()
    # Persist children as refs list, not embedded dict
    data.pop("children", None)
    if data.get("enabled") is True:
        data.pop("enabled")
    if child_refs:
        data["children"] = child_refs
    return data


def _save_node_recursive(inst_dir: Path, params: Any, parent_type: Optional[str], here_key: Optional[str]) -> Tuple[Path, Dict[str, Any]]:
    type_str: str = getattr(params, "type")  # pydantic field
    attribute: Optional[str] = getattr(params, "attribute", None)

    # First save children to obtain their file refs
    child_refs: List[Dict[str, str]] = []
    for key, child in (getattr(params, "children", {}) or {}).items():
        c_type = getattr(child, "type")
        c_path, _ = _save_node_recursive(inst_dir, child, type_str, key)
        ref = c_path.relative_to(inst_dir).as_posix()
        # Normalize into ref under instruments/
        if not ref.startswith("sim900/") and not ref.startswith("dbay/"):
            # keep as is for top-level leafs
            pass
        child_refs.append({"kind": str(c_type), "ref": ref, "key": str(key)})

    # Now write this node
    target = _choose_node_path(inst_dir, type_str, parent_type, here_key, attribute)
    data = _dump_parent_to_dict(params, child_refs)
    _write_yaml(target, data)
    return target, data


def save_instruments_to_config(instruments: Dict[str, Any], config_dir: str | Path) -> None:
    """Write the given instruments dict into config/instruments as multi-file YAML.

    Overwrites files deterministically based on type/key/attribute naming.
    """
    base_dir = Path(config_dir)
    inst_dir = (base_dir / "instruments").resolve()
    # Write each top-level instrument
    for key, child in (instruments or {}).items():
        _save_node_recursive(inst_dir, child, parent_type=None, here_key=str(key))


# ---------------------------- High-level workflows ----------------------------

def merge_instruments(base: Dict[str, Any], delta: Dict[str, Any]) -> Dict[str, Any]:
    """Merge delta instruments dict into base dict (in place)."""
    for key, dval in (delta or {}).items():
        if key not in base:
            base[key] = dval
            continue
        bval = base[key]
        # If both look like parents (have children), deep-merge
        if hasattr(bval, "children") and hasattr(dval, "children"):
            merge_parent_params(bval, dval)
        else:
            base[key] = dval
    return base


def load_merge_save_instruments(config_dir: str | Path, subset: Dict[str, Any]) -> Dict[str, Any]:
    """Load current instruments, merge the provided subset dict, and persist the result.

    Returns the merged instruments dict.
    """
    full = load_instruments(config_dir)
    merged = merge_instruments(full, subset)
    save_instruments_to_config(merged, config_dir)
    return merged


