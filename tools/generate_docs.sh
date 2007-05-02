#! /bin/sh
a2x -f chunked --asciidoc-opts="-d book" -d docs/html/ docs/txt/dev.txt
mv docs/html/dev.chunked/* docs/html/dev
rm -rf docs/html/dev.chunked
