#!/bin/sh
get_or_update() {
    name=$1;repo=$2;
    echo -n syncing $name :\ 
    if [ ! -d "src/$name" ]
    then
        echo checkout
        hg clone -q $repo src/$name
    else
        echo update
        cd src/$name >/dev/null
        HGPLAIN=1 hg pull -uq
        cd ../.. >/dev/null
    fi

    ln -sf src/$name/$name $name #XXX: asume normal forms
}

if [ ! `which hg` ]
then
    echo "Error: You must install Mercurial to update the externals"
    exit
fi

FROM_WD=`pwd`
cd $(dirname $(dirname $PWD/$0))
mkdir -p externals/src >/dev/null
cd externals >/dev/null

get_or_update rope http://www.bitbucket.org/agr/rope/

get_or_update anyvc http://bitbucket.org/RonnyPfannschmidt/anyvc/
get_or_update pygtkhelpers http://bitbucket.org/aafshar/pygtkhelpers-main/

get_or_update apipkg http://bitbucket.org/hpk42/apipkg/
get_or_update execnet http://bitbucket.org/hpk42/execnet/

get_or_update flatland http://bitbucket.org/jek/flatland/

cd $FROM_WD
