#!/bin/sh
get_or_update() {
    name=$1;repo=$2;
    echo -n syncing $name \ 
    if [ ! -d "src/$name" ]
    then
        echo -n checkout\ 
        hg clone -q $repo src/$name
    else
        echo -n update\ 
        cd src/$name >/dev/null
        hg pull -uq
        cd ../.. >/dev/null
    fi

    ln -sf src/$name/$name $name #XXX: asume normal forms
    cd src/$name >/dev/null
    echo -n build\ 
    python setup.py build_ext -i >/dev/null
    echo done
    cd ../.. >/dev/null
}

if [ ! `which hg` ]
then 
    print "Error: You must install Mercurial to update the externals"
    exit
fi

FROM_WD=`pwd`
cd $(dirname $(dirname $PWD/$0))
mkdir -p externals/src >/dev/null
cd externals >/dev/null

get_or_update rope http://www.bitbucket.org/agr/rope/
get_or_update anyvc http://bitbucket.org/RonnyPfannschmidt/anyvc/
get_or_update pygtkhelpers http://bitbucket.org/aafshar/pygtkhelpers-main/

cd $FROM_WD
