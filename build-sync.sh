#!/bin/bash
# sync MacLinux etc to SVN
wget -N http://people.ds.cam.ac.uk/ssb22/setup/maclinux.txt
wget -N http://people.ds.cam.ac.uk/ssb22/setup/webcheck.py
wget -N http://people.ds.cam.ac.uk/ssb22/setup/imapfix.py
svn commit -m "Update maclinux/webcheck/imapfix"
