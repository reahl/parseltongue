#!/bin/bash -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <gemstone_version>"
    exit 1
fi

VERSION=$1

GEMSHELL=$(readlink -f $(dirname $0))/gemShell.sh

cat <<EOF >> $HOME/.profile
$GEMSHELL $VERSION
EOF
