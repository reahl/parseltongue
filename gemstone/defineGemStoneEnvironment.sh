#!/bin/sh -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <gemstone_version>"
    exit 1
fi

VERSION=$1

GEMSHELL=$(readlink -f $(dirname $0))/gemShell.sh

echo "================== profile before =========="
echo GEMSTONE1: $GEMSTONE
cat $HOME/.profile
echo "================== profile before end =========="

cat <<EOF >> $HOME/.profile
VERSION=$VERSION . $GEMSHELL
echo GEMSTONE: $GEMSTONE
EOF

echo "================== profile after=========="
echo GEMSTONE2: $GEMSTONE
cat $HOME/.profile
echo "================== profile after end=========="
