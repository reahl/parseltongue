from setuptools import setup
from setuptools.extension import Extension
from Cython.Build import cythonize
from os import environ
gemstone_dir = environ['GEMSTONE']

setup(
    name='parseltongue',
    setup_requires=['cython','pytest-runner'],
    tests_require=['pytest', 'reahl-component'],
    ext_modules=cythonize([Extension('ptongue',
                    include_dirs = ['{}/include'.format(gemstone_dir)],
                    library_dirs=['.', '{}/lib'.format(gemstone_dir)],
                    libraries=['gcits-3.3.3-64', 'gcilnk-3.3.3-64', 'icuuc.54.1'],
                    language="c++",
                    sources = ['ptongue.pyx'],
                    extra_compile_args=[ "-fmessage-length=0", "-fcheck-new", "-ggdb", "-m64", "-pipe", "-D_REENTRANT", "-D_GNU_SOURCE", "-fno-strict-aliasing", "-fno-exceptions"],
                    extra_link_args=["-Wl,-traditional", "-Wl,--warn-unresolved-symbols", "-m64", "-lpthread", "-lcrypt", "-lc", "-lm", "-lrt", "-Wl,-z,muldefs"])]))

