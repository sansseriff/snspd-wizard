from __future__ import annotations

"""
Config I/O utilities for loading, merging, and saving the multi-file instruments config
into a single in-memory pydantic Params tree rooted at instruments (no ComputerParams).

Directory layout expected under a given config_dir (illustrative):

config/
  instruments/
    prologix_gpib_key_<slug(port)>.yml
    dbay/
      dbay_key_<slug(server_address:port)>.yml
      modules/
        dac4D_key_<slot>.yml
        dac16D_key_<slot>.yml
    sim900/
      sim900_key_<gpib_addr>.yml        # SIM900 mainframes, as children of Prologix
      modules/
        sim928_key_<slot>.yml
        sim970_key_<slot>.yml
        sim921_key_<slot>.yml
    keysight_whatever_key_<something>.yml

Notes:
- Parents express children as a mapping from string keys (e.g. slot index, GPIB
  address) to refs with fields: kind, ref.
- Leaf Params may carry an 'attribute' string to serve as a user-facing identifier.

Provided functions:
- load_instruments(config_dir) -> dict[str, InstrumentParams]
- merge_parent_params(base, delta) -> base (mutated) for tree-union semantics
- merge_instruments(base_dict, delta_dict) -> merged dict (mutates base)
- save_instruments_to_config(instruments, config_dir) -> writes files back using stable paths
- load_merge_save_instruments(config_dir, subset_instruments) -> merged dict
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any,Dict,Optional,Tuple,Type,List,cast

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

# Import Params classes
from lab_wizard.lib.instruments.general.prologix_gpib import PrologixGPIBParams
from lab_wizard.lib.instruments.sim900.sim900 import Sim900Params
from lab_wizard.lib.instruments.sim900.modules.sim928 import Sim928Params
from lab_wizard.lib.instruments.sim900.modules.sim970 import Sim970Params
from lab_wizard.lib.instruments.sim900.modules.sim921 import Sim921Params
from lab_wizard.lib.instruments.dbay.dbay import DBayParams
from lab_wizard.lib.instruments.dbay.modules.dac4d import Dac4DParams
from lab_wizard.lib.instruments.dbay.modules.dac16d import Dac16DParams


# ---------------------------- YAML helpers ----------------------------

# Use round-trip mode so we can preserve and add helpful comments in the
# on-disk config tree, while still converting to plain dicts before
# instantiating Pydantic models.
_yaml: Any = YAML(typ="rt")
_yaml.default_flow_style = False


def _read_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        loaded: Any = _yaml.load(f)
        return cast(Dict[str, Any], loaded or {})


def _write_yaml(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # Convert plain dicts into a CommentedMap so we can attach comments such
    # as "managed by wizard" to specific keys (e.g. child refs).
    if not isinstance(data, CommentedMap):
        cm = CommentedMap()
        for k, v in data.items():
            cm[k] = v
        data_to_dump: Any = cm
    else:
        data_to_dump = data
    with path.open("w", encoding="utf-8") as f:
        _yaml.dump(data_to_dump, f)


# ---------------------------- Key slug helpers ----------------------------

SLUG_ESCAPE_PREFIX = "~"


def key_to_slug(key: str) -> str:
    """Convert an arbitrary key string into a filesystem-safe slug.

    - Alphanumeric characters and '-','_' are left as-is.
    - All other characters are encoded as '~HH' where HH is the hex code of the
      character's ordinal. This is reversible via slug_to_key.
    """

    pieces: List[str] = []
    for ch in key:
        if ch.isalnum() or ch in "-_":
            pieces.append(ch)
        else:
            pieces.append(f"{SLUG_ESCAPE_PREFIX}{ord(ch):02X}")
    return "".join(pieces)


def slug_to_key(slug: str) -> str:
    """Inverse of key_to_slug.

    Not currently used by the loader (we keep original keys in YAML), but
    available for tools that need to map filenames back to dictionary keys.
    """

    out: List[str] = []
    i = 0
    n = len(slug)
    while i < n:
        ch = slug[i]
        if ch == SLUG_ESCAPE_PREFIX and i + 2 < n:
            hex_part = slug[i + 1 : i + 3]
            try:
                code = int(hex_part, 16)
            except ValueError:
                # Not a valid escape, keep literal
                out.append(ch)
                i += 1
                continue
            out.append(chr(code))
            i += 3
        else:
            out.append(ch)
            i += 1
    return "".join(out)


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


def _load_node(
    base_dir: Path,
    node_path: Path,
    visited_paths: Optional[set[Path]] = None,
) -> Tuple[Any, Dict[str, Any]]:
    """Load a node YAML file and return (Params instance, raw dict).

    Does not load children yet. When visited_paths is provided, the resolved
    node_path is added to that set so callers can reconstruct the set of all
    YAML files that participate in the logical instruments tree.
    """
    if visited_paths is not None:
        visited_paths.add(node_path.resolve())
    data = _read_yaml(node_path)
    type_str = data.get("type")
    if not isinstance(type_str, str):
        raise ValueError(f"Missing/invalid 'type' in {node_path}")
    # Copy without children for instantiation; children processed separately
    shallow = {k: v for k, v in data.items() if k != "children"}
    params = _params_from_dict(type_str, shallow)
    return params, data


def _attach_children(
    base_dir: Path,
    parent_params: Any,
    raw_dict: Dict[str, Any],
    visited_paths: Optional[set[Path]] = None,
) -> None:
    # Children are represented in YAML as a mapping: key -> {kind, ref}
    children_map: Dict[str, Dict[str, Any]] = cast(
        Dict[str, Dict[str, Any]], raw_dict.get("children") or {}
    )
    if not children_map:
        return
    for key, entry in list(children_map.items()):
        kind = cast(Optional[str], entry.get("kind"))
        ref = cast(Optional[str], entry.get("ref"))
        if not (isinstance(kind, str) and isinstance(ref, str)):
            raise ValueError("child entry requires string fields: kind, ref, and mapping key")
        child_path = _resolve_child_file(base_dir, ref)
        child_params, child_raw = _load_node(base_dir, child_path, visited_paths)

        if getattr(child_params, "enabled", True) is False:
            continue

        # recursively attach grandchildren
        _attach_children(base_dir, child_params, child_raw, visited_paths)
        # add to parent
        if not hasattr(parent_params, "children"):
            raise ValueError(f"Parent type {type(parent_params).__name__} has no children field")
        parent_params.children[key] = child_params  # type: ignore[attr-defined]


def load_instruments(
    config_dir: str | Path,
    visited_paths: Optional[set[Path]] = None,
) -> Dict[str, Any]:
    """Load the instruments config into a top-level instruments dict mapping keys to Params.

    Heuristic: Any top-level instrument YAML directly under instruments/ is considered a top-level entry.
    Its key is inferred as:
      - prologix_gpib: params.port
      - dbay: f"{server_address}:{port}" (port optional if default)
      - sim900: loaded only as a child of PrologixGPIB (not a top-level instrument)
      - other leaf instruments: use an attribute or fallback to type name
    """
    base_dir = Path(config_dir)
    inst_dir = (base_dir / "instruments").resolve()
    instruments: Dict[str, Any] = {}

    if not inst_dir.exists():
        return instruments

    # Top-level files (exclude known folders)
    for p in sorted(inst_dir.glob("*.yml")):
        params, raw = _load_node(base_dir, p, visited_paths)
        print()
        print("XXXXXXXX params in load_instruments", params)
        print("YYYY raw in load_instruments", raw)
        print()

        if getattr(params, "enabled", True) is False:
            continue

        _attach_children(base_dir, params, raw, visited_paths)
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

    # Known parent folders (DBay). Rather than relying on hard-coded
    # filenames like "dbay.yml", scan all YAML files under
    # these folders and use their internal "type" field to decide how to key
    # them in the top-level instruments dict.
    for folder in ("dbay",):
        folder_dir = inst_dir / folder
        if not folder_dir.exists():
            continue
        for p in sorted(folder_dir.glob("*.yml")):
            params, raw = _load_node(base_dir, p, visited_paths)

            if getattr(params, "enabled", True) is False:
                continue

            _attach_children(base_dir, params, raw, visited_paths)
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


def load_instruments_with_paths(
    config_dir: str | Path,
) -> Tuple[Dict[str, Any], set[Path]]:
    """Load instruments and also return the set of YAML files that participated.

    This is useful for normalization / cleanup tooling that wants to know which
    files are reachable from the logical instruments tree.
    """

    visited: set[Path] = set()
    instruments = load_instruments(config_dir, visited_paths=visited)
    return instruments, visited


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
        # General rule: encode dictionary key into a filesystem-safe slug and
        # include it in the filename so the config tree looks dictionary-like.
        slug = key_to_slug(str(key))
        base_name = f"{type_str}_key_{slug}.yml"
    else:
        base_name = f"{type_str}.yml"
    if sub:
        # Parent/child types with a dedicated subfolder (e.g. dbay, sim900 and
        # their modules) live under that folder.
        return inst_dir / sub / base_name
    else:
        # Top-level instruments live directly under instruments/ using the
        # same {type}_key_{slug(key)}.yml convention (when a key is present).
        return inst_dir / base_name


def _dump_parent_to_dict(params: Any, child_refs: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
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
    # Children are represented as a mapping from string key to {kind, ref}.
    child_refs: Dict[str, Dict[str, str]] = {}
    for key, child in (getattr(params, "children", {}) or {}).items():
        c_type = getattr(child, "type")
        c_path, _ = _save_node_recursive(inst_dir, child, type_str, key)
        ref = c_path.relative_to(inst_dir).as_posix()
        # NOTE: 'ref' is code-owned: humans should not edit it. It always
        # reflects the canonical path of the child under config/instruments.
        child_refs[str(key)] = {"kind": str(c_type), "ref": ref}

    # Now write this node
    target = _choose_node_path(inst_dir, type_str, parent_type, here_key, attribute)
    data = _dump_parent_to_dict(params, child_refs)

    # Attach a helpful comment to the "ref" field if we are in round-trip mode.
    # We construct a CommentedMap in _write_yaml, but here we can hint by using
    # CommentedMap directly so we can control comments for children.
    cm = CommentedMap()
    for k, v in data.items():
        cm[k] = v
    # Add comments on each child's ref entry to warn humans not to edit it.
    children_raw: Any = cm.get("children", None)  # type: ignore[call-arg]
    if isinstance(children_raw, dict):
        for yaml_key, entry in cast(Dict[Any, Any], children_raw).items():
            if not isinstance(entry, CommentedMap) and isinstance(entry, dict):
                tmp_cm: CommentedMap = CommentedMap()
                for ck, cv in cast(dict[Any, Any], entry).items():
                    tmp_cm[ck] = cv
                cast(Dict[Any, Any], children_raw)[yaml_key] = tmp_cm
                entry = tmp_cm
            if isinstance(entry, CommentedMap):
                # Add a warning comment around the ref field to signal that it
                # is owned by the wizard and will be updated automatically.
                entry.yaml_set_comment_before_after_key(  # type: ignore[no-untyped-call]
                    "ref",
                    before=" DO NOT EDIT: managed by wizard; path may be renamed automatically.",
                )

    _write_yaml(target, cm)
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


# ---------------------------- Normalization ----------------------------

def _iter_instrument_yaml_files(config_dir: Path) -> List[Path]:
    """Return a list of all YAML files under config/instruments.

    Used by normalization tooling to detect orphaned files.
    """

    inst_dir = (config_dir / "instruments").resolve()
    if not inst_dir.exists():
        return []
    return sorted(inst_dir.rglob("*.yml"))


def normalize_instruments(config_dir: str | Path) -> Dict[str, Any]:
    """Normalize the instruments config tree.

    Operations:
    - Load the current instruments tree.
    - Re-save using canonical filenames (type + key slug) and auto-managed refs.
    - Remove any orphaned YAML files in config/instruments that are no longer
      referenced by the current tree (best-effort).
    """

    base_dir = Path(config_dir)

    # Step 1: Load and immediately re-save; filenames and refs are canonicalized
    # by _choose_node_path and _save_node_recursive.
    instruments = load_instruments(config_dir)
    save_instruments_to_config(instruments, config_dir)

    # Step 2: Re-load and compute the closure of all YAML files reachable from
    # the logical instruments tree (top-level + children via refs).
    _, reachable_paths = load_instruments_with_paths(config_dir)

    # Step 3: Any YAML file under instruments/ that is not reachable is treated
    # as an orphan (e.g. leftovers from type/key renames) and can be removed.
    all_files = set(_iter_instrument_yaml_files(base_dir))
    orphans = all_files - reachable_paths
    for orphan in orphans:
        try:
            orphan.unlink()
        except OSError:
            # Best-effort cleanup; ignore failures (permissions, races, etc.).
            pass

    return instruments
