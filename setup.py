"""Setup for pymartini."""

from setuptools import find_packages, setup

with open("README.md") as f:
    readme = f.read()

# Runtime requirements.
inst_reqs = ["numpy"]

extra_reqs = {
    "test": ["pytest", "pytest-benchmark", "imageio"],
}

setup(
    name="pymartini",
    version="0.1.0",
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
        "Topic :: Scientific/Engineering :: GIS"],
    keywords="mesh heightmap elevation terrain numpy",
    author="Kyle Barron",
    author_email="kylebarron2@gmail.com",
    url="https://github.com/kylebarron/pymartini",
    license="MIT",
    packages=find_packages(
        exclude=["ez_setup", "scripts", "examples", "test"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=inst_reqs,
    extras_require=extra_reqs,
)
