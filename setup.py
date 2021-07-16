from setuptools import setup
from os import environ
import re

gemstone_dir = environ['GEMSTONE']

version_match = re.match('/opt/gemstone/GemStone64Bit(\d+\.\d+\.\d+)-x86_64.Linux', gemstone_dir)
assert version_match, 'Cannot parse a gemstone version from the current $GEMSTONE (%s)' % gemstone_dir
gemstone_version = version_match.group(1)


setup(
    name='parseltongue',
    version='2.0.0',
    install_requires=['reahl-component'],
    setup_requires=['cython','pytest-runner'],
    tests_require=['pytest', 'reahl-component', 'reahl-tofu'],
    packages=['ptongue']
    )

