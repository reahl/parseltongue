pip install Cython
echo "python setup.py build_ext --inplace"
echo "python setup.py develop -N"
echo "export LD_LIBRARY_PATH=/opt/gemstone/GemStone64Bit3.3.3-x86_64.Linux/lib"
echo "pytest"