#!/bin/bash
# sync MacLinux to SVN
wget -N http://people.ds.cam.ac.uk/ssb22/setup/maclinux.txt
svn commit -m "Update maclinux.txt"
