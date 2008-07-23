#!/usr/bin/env bash

INTLTOOL=`which intltool-extract`
if [ "X" == "X$INTLTOOL" ]; then
	echo "intltool-extract not found."
	echo "You need to install intltool package before using this tool."
	exit
fi

GETTEXT=`which gettext`
if [ "X" == "X$GETTEXT" ]; then
	echo "gettext not found."
	echo "You need to install gettext package before using this tool."
	exit
fi

function usage()
{
	echo "Usage: tools/locale.sh [build|update|create] <servicename> <lang>"
	echo "Examples:"
	echo "  - Build all locales : tools/locale.sh build"
	echo "  - Create po for a service : tools/locale.sh create service fr_FR"
	echo "  - Update po for a service : tools/locale.sh update service fr_FR"
	echo "  - Update po for pida : tools/locale.sh update pida fr_FR"
	echo "  - Import all po from launchpad : tools/locale.sh import_launchpad launchpad-export.tar.gz"
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
	xgettext -k_ -kN_ -o $file `ls *.py glade/*.glade.h 2>/dev/null`

	echo "Update some info"
	sed -e 's/CHARSET/utf-8/' $file > $file.bak
	sed -e 's/SOME\ DESCRIPTIVE\ TITLE/PIDA/' $file.bak > $file
	sed -e "s/YEAR\ THE\ PACKAGE'S\ COPYRIGHT\ HOLDER/The\ PIDA\ Team/" $file > $file.bak
	sed -e 's/the\ PACKAGE\ package/the\ PIDA\ package/' $file.bak > $file

	rm $file.bak 2>/dev/null
	rm glade/*.glade.h 2>/dev/null

	echo "Done."
	echo ""
	echo `grep 'msgstr ""' $file | wc -l` "messages need to be translated (approx)"
	echo "Now edit file pida/services/$1/$file"

	cd ../../..
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
	xgettext --omit-header --foreign-user -k_ -kN_ -o $file.new `ls *.py glade/*.glade.h 2>/dev/null`

	echo "Merging messages"
	msgmerge -U $file $file.new

	rm $file.new 2>/dev/null
	rm glade/*.glade.h 2>/dev/null

	echo "Done."
	echo ""
	echo `grep 'msgstr ""' $file | wc -l` "messages need to be translated (approx)"
	echo "Now edit file pida/services/$1/$file"

	cd ../../..
}

function locale_update_pida()
{
	cd pida

	dir="resources/locale/$1/LC_MESSAGES"
	file="$dir/pida.po"

	if [ ! -f "$file" ]; then
		cd ..
		echo "Pida po file don't exist ?!"
		exit
	fi

	echo "Generate temporary .h for glade files"
	find resources/glade -iname '*.glade' -exec intltool-extract --type=gettext/glade {} \;

	echo "Find py files"
	files=`find . -iname '*py' | grep -v -E '\/.svn\/|\/services\/|\/utils\/feedparser.py'`

	echo "Extract messages"
	xgettext --omit-header --foreign-user -k_ -kN_ -o $file.new $files resources/glade/*.glade.h

	echo "Merging messages"
	msgmerge -U $file $file.new

	rm $file.new 2>/dev/null
	rm resources/glade/*.glade.h 2>/dev/null

	echo "Done."
	echo ""
	echo `grep 'msgstr ""' $file | wc -l` "messages need to be translated (approx)"
	echo "Now edit file pida/$file"

	cd ..
}

function locale_import_launchpad()
{
	tmpdir="/tmp/pidalocale_$RANDOM"

	echo "Create temporary $tmpdir"
	mkdir -p $tmpdir

	echo "Extract launchpad file"
	tar -C $tmpdir -xzf $1
	if [ $? -ne 0 ]; then
		echo ""
		echo "Invalid launchpad tar.gz export file"
		echo "Go to https://translations.launchpad.net/pida/trunk/+export"
		echo "And click on 'Request Download'"
		exit
	fi

	cd pida
	for tr in $tmpdir/pida-*.po; do
		lang=`basename $tr .po | sed 's/pida-//'`
		dir="resources/locale/$lang/LC_MESSAGES"
		file="$dir/pida.po"

		if [ ! -d "$dir" ]; then
			echo "Create lang $lang"
			mkdir -p $dir
		fi

		echo "Copy file for $lang"
		cp $tr $file

		pushd .
		cd ..
		locale_update_pida $lang
		popd
	done

	echo "Remove temporary $tmpdir"
	rm -rf $tmpdir

	echo "Done."
	echo ""
	echo "Now, build all po file :"
	echo " - tools/locales.sh build"
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

		if [ "$2" == "pida" ]; then
			locale_update_pida $3
		else
			locale_update $2 $3
		fi
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

	"import_launchpad")
		if [ "X$2" == "X" ]; then
			usage
			exit
		fi

		locale_import_launchpad $2
		;;
	
	*)
		usage
		;;
esac
