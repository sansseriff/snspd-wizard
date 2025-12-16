import pathlib

from lab_wizard.lib.utilities.config_io import (
    load_instruments,
    save_instruments_to_config,
)
from lab_wizard.lib.instruments.dbay.dbay import DBayParams


def _write(p: pathlib.Path, data: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(data, encoding="utf-8")


def test_orphan_module_preservation(tmp_path: pathlib.Path):
    """
    Test that a module file that exists on disk but is not referenced by any parent
    (orphaned/inactive) is NOT loaded into memory, but is ALSO NOT deleted when
    saving the configuration back to disk.
    """
    cfg = tmp_path / "config"
    inst_dir = cfg / "instruments"
    
    # 1. Setup a DBay with one active child (dac4D)
    _write(inst_dir / "dbay" / "dbay.yml", """
type: dbay
server_address: 10.7.0.4
port: 8345
children:
  "1":
    kind: dac4D
    ref: dbay/modules/active_dac4d.yml
""")
    
    _write(inst_dir / "dbay" / "modules" / "active_dac4d.yml", """
type: dac4D
name: ActiveDAC
num_channels: 4
""")

    # 2. Create an ORPHANED module file (not referenced in dbay.yml)
    orphan_path = inst_dir / "dbay" / "modules" / "orphan_dac16d.yml"
    _write(orphan_path, """
type: dac16D
name: OrphanDAC
num_channels: 16
""")

    # 3. Load instruments
    instruments = load_instruments(cfg)
    
    # Verify loaded structure
    dbay_key = "10.7.0.4:8345"
    assert dbay_key in instruments
    dbay = instruments[dbay_key]
    assert isinstance(dbay, DBayParams)
    
    # Active child should be present
    assert "1" in dbay.children
    assert dbay.children["1"].name == "ActiveDAC"
    
    # Orphan should NOT be in the in-memory children
    # (The key for dac16d would be unknown since it's not in the parent's map, 
    # but we can verify the count)
    assert len(dbay.children) == 1

    # 4. Save instruments back to disk
    save_instruments_to_config(instruments, cfg)

    # 5. Verify Orphan file STILL EXISTS
    assert orphan_path.exists(), "Orphaned module file should not be deleted during save"
    
    # Verify Active file still exists
    assert (inst_dir / "dbay" / "modules" / "active_dac4d.yml").exists()


def test_enabled_flag(tmp_path: pathlib.Path):
    """
    Test that 'enabled: false' prevents loading of instruments/modules.
    """
    cfg = tmp_path / "config"
    inst_dir = cfg / "instruments"

    # 1. Setup Prologix (Enabled) -> Sim900 (Enabled) -> Sim928 (Disabled)
    _write(inst_dir / "prologix.yml", """
type: prologix_gpib
port: /dev/ttyUSB0
enabled: true
children:
  "5":
    kind: sim900
    ref: sim900/sim900.yml
""")
    
    _write(inst_dir / "sim900" / "sim900.yml", """
type: sim900
children:
  "1":
    kind: sim928
    ref: sim900/modules/sim928.yml
""")

    _write(inst_dir / "sim900" / "modules" / "sim928.yml", """
type: sim928
enabled: false
""")

    # 2. Setup a DISABLED top-level instrument
    _write(inst_dir / "disabled_dbay.yml", """
type: dbay
server_address: 1.2.3.4
enabled: false
""")

    # 3. Load
    instruments = load_instruments(cfg)

    # Prologix should be loaded
    assert "/dev/ttyUSB0" in instruments
    prologix = instruments["/dev/ttyUSB0"]
    
    # Sim900 should be loaded (as child of prologix)
    assert "5" in prologix.children
    sim900 = prologix.children["5"]
    
    # Sim928 should NOT be loaded (enabled: false)
    assert "1" not in sim900.children

    # Disabled DBay should NOT be loaded
    # (Key would be 1.2.3.4:8345)
    assert "1.2.3.4:8345" not in instruments

    # Check that enabled ones ARE present
    assert "/dev/ttyUSB0" in instruments

    # 4. Save and Verify 'enabled: false' is preserved (or file untouched)
    save_instruments_to_config(instruments, cfg)
    
    # Check that the disabled module file still says enabled: false
    # Note: save_instruments_to_config only writes files for nodes in the tree.
    # Since Sim928 was not loaded, it is not in the tree, so it won't be re-written.
    # So the file should remain as is.
    content = (inst_dir / "sim900" / "modules" / "sim928.yml").read_text()
    assert "enabled: false" in content


if __name__ == "__main__":
    # Manual run helper
    test_orphan_module_preservation(pathlib.Path("test_output"))
    test_enabled_flag(pathlib.Path("test_output"))
    print("Tests passed!")
