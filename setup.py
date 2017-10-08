# -*- coding: utf-8 -*-

"""Vaayu - Python Library for Wind Energy Applications
"""

from setuptools import setup

VERSION = "0.0.1"

classifiers = [
    "Development Status :: 3 -Alpha",
    "License :: OSI Approved :: Apache Software License",
    "Operating System :: POSIX",
    "Operating System :: POSIX :: Linux",
    "Operating System :: MacOS :: MacOS X",
    "Operating System :: Microsoft :: Windows",
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: Implementation :: CPython",
    "Topic :: Scientific/Engineering :: Physics"
    "Topic :: Scientific/Engineering :: Visualization",
    "Topic :: Utilities",
]

setup(
    name="vaayu",
    version=VERSION,
    url="https://github.com/sayerhs/vaayu",
    license="Apache Lincense, Version 2.0",
    description="Vaayu - Python Library for Wind Energy Applications",
    long_description=__doc__,
    author="Shreyas Ananthan",
    author_email="shreyas@umd.edu",
    maintainer="Shreyas Ananthan",
    maintainer_email="shreyas@umd.edu",
    include_package_data=True,
    platforms="any",
    classifiers=classifiers,
    packages=[
        'vaayu'
    ],
)
