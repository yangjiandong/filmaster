#!/bin/bash
#command line args passing to ln (i.e. -f)
set -x
cd film20/config
ln -sf $@ urls/en.py urls.py
cd ../static
ln -sf $@ english.css localized.css
ln -sf $@ avatars-dev avatars
cd img
ln -sf $@ en localized
cd ../../
