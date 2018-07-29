#!/bin/sh -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <gemstone_version>"
    exit 1
fi

VERSION=$1

GEMVARS=$(readlink -f $(dirname $0))/gemVars.sh
VAGRANT_HOME=/home/vagrant

cat <<EOF >> $VAGRANT_HOME/.profile
. $GEMVARS $VERSION
EOF


