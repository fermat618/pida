#! /bin/sh
rm -rf docs/html/dev
a2x -f chunked -d docs/html/ --asciidoc-opts="-d book" docs/txt/dev.txt
mv docs/html/dev.chunked docs/html/dev
