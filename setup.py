"""
Setup script for cv-intelligence package.
This file is provided for compatibility with older build systems.
The main configuration is in pyproject.toml.
"""
from setuptools import setup, find_packages

setup(
    name="cv-intelligence",
    version="0.1.0",
    packages=find_packages(where="demo", include=["src*"]),
    package_dir={"": "demo"},
    python_requires=">=3.10",
)
