#!/bin/sh
for plugin in pida-plugins/*/
do
    ./run-plugin-upload.py $plugin
done
