from setuptools import setup

setup(
    name='parseltongue',
    version='2.0.0',
    install_requires=['reahl-component', 'packaging'],
    setup_requires=['pytest-runner'],
    tests_require=['pytest', 'reahl-component', 'reahl-tofu'],
    packages=['ptongue']
    )

