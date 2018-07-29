#!/bin/sh -e

if ( [ -z "$VERSION" ] ) && ( [ "$#" -ne 1 ] ); then
    echo "Usage: $0 <gemstone_version>"
    exit 1
fi

if [ "$#" -eq 1 ]; then
    VERSION=$1
fi

ARCH=x86_64
export GEMSTONE=/opt/gemstone/GemStone64Bit${VERSION}-${ARCH}.Linux
export LD_LIBRARY_PATH=$GEMSTONE/lib
. $GEMSTONE/bin/gemsetup.sh

if [ "$(basename -- $0)" = "gemShell.sh" ]; then
    echo "Not sourced, executing bash"
    exec bash
fi
    
