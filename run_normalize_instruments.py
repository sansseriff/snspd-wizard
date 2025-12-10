from pathlib import Path

from lab_wizard.lib.utilities.config_io import normalize_instruments


def main() -> None:
    # Use the lab_wizard/config directory as the base config dir, which is
    # expected to contain an "instruments" subfolder.
    base_dir = Path(__file__).parent / "lab_wizard" / "config"
    print(f"Normalizing instruments under: {base_dir}")
    instruments = normalize_instruments(base_dir)
    print(f"Normalized {len(instruments)} top-level instrument(s).")


if __name__ == "__main__":
    main()



