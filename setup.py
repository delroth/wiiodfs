#! /usr/bin/python2
"""
setup.py
~~~~~~~~

Setuptools based setup script.

This file is part of wiiodfs.

wiiodfs is free software: you can redistribute it and/or modify it under the
terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

wiiodfs is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
wiiodfs.  If not, see <http://www.gnu.org/licenses/>.
"""

from setuptools import setup, find_packages

setup(
    name="wiiodfs",
    version="0.1",

    packages=find_packages(),
    entry_points={
        'console_scripts': ['wiiodmount = wiiod.entry:main']
    },

    install_requires=["fs", "pycrypto"],

    author="Pierre Bourdon",
    author_email="delroth@gmail.com",
    description="An implementation of a Wii Optical Disc reader.",
    long_description=open('README').read(),
    license="GPL",
    keywords="wii filesystem disc games optical fuse",
    url="http://bitbucket.org/delroth/wiiodfs/",
    download_url="http://bitbucket.org/delroth/wiiodfs/downloads/wiiodfs-0.1.tar.gz",

    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: No Input/Output (Daemon)",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 2",
        "Topic :: Software Development :: Embedded Systems",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
    ],
)
