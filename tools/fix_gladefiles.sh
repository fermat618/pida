#!/bin/bash
rm $(find -name \*.glade) $(find -name *.orig)
hg revert --all --quiet

for gladefile in $(find -name \*-*.glade)
do
    plugin=$(dirname $(dirname $gladefile))
    gladename=$(basename $gladefile .glade)
    echo renaming $gladename in ${plugin//.\/pida*?\//}
    for pyfile in $plugin/*.py
    do
        sed -i "s/$gladename/${gladename//-/_}/" $pyfile
        rm -f $pyfile.orig
    done
    hg rename "$gladefile" "${gladefile//-/_}"
    grep -n $gladename $plugin/*.py 
done
echo fixing glade files
for gladefile in $(find -name \*.glade)
do
    for name in $(xmlstarlet sel -t -m "//object" -v @id -n ${gladefile}|grep -)
    do
        xmlstarlet \
            ed -P -u "//object[@id='$name']/@id" -v ${name//-/_} \
            $gladefile >  $gladefile.2 && mv $gladefile.2 $gladefile
    done
done

