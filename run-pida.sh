#!/bin/sh
PIDA_PATH=`dirname $0`
PYTHONPATH="$PYTHONPATH:$PIDA_PATH" python $PIDA_PATH/bin/pida $*
