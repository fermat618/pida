#!/usr/bin/env bash

function usage()
{
	echo "Usage: tools/locale.sh [build|update|create] <servicename> <lang>"
	echo "Examples:"
	echo "  - Build all locales : tools/locale.sh build"
	echo "  - Create po for a service : tools/locale.sh create service fr_FR"
	echo "  - Update po for a service : tools/locale.sh update service fr_FR"
}

function locale_build()
{
	echo "Searching all 'po' files..."
	for file in `find . -iname '*.po' | grep -v 'contrib'`; do
		echo -n "Processing $file... "
		msgfmt -o `dirname $file`/`basename $file .po`.mo $file
		echo "OK"
	done
	echo "Build done."
}

function locale_create()
{
	if [ ! -d "pida/services/$1" ]; then
		echo "Service '$1' not exist"
		exit
	fi

	cd pida/services/$1
	dir="locale/$2/LC_MESSAGES"
	file="$dir/$1.po"

	if [ -f "$dir/$1.po" ]; then
		cd ../../..
		echo "Service '$1' have already a po file, use update instead of create"
		echo "Remove this file if you really want to create it"
		exit
	fi

	echo "Create directory $dir"
	mkdir -p $dir

	echo "Generate temporary .h for glade files"
	find glade -iname '*.glade' -exec intltool-extract --type=gettext/glade {} \;

	echo "Extract messages"
	xgettext -k_ -kN_ -o $file *.py glade/*.glade.h

	echo "Update some info"
	sed -e 's/CHARSET/utf-8/' $file > $file.bak
	sed -e 's/SOME\ DESCRIPTIVE\ TITLE/PIDA/' $file.bak > $file
	sed -e "s/YEAR\ THE\ PACKAGE'S\ COPYRIGHT\ HOLDER/The\ PIDA\ Team/" $file > $file.bak
	sed -e 's/the\ PACKAGE\ package/the\ PIDA\ package/' $file.bak > $file

	rm $file.bak 2>/dev/null
	rm glade/*.glade.h 2>/dev/null

	cd ../../..
	echo "Done."
	echo ""
	echo "Now edit file pida/services/$1/$file"
}

function locale_update()
{
	if [ ! -d "pida/services/$1" ]; then
		echo "Service '$1' not exist"
		exit
	fi

	cd pida/services/$1
	dir="locale/$2/LC_MESSAGES"
	file="$dir/$1.po"

	if [ ! -f "$dir/$1.po" ]; then
		cd ../../..
		echo "Service '$1' don't have a po file, use create instead of update"
		exit
	fi

	echo "Generate temporary .h for glade files"
	find glade -iname '*.glade' -exec intltool-extract --type=gettext/glade {} \;

	echo "Extract messages"
	xgettext --omit-header --foreign-user -k_ -kN_ -o $file.new *.py glade/*.glade.h

	echo "Update some info"
	sed -e 's/CHARSET/utf-8/' $file.new > $file.bak
	
	echo "Merging messages"
	msgmerge -U $file $file.bak

	rm $file.new 2>/dev/null
	rm $file.bak 2>/dev/null
	rm glade/*.glade.h 2>/dev/null

	cd ../../..
	echo "Done."
	echo ""
	echo "Now edit file pida/services/$1/$file"
}

case "$1" in 
	"build")
		locale_build
		;;
	
	"update")
		if [ "X$2" == "X" ]; then
			usage
			exit
		fi

		if [ "X$3" == "X" ]; then
			usage
			exit
		fi

		locale_update $2 $3
		;;

	"create")
		if [ "X$2" == "X" ]; then
			usage
			exit
		fi

		if [ "X$3" == "X" ]; then
			usage
			exit
		fi

		locale_create $2 $3
		;;
	
	*)
		usage
		;;
esac
