#!/bin/bash -e

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <gemstone_version>"
    exit 1
fi

VERSION=$1

export VAGRANT_HOME=/home/vagrant

cat <<'EOF' >> $VAGRANT_HOME/.profile
/vagrant/gemstone/gemShell.sh $VERSION
EOF
