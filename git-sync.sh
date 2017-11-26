#!/bin/bash
wget -N http://people.ds.cam.ac.uk/ssb22/setup/maclinux.txt
wget -N http://people.ds.cam.ac.uk/ssb22/setup/webcheck.py
wget -N http://people.ds.cam.ac.uk/ssb22/setup/imapfix.py
git commit -am "Update $(echo $(git diff|grep '^--- a/'|sed -e 's,^--- a/,,')|sed -e 's/ /, /g')" && git push
