#! /bin/sh
a2x -f chunked -d docs/html/ docs/txt/dev.txt
mv docs/html/dev.chunked docs/html/dev
