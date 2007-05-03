#!/usr/bin/env bash

if [ "X$1" == "X" ]; then 
	echo "Usage: ./create-po.sh fr_FR"
	exit
fi

FILES=`find -iname '*.py' | grep -v -E 'pida/services|pida/utils|contrib'`
mkdir -p pida/resources/locale/$1/LC_MESSAGES/
if [ -f pida/resource/locale/$1/LC_MESSAGES/pida.po ]; then
	xgettext -o new.po $FILES
	sed -e 's/CHARSET/utf-8/' new.po > new2.po
	mv new2.po new.po
	msgmerge -U pida/resources/locale/$1/LC_MESSAGES/pida.po new.po
	rm new.po
else
	xgettext -o pida/resources/locale/$1/LC_MESSAGES/pida.po $FILES
fi
