from setuptools import setup
from setuptools.extension import Extension
from Cython.Build import cythonize
from os import environ
import re

gemstone_dir = environ['GEMSTONE']

version_match = re.match('/opt/gemstone/GemStone64Bit(\d+\.\d+\.\d+)-x86_64.Linux', gemstone_dir)
assert version_match, 'Cannot parse a gemstone version from the current $GEMSTONE (%s)' % gemstone_dir
gemstone_version = version_match.group(1)



gemstone_compile_args=[ '-fmessage-length=0',
                        '-fcheck-new',
                        '-O3',
                        '-ggdb',
                        '-m64',
                        '-pipe',
                        '-D_REENTRANT',
                        '-D_GNU_SOURCE',
                        '-pthread',
                        '-fPIC',
                        '-fno-strict-aliasing',
                        '-fno-exceptions']
#                        '-x'
#                        'c++']
gemstone_link_args=['-m64',
                    '-Wl,-Bdynamic,--no-as-needed',
                    '-lpthread',
                    '-Wl,--as-needed',
                    '-lcrypt',
#                    '-ldl',
                    '-lc',
                    '-lm',
                    '-lrt',
                    '-Wl,-traditional',
                    '-Wl,-flat_namespace,-undefined,dynamic_lookup',
                    '-Wl,-z,lazy']



setup(
    name='parseltongue',
    version='1.0.2',
    install_requires=['reahl-component'],
    setup_requires=['cython','pytest-runner'],
    tests_require=['pytest', 'reahl-component', 'reahl-tofu'],
    packages=['ptongue'],
    ext_modules=cythonize([Extension('ptongue.gemproxy',
                                     include_dirs = ['{}/include'.format(gemstone_dir)],
                                     language='c++',
                                     sources = ['ptongue/gemproxy.pyx']
                           ),
                           Extension('ptongue.gemproxyrpc',
                                     include_dirs = ['{}/include'.format(gemstone_dir)],
                                     library_dirs=['.', '{}/lib'.format(gemstone_dir)],
                                     libraries=['gcits-{}-64'.format(gemstone_version)],
                                     libraries=['dl'],
                                     language='c++',
                                     sources = ['ptongue/gemproxyrpc.pyx'],
                                     extra_compile_args=gemstone_compile_args,
                                     extra_link_args=gemstone_link_args
                           ),
                           Extension('ptongue.gemproxylinked',
                                     include_dirs = ['{}/include'.format(gemstone_dir)],
                                     library_dirs=['.', '{}/lib'.format(gemstone_dir)],
                                     libraries=['dl'],
                                     libraries=['gcilnk-{}-64'.format(gemstone_version), 'gbjgci313-{}-64'.format(gemstone_version),
                                                'icuuc.54.1', 'icui18n.54.1', 'icudata.54.1', 'gcsi-{}-64'.format(gemstone_version)],
                                     language='c++',
                                     sources = ['ptongue/gemproxylinked.pyx'],
                                     extra_compile_args=gemstone_compile_args,
                                     extra_link_args=gemstone_link_args
                           )],
                           compiler_directives={'language_level': '3'}
    ))

