#from distutils.core import setup, Extension
#run virtualenv: python setup.py develop -N
from setuptools import setup, find_packages, Extension
module1 = Extension('spi', sources = ['spi.c', 'spi_data.c'])

setup (
    name = 'spi',
    version = '1.0',
    description = 'Do stuff!',
    ext_modules = [module1],
 )