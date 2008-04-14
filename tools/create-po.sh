#!/usr/bin/env bash

if [ "X$1" == "X" ]; then 
	echo "Usage: ./create-po.sh fr_FR"
	exit
fi

# Beware build/ must not existing when using this script.
# I didn't find how to ignore the build/ directory below... (d_rol)
FILES=`find -iname '*.py' | grep -v -E 'pida/services|pida/utils|contrib'`
mkdir -p pida/resources/locale/$1/LC_MESSAGES/
if [ -f pida/resources/locale/$1/LC_MESSAGES/pida.po ]; then
	echo Merging new strings...
	xgettext -o new.po $FILES
	sed -e 's/CHARSET/utf-8/' new.po > new2.po
	mv new2.po new.po
	msgmerge -U pida/resources/locale/$1/LC_MESSAGES/pida.po new.po
	rm new.po
else
	echo Writing new locale...
	xgettext -o pida/resources/locale/$1/LC_MESSAGES/pida.po $FILES
fi
