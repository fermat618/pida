#!/usr/bin/env bash
for file in `find . -iname '*.po' | grep -v 'contrib'`; do
	echo -n "Processing $file... "
	msgfmt -o `dirname $file`/`basename $file .po`.mo $file
	echo "OK"
done
