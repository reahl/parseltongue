#!/bin/sh -ex

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <gemstone_version>"
    exit 1
fi

. $(dirname $0)/gemVars.sh
exec bash
    
