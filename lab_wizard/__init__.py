# Root package marker for snspd_measure
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("lab-wizard")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "0.0.1"

__all__ = ["__version__"]
