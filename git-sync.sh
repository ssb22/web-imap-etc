#!/bin/bash
git pull --no-edit
wget -N http://people.ds.cam.ac.uk/ssb22/setup/maclinux.txt http://people.ds.cam.ac.uk/ssb22/setup/webcheck.py http://people.ds.cam.ac.uk/ssb22/setup/imapfix.py http://people.ds.cam.ac.uk/ssb22/gradint/timetrack.js
git commit -am "Update $(echo $(git diff|grep '^--- a/'|sed -e 's,^--- a/,,')|sed -e 's/ /, /g')" && git push
