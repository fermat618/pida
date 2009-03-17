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
        ln -sf $name src/$name/$name #XXX: asume normal forms
    else
        echo -n update\ 
        pushd src/$name >/dev/null
        case $vcs in
            hg) hg pull -uq;;
            bzt) bzr update -q;;
        esac
        popd >/dev/null
    fi

    pushd src/$name >/dev/null
    echo -n build\ 
    python setup.py build_ext -i >/dev/null
    echo done
    popd >/dev/null
}


mkdir -p externals/src >/dev/null
pushd externals >/dev/null

get_or_update rope hg http://www.bitbucket.org/agr/rope/
get_or_update anyvc hg http://bitbucket.org/RonnyPfannschmidt/anyvc/
get_or_update kiwi bzr lp:kiwi

popd >/dev/null
