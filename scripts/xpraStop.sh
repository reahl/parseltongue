#!/bin/bash

export REMOTE_DISPLAY=":100"

while getopts "v:d:" opt; do
    case $opt in
        v) 
           export MACHINE_NAME="$OPTARG"
           ;;
        d) 
           export REMOTE_DISPLAY="$OPTARG"
           ;;
        *)
           echo "Usage: $(basename $0) [-v vagrant_machine_name] [-d remote_display]"  >&2
           exit 1
           ;;
    esac
done

set -x
vagrant ssh $MACHINE_NAME -- xpra stop "$REMOTE_DISPLAY"
