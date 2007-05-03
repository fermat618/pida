#!/usr/bin/env bash
for file in `find . -iname '*.po' | grep -v 'contrib'`; do
	echo -n "Processing $file... "
	pushd . &>/dev/null
	cd `dirname $file`
	msgfmt -o `basename $file .po`.mo `basename $file`
	popd &>/dev/null
	echo "OK"
done
