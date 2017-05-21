#from distutils.core import setup, Extension
#To create virtualenv run: python setup.py develop -N.
#To clean run: python setup.py clean
from setuptools import setup, find_packages, Extension
#from distutils.core import setup, Extension
setup(name="player", version="1.0",
      ext_modules=[
         Extension("player", ["player.c"]),
         ])