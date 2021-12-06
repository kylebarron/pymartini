"""Setup for pymartini."""
from pathlib import Path

import numpy as np

# setuptools must be before Cython
from setuptools import find_packages, setup

from Cython.Build import cythonize  # isort: skip

with open("README.md") as f:
    readme = f.read()

# Runtime requirements.
inst_reqs = ["numpy"]

extra_reqs = {
    "test": ["pytest", "pytest-benchmark", "imageio"],
    "build": ["numpy", "Cython"],
}


# Ref https://suzyahyah.github.io/cython/programming/2018/12/01/Gotchas-in-Cython.html
def find_pyx(path='.'):
    return list(map(str, Path(path).glob('**/*.pyx')))


setup(
    name="pymartini",
    version="0.4.3",
    python_requires=">=3.6",
    description="A Python port of Martini for fast terrain mesh generation",
    long_description=readme,
    long_description_content_type="text/markdown",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Scientific/Engineering :: GIS",
    ],
    keywords="mesh heightmap elevation terrain numpy",
    author="Kyle Barron",
    author_email="kylebarron2@gmail.com",
    url="https://github.com/kylebarron/pymartini",
    license="MIT",
    packages=find_packages(exclude=["ez_setup", "scripts", "examples", "test"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
    ext_modules=cythonize(find_pyx(), language_level=3),
    # Include Numpy headers
    include_dirs=[np.get_include()],
)
