#!/bin/sh
get_or_update() {
    vcs=$2;name=$1;repo=$3;
    echo -n syncing $name \ 
    if [ ! -d "src/$name" ]
    then
        echo -n checkout\ 
        case $vcs in
            hg) hg clone -q $repo src/$name;;
            bzr) bzr checkout -q $repo src/$name;
        esac
    else
        echo -n update\ 
        cd src/$name >/dev/null
        case $vcs in
            hg) hg pull -uq;;
            bzt) bzr update -q;;
        esac
        cd ../.. >/dev/null
    fi

    ln -sf src/$name/$name $name #XXX: asume normal forms
    cd src/$name >/dev/null
    echo -n build\ 
    python setup.py build_ext -i >/dev/null
    echo done
    cd ../.. >/dev/null
}

if [ ! `which bzr` ]
then
    print "Error: You must install bzr to update Kiwi."
    exit
fi

if [ ! `which hg` ]
then 
    print "Error: You must install Mercurial to update anyvnc and rope."
    exit
fi

mkdir -p externals/src >/dev/null
cd externals >/dev/null

get_or_update rope hg http://www.bitbucket.org/agr/rope/
get_or_update anyvc hg http://bitbucket.org/RonnyPfannschmidt/anyvc/
get_or_update kiwi bzr lp:kiwi
get_or_update pygtkhelpers hg http://bitbucket.org/aafshar/pygtkhelpers-main/

cd ..  >/dev/null
