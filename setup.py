# -*- coding: utf-8 -*-

# DO NOT EDIT THIS FILE!
# This file has been autogenerated by dephell <3
# https://github.com/dephell/dephell

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

readme = ""

setup(
    long_description=readme,
    name="wakethevote",
    version="0.1.0",
    python_requires="==3.*,>=3.6.0",
    author="14 Cities",
    author_email="info@14cities.org",
    entry_points={"console_scripts": ["wakevote = wakethevote.cli:main"]},
    packages=["wakethevote"],
    package_dir={"": "src"},
    package_data={},
    install_requires=[
        "folium==0.*,>=0.10.1",
        "geopandas==0.*,>=0.6.2",
        "pandas==0.*,>=0.25.3",
        "requests==2.*,>=2.22.0",
        "rtree==0.*,>=0.9.3",
    ],
    extras_require={"dev": ["pytest==5.*,>=5.2.0", "python-dotenv==0.*,>=0.10.3"]},
)
