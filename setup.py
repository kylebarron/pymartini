# Project metadata lives in pyproject.toml. This file only declares the Cython
# extension, which setuptools can't yet configure from pyproject.toml alone.
import numpy as np
from Cython.Build import cythonize
from setuptools import setup

setup(
    ext_modules=cythonize("pymartini/*.pyx", language_level=3),
    # Include Numpy headers
    include_dirs=[np.get_include()],
)
