"""Top-level package for pymartini."""

from importlib.metadata import PackageNotFoundError, version

from .martini import Martini
from .util import decode_ele, rescale_positions

__author__ = """Kyle Barron"""
__email__ = "kylebarron2@gmail.com"

try:
    __version__ = version("pymartini")
except PackageNotFoundError:
    __version__ = "uninstalled"

__all__ = ["Martini", "__version__", "decode_ele", "rescale_positions"]
