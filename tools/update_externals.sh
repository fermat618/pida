#!/bin/sh

REPOSPATH="`pwd`/externals/src"
OLDPATH=`pwd`
REPOS="
rope|hg|http://www.bitbucket.org/agr/rope/|rope/rope|rope
anyvc|hg|http://bitbucket.org/RonnyPfannschmidt/anyvc/|anyvc/anyvc|anyvc
kiwi|bzr|lp:kiwi|kiwi/kiwi|kiwi
"

mkdir -p $REPOSPATH
cd "$REPOSPATH"


for x in $REPOS; do
        dir=$(echo "$x" | cut -d\| -f1)
        vcs=$(echo "$x" | cut -d\| -f2)
        repo=$(echo "$x" | cut -d\| -f3)
        linksrc=$(echo "$x" | cut -d\| -f4)
        linkdest=$(echo "$x" | cut -d\| -f5)

        if [ ! -d "$dir/" ]; then
            echo "[$vcs] $repo -> $dir"
            case "$vcs" in
            hg)
                    hg clone "$repo" "$dir"
                    ;;
            bzr)
                    bzr checkout "$repo" "$dir"
                    ;;
            esac
            if test -n "$linksrc"; then
                cd ..
                ln -s src/$linksrc $linkdest
                cd src
            fi
        fi
done



for x in $REPOS; do
        dir=$(echo "$x" | cut -d\| -f1)
        vcs=$(echo "$x" | cut -d\| -f2)
        repo=$(echo "$x" | cut -d\| -f3)
        linksrc=$(echo "$x" | cut -d\| -f4)
        linkdest=$(echo "$x" | cut -d\| -f5)

        cd "$dir"

        echo "[$dir] syncing"
        case "$vcs" in
        hg)        hg pull && hg update ;;
        *)        echo "$vcs: not supported yet." ;;
        esac

        cat <<-EOT

        [$dir] building...
EOT
        (
        python setup.py build_ext -i
        python setup.py build
        ) 
       cd - > /dev/null
done
echo "finished"
cd $OLDPATH
