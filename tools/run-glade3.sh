#!/bin/sh

SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`

echo $SCRIPTPATH

PYTHONPATH=$SCRIPTPATH
GLADE_CATALOG_PATH=$SCRIPTPATH/glade3-plugin/ \
GLADE_MODULE_PATH=$SCRIPTPATH/glade3-plugin/  \
PYTHONPATH=$SCRIPTPATH/glade3-plugin/:$SCRIPTPATH/../externals/ glade-3 $*
