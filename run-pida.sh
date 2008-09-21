#!/bin/sh
PIDA_PATH=`dirname $0`
PYTHONPATH="$PIDA_PATH:$PYTHONPATH" python $PIDA_PATH/bin/pida $*
