#!/usr/bin/env bash

if [ "X$1" == "X" ]; then 
	echo "Usage: ./create-po.sh fr_FR"
	exit
fi

FILES=`find ../../ -iname '*.py' | grep -v -E 'pida/services|pida/utils'`
mkdir -p $1/LC_MESSAGES/
xgettext -o $1/LC_MESSAGES/pida.po $FILES

