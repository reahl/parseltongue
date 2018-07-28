
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <gemstone_version>"
    exit 1
fi

VERSION=$1
ARCH=x86_64
export GEMSTONE=/opt/gemstone/GemStone64Bit${VERSION}-${ARCH}.Linux
export LD_LIBRARY_PATH=$GEMSTONE/lib
. $GEMSTONE/bin/gemsetup.sh
exec bash
