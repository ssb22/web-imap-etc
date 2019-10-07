#!/bin/bash
git pull --no-edit
wget -N http://ssb22.user.srcf.net/setup/maclinux.txt http://ssb22.user.srcf.net/setup/webcheck.py http://ssb22.user.srcf.net/setup/imapfix.py http://ssb22.user.srcf.net/gradint/timetrack.js
git commit -am "Update $(echo $(git diff|grep '^--- a/'|sed -e 's,^--- a/,,')|sed -e 's/ /, /g')" && git push
