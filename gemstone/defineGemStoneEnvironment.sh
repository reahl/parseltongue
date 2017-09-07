#!/bin/bash -e

cat <<'EOF' >> $HOME/.profile
    export GEMSTONE=/opt/gemstone/GemStone64Bit3.3.3-x86_64.Linux
    . $GEMSTONE/bin/gemsetup.sh  
EOF
