# Script to convert Saved Messages copied out of Telegram Messenger
# (Desktop) into note-to-self emails in IMAP (requires imapfix.py).
# Works on GNU/Linux and Mac versions of Telegram Desktop as of 2018-04
# but not mobile versions.  NB they can select only 100 messages at a time,
# but if you have a version of Telegram Desktop published after 2018-08,
# it can export entire conversations to HTML by itself.

# This version assumes no paragraph breaks in messages.

from imapfix import do_multinote

to_real_inbox = False # True if --*-inbox version

import time, sys
for p in sys.stdin.read().split("\n\n"):
    head,msg = p.split("\n",1)
    subj = msg.split("\n",1)[0][:60]
    if msg==subj: msg = ""
    timestamp = head.rsplit("[")[1][:-1] # 30.04.18 20:02
    tdate,ttime = timestamp.split()
    dd,mmm,yy = tdate.split('.')
    hh,mm = ttime.split(':')
    do_multinote(msg,time.mktime((int(yy)+2000,int(mmm),int(dd),int(hh),int(mm),0,-1,-1,-1)),to_real_inbox,subj)
