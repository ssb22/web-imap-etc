#!/usr/bin/env python

# ImapFix v1.11 (c) 2013-14 Silas S. Brown.  License: GPL

# Put your configuration into imapfix_config.py,
# overriding these options:

hostname = "imap4-ssl.example.org"
username = "me"
password = "xxxxxxxx"
login_retry = False # True = don't stop on login failure
# (useful if your network connection is not always on)

filtered_inbox = "in" # or =None if you don't want to do
# any moving from inbox to filtered_inbox (i.e. no rules)
# but just use maildirs_to_imap or maildir_to_copyself,
# e.g. because you're on an auxiliary machine (which does
# not have your spamprobe database etc) but still want to
# use maildir_to_copyself for mutt (see notes below)

leave_note_in_inbox = True # for "new mail" indicators

newmail_directory = None
# or newmail_directory = "/path/to/a/directory"
# - any new mail put into any folder by header_rules will
# result in a file being created in that local directory
# with the same name as the folder

max_size_of_first_part = 48*1024
# any messages whose first part is longer than this will be
# converted into attachments.  This is for sync'ing in
# bandwidth-limited situations using a device that knows to
# not fetch attachments but doesn't necessarily know to not
# fetch more than a certain amount of text (especially if
# it's only HTML).

header_rules = [
    ("folder-name-1",
     ["regexp to check for in header",
      "regexp to check for in header",
      "regexp to check for in header"]),
    ("folder-name-2",
     ["regexp to check for in header"]),
    # etc; folder name None = delete the message;
    # "inbox" = change to filtered_inbox;
    # "spam" = change to spam_folder;
    # start with a * if this folder does not need any
    # notification in newmail_directory
]

def extra_rules(message_as_string): return False
# you can override this to any function you want, which
# returns the name of a folder, or None to delete the
# message, or False = no decision
catch_extraRules_errors = True

spamprobe_command = "spamprobe -H all" # (or = None)
spam_folder = "spam"

poll_interval = 4*60 # TODO: use imaplib2 and IDLE ?
# Note: set poll_interval=False if you want just one run.
logout_before_sleep = False # suggest set to True if using
# a long poll_interval, or if filtered_inbox=None

midnight_command = None
# or, daily_command = "system command to run at midnight"
# (useful if you don't have crontab access on the machine)

quiet = True # False = print messages (including quota)
# If you set quiet = 2, will be quiet if and only if the
# standand output is not connected to a terminal

maildirs_to_imap = None # or path to a local directory of
# maildirs; messages will be moved to their corresponding
# folders on IMAP (renaming inbox to filtered_inbox
# and spam to spam_folder, and converting character sets)
maildir_colon = ':'

maildir_to_copyself = None # or path to a maildir whose
# messages should be moved to imap's copyself (for example if
# mutt is run on the same machine and saves its messages
# locally, which is more responsive than uploading to imap,
# but you still want them to be uploaded to imap eventually)
copyself_delete_attachments = False # if True, attachments
# are DELETED when moving from maildir_to_copyself to the
# IMAP folder (but a record is still kept of what was
# attached, unlike the fcc_attach='no' setting in Mutt 1.5)
copyself_folder_name = "Sent Items"

archive_path = "oldmail"
archive_rules = [
    # These rules are used when you run with --archive
    # Each rule is: ("folder-name", max-age (days), spamprobe-action)
    # If max-age specified, older messages will be archived.  Independently of this, spamprobe-action (if specified) will be run on all messages.
    ("spam-confirmed", 30, "train-spam"),
    ("some-folder", 90, None),
    ("some-other-folder", None, "train-good"),
    ]
compression = "bz2" # or "gz" or None
archived_attachments_path = "archived-attachments" # or None
attachment_filename_maxlen = 30

# Set secondary_imap_hostname if you also want to check
# some other IMAP server and treat its messages as being
# in the inbox of the main server (i.e. copied over and
# processed as normal).  You can check this less often by
# setting secondary_imap_delay.  (Will not stay logged in
# between checks.)
secondary_imap_hostname = ""
secondary_imap_username = "me"
secondary_imap_password = "xxxxxxxx"
secondary_imap_delay = 24 * 3600

# Run with --quicksearch (search string) to search both
# archive_path and the server (all folders), but "quick"
# in that it doesn't decode MIME attachments etc
# (TODO: implement more thorough search, with regexps, but
# it would have to download all messages from the server)

# Run with --delete (folder name) to delete a folder

# Run with --note (subject) to put a note to yourself
# (taken from standard input) directly into filtered_inbox
# without doing any other kind of run.  This might be
# useful from scripts etc (you can get the note without
# having to wait for it to go through SMTP and polling).
# Run with --htmlnote to do the same but send as HTML.
# Run with --maybenote to do --note only if standard input
# has text (no mail left if your script printed nothing).

# End of configuration options
# ------------------------------------------------------

from imapfix_config import *

if filtered_inbox==None: spamprobe_command = None

import imaplib,email,email.utils,time,os,sys,re,base64,quopri,mailbox,traceback
from cStringIO import StringIO

if compression=="bz2":
    import bz2
    compression_ext = ".bz2"
elif compression=="gz":
    import gzip
    compression_ext = ".gz"
else: compression_ext = ""

def debug(msg):
    if not quiet: print msg
    
def check_ok(r):
    "Checks that the return value of an IMAP call 'r' is OK, raises exception if not"
    typ, data = r
    if not typ=='OK': raise Exception(typ+' '+repr(data))

def spamprobe_rules(message):
  if run_spamprobe("train",message).startswith("SPAM"): return spam_folder # classify + maybe update database
  else: return filtered_inbox

def run_spamprobe(action,message):
  if not spamprobe_command: return ""
  cIn, cOut = os.popen2(spamprobe_command+" "+action)
  cIn.write(message); cIn.close()
  return cOut.read()

def spamprobe_cleanup():
    if not spamprobe_command: return
    debug("spamprobe cleanup")
    os.system(spamprobe_command+" cleanup")

def process_header_rules(header):
  for box,matchList in header_rules:
    for headerLine in header.split("\r\n"):
      for m in matchList:
        i=re.finditer(m,headerLine)
        try: i.next()
        except StopIteration: continue
        if box and box[0]=='*': box=box[1:] # just save it without indication
        elif box: open(newmail_directory+os.sep+box,'a')
        return rename_folder(box)
  return False

def process_imap_inbox():
    make_sure_logged_in()
    check_ok(imap.select()) # the inbox
    typ, data = imap.search(None, 'ALL')
    if not typ=='OK': raise Exception(typ)
    imapMsgid = None ; newMail = False
    for msgID in data[0].split():
        typ, data = imap.fetch(msgID, '(RFC822)')
        if not typ=='OK': continue
        # data[0][0] is e.g. '1 (RFC822 {1015}'
        message = data[0][1]
        if leave_note_in_inbox and imap==saveImap and isImapfixNote(message):
            if imapMsgid: # somehow ended up with 2, delete one
                imap.store(imapMsgid, '+FLAGS', '\\Deleted')
            imapMsgid = msgID ; continue
        # globalise charsets BEFORE the filtering rules
        # (especially if they've been developed based on
        # post-charset-conversion saved messages)
        msg = email.message_from_string(message)
        changed = globalise_charsets(msg)
        if max_size_of_first_part and size_of_first_part(msg) > max_size_of_first_part: msg,changed = turn_into_attachment(msg),True
        if changed: message = msg.as_string()
        header = message[:message.find("\r\n\r\n")]
        box = process_header_rules(header)
        if box==False:
            try: box = rename_folder(extra_rules(message))
            except:
                if not catch_extraRules_errors: raise
                o = StringIO() ; traceback.print_exc(None,o)
                save_to(filtered_inbox,"From: imapfix.py\r\nSubject: imapfix_config problem in extra_rules (message has been saved to '%s')\r\nDate: %s\r\n\r\n%s\n" % (filtered_inbox,email.utils.formatdate(time.time()),o.getvalue()))
                box = filtered_inbox
            if box==False: box = spamprobe_rules(message)
        if box:
            debug("Saving message to "+box)
            save_to(box, message)
            if box==filtered_inbox: newMail = True
        else: debug("Deleting message")
        imap.store(msgID, '+FLAGS', '\\Deleted')
    if leave_note_in_inbox and imap==saveImap:
      if newMail:
        if imapMsgid: # delete the old one
            imap.store(imapMsgid, '+FLAGS', '\\Deleted')
        save_to("", imapfixNote())
      elif imapMsgid:
        # un-"seen" it (in case the IMAP server treats our fetching it as "seen"); TODO what if the client really read it but didn't delete?
        imap.store(imapMsgid, '-FLAGS', '\\Seen')
    check_ok(imap.expunge())
    if (not quiet) and imap==saveImap: debug("Quota "+repr(imap.getquotaroot(filtered_inbox)[1]))

def imapfixNote(): return "From: imapfix.py\r\nSubject: Folder "+repr(filtered_inbox)+" has new mail\r\nDate: "+email.utils.formatdate(time.time())+"\r\n\r\n \n" # make sure there's at least one space in the message, for some clients that don't like empty body
# (and don't put a date in the Subject line: the message's date is usually displayed anyway, and screen space might be in short supply)
def isImapfixNote(msg): return "From: imapfix.py" in msg and ("Subject: Folder "+repr(filtered_inbox)+" has new mail") in msg

def archive(foldername, mboxpath, age, spamprobe_action):
    if age:
      if spamprobe_action: extra = ", spamprobe="+spamprobe_action
      else: extra = ""
      debug("Archiving from "+foldername+" to "+mboxpath+extra+"...")
      suf = "" ; sc = 0
      while os.path.exists(mboxpath+suf+compression_ext):
        sc += 1 ; suf = "."+str(sc)
      while sc:
        if sc==1: suf = ""
        else: suf = "."+str(sc-1)
        suf2 = "."+str(sc)
        os.rename(mboxpath+suf+compression_ext,
                  mboxpath+suf2+compression_ext)
        sc -= 1
      mbox = mailbox.mbox(mboxpath) # will compress below
    else:
      debug("Processing "+foldername+"...")
      mbox = None
    make_sure_logged_in()
    typ, data = imap.select(foldername)
    if not typ=='OK': return # couldn't select that folder
    typ, data = imap.search(None, 'ALL')
    if not typ=='OK': raise Exception(typ)
    for msgID in data[0].split():
        typ, data = imap.fetch(msgID, '(RFC822)')
        if not typ=='OK': continue
        message = data[0][1]
        if spamprobe_action:
            # TODO: combine multiple messages first?
            run_spamprobe(spamprobe_action, message)
        if not age: continue
        msg = email.message_from_string(message)
        if 'Date' in msg: t = email.utils.mktime_tz(email.utils.parsedate_tz(msg['Date']))
        else: t = time.time() # undated message ??
        if t >= time.time() - age: continue
        if archived_attachments_path:
            save_attachments_separately(msg)
        mbox.add(msg) # TODO: .set_flags A=answered R=read ?  (or doesn't it matter so much for old-message archiving; flags aren't always right anyway as you might have answered something using another method)
        imap.store(msgID, '+FLAGS', '\\Deleted')
    if mbox:
        mbox.close()
        if compression:
            open_compressed(mboxpath,'wb').write(open(mboxpath,'rb').read())
            os.remove(mboxpath)
    # don't do this until got here without error:
    check_ok(imap.expunge())

def save_attachments_separately(msg):
    if msg.is_multipart():
        for i in msg.get_payload():
            save_attachments_separately(i)
        return
    try: fname = msg.get_filename()
    except: fname="illegal-filename-A"
    if not fname: return
    try: fname=fname.encode("us-ascii") # (or utf-8 if the filesystem definitely supports it)
    except: fname="illegal-filename-B"
    if '.' in fname: fext = fname[fname.rindex('.'):]
    else: fext = ""
    if len(fext) > attachment_filename_maxlen:
        fname = fname[:attachment_filename_maxlen]
    else:
        fname = fname[:-len(fext)]
        fname = fname[:attachment_filename_maxlen-len(fext)] + fext
    data = msg.get_payload(None,True)
    if not data: return
    msg.set_payload("")
    try: os.mkdir(archived_attachments_path)
    except: pass # OK if exists
    f2 = archived_attachments_path+os.sep+fname
    suffix = "" ; sufCount = 0
    while os.path.exists(f2+suffix+compression_ext):
        if open_compressed(f2+suffix,'rb').read() == data:
            # it's a duplicate - keep what we already have
            return
        sufCount += 1 ; suffix = "."+str(sufCount)
    open_compressed(f2+suffix,'wb').write(data)

def delete_attachments(msg):
    if msg.is_multipart():
        for i in msg.get_payload():
            delete_attachments(i)
    elif msg.get_filename(): msg.set_payload("")

def open_compressed(fname,mode):
    if compression=="bz2":
        return bz2.BZ2File(fname+".bz2",mode)
        # (compresslevel default is 9)
    elif compression=="gz":
        return gzip.open(fname+".gz",mode)
        # (again, compresslevel default is 9)
    else: return open(fname,mode)

already_created = set()
def save_to(mailbox, message_as_string,
            flags="", received_time = None):
    "Saves message to a mailbox on the saveImap connection, creating the mailbox if necessary"
    make_sure_logged_in()
    if not mailbox in already_created:
        saveImap.create(mailbox) # error if exists OK
        already_created.add(mailbox)
    if not received_time: received_time = time.time()
    check_ok(saveImap.append(mailbox, flags, imaplib.Time2Internaldate(received_time), message_as_string))

def rename_folder(folder):
    if not isinstance(folder,str): return folder
    if folder.lower()=="inbox":
        return filtered_inbox
    elif folder.lower()=="spam": return spam_folder
    else: return folder

def do_maildirs_to_imap():
    mailbox.Maildir.colon = maildir_colon
    for d in os.listdir(maildirs_to_imap):
        d2 = maildirs_to_imap+os.sep+d
        if not os.path.exists(d2+os.sep+"cur"):
            continue # not a maildir
        to = rename_folder(d)
        debug("Moving messages from maildir "+d+" to imap "+to)
        m = mailbox.Maildir(d2,None)
        for k,msg in m.items():
            globalise_charsets(msg)
            if 'Date' in msg: t = email.utils.mktime_tz(email.utils.parsedate_tz(msg['Date']))
            else: t = None # undated message ??
            save_to(to,msg.as_string(),imap_flags_from_maildir_msg(msg),t)
            del m[k]
        newcurtmp = ["new","cur","tmp"]
        if not any(os.listdir(d2+os.sep+ntc) for ntc in newcurtmp): # folder is now empty: remove it
            for nct in newcurtmp: os.rmdir(d2+os.sep+nct)
            os.rmdir(d2)

def imap_flags_from_maildir_msg(msg): return " ".join(" ".join({'S':r'\Seen','D':r'\Deleted','R':r'\Answered','F':r'\Flagged'}.get(flag,"") for flag in msg.get_flags()).split())

def do_maildir_to_copyself():
    mailbox.Maildir.colon = maildir_colon
    m = mailbox.Maildir(maildir_to_copyself,None)
    said = False
    for k,msg in m.items():
        if not said:
            debug("Moving messages from "+maildir_to_copyself+" to imap "+copyself_folder_name)
            said = True
        globalise_charsets(msg)
        if 'Date' in msg: t = email.utils.mktime_tz(email.utils.parsedate_tz(msg['Date']))
        else: t = None # undated message ??
        if copyself_delete_attachments:
            delete_attachments(msg)
        save_to(copyself_folder_name,msg.as_string(),imap_flags_from_maildir_msg(msg),t)
        del m[k]

def globalise_header_charset(match):
    charset = match.group(1).lower()
    if charset=="utf-8":
        return match.group() # no changes needed
    if charset in ['gb2312','gbk']: charset='gb18030'
    encoding = match.group(2)
    text = match.group(3)
    try:
        if encoding=='Q': text = quopri.decodestring(text)
        else: text = base64.decodestring(text)
        text = text.decode(charset)
    except:
        debug("Bad header line: exception decoding "+repr(text)+" in "+charset+", leaving unchanged")
        return match.group()
    return "=?UTF-8?B?"+base64.encodestring(text.encode('utf-8')).replace("\n","")+"?="

import email.mime.multipart,email.mime.message,email.mime.text
def turn_into_attachment(message):
    m2 = email.mime.multipart.MIMEMultipart()
    for k,v in message.items():
        if not k.lower() in ['content-length','content-type','content-transfer-encoding','lines']: m2[k]=v
    m2.attach(email.mime.text.MIMEText("Large message converted to attachment")) # by imapfix, but best not mention this as it might bias the filters?
    m2.attach(email.mime.message.MIMEMessage(message))
    return m2
def size_of_first_part(message):
    if message.is_multipart():
        for i in message.get_payload():
            return size_of_first_part(i)
        return 0
    return len(message.get_payload())

def globalise_charsets(message):
    """'Globalises' the character sets of all parts of
        email.message.Message object 'message'.
        Only us-ascii and utf-8 charsets are 'global'.
        Returns True if any changes were made."""
    changed = False
    for line in ["From","To","Cc","Subject","Reply-To"]:
        if not line in message: continue
        l = message[line]
        l2 = re.sub(r'=\?(.*?)\?(.*?)\?(.*?)\?=',globalise_header_charset,l)
        if l==l2: continue
        # debug("Setting "+line+" to "+repr(l2))
        del message[line]
        message[line] = l2
        changed = True
    if message.is_multipart():
        for i in message.get_payload():
            if globalise_charsets(i): changed = True
        return changed
    m = message.get_content_charset(None)
    if m in [None,'us-ascii','utf-8']: return changed # no further conversion required
    if m in ['gb2312','gbk']: m = 'gb18030'
    try: p = message.get_payload(decode=True).decode(m)
    except: return changed # problems decoding this message
    if 'Content-Transfer-Encoding' in message:
        del message['Content-Transfer-Encoding']
    if message.get_content_type()=="text/html": p = re.sub(r'(?i)<meta\s+http[-_]equiv="?content-type"?\s+content="[^"]*">','',p) # better remove charset meta tags after we changed the charset (TODO: what if they conflict with the message header anyway?)
    message.set_payload(p.encode('utf-8'),'utf-8')
    return True # charset changed

def mainloop():
  newtime = oldtime = time.localtime()[:3]
  done_spamprobe_cleanup = False
  secondary_imap_due = 0
  while True:
    if maildirs_to_imap: do_maildirs_to_imap()
    if maildir_to_copyself: do_maildir_to_copyself()
    if filtered_inbox:
        process_imap_inbox()
        if time.time() > secondary_imap_due and secondary_imap_hostname:
            process_secondary_imap()
            secondary_imap_due = time.time() + secondary_imap_delay
    if not done_spamprobe_cleanup:
        spamprobe_cleanup()
        done_spamprobe_cleanup = True
    if logout_before_sleep: make_sure_logged_out()
    if not poll_interval: break
    debug("Sleeping for "+str(poll_interval)+" seconds")
    time.sleep(poll_interval) # TODO catch imap connection errors and re-open?  or just put this whole process in a loop
    newtime = time.localtime()[:3]
    if not oldtime==newtime:
      oldtime=newtime
      if midnight_command: os.system(midnight_command)
      done_spamprobe_cleanup = False

def process_secondary_imap():
    global imap
    try:
        imap = imaplib.IMAP4_SSL(secondary_imap_hostname)
        check_ok(imap.login(secondary_imap_username,secondary_imap_password))
    except:
        debug("Could not log in to secondary IMAP: skipping it this time")
        imap = None
    if imap: process_imap_inbox()
    imap = saveImap

def do_archive():
    try: os.mkdir(archive_path)
    except: pass # no error if exists
    for foldername,age,action in archive_rules:
        if age: age = age*24*3600
        archive(foldername, archive_path+os.sep+foldername, age, action)

def yield_folders():
    "iterates through folders in imap, selecting each one as it goes"
    make_sure_logged_in()
    for foldername in imap.list()[1]:
        if '"/"' in foldername: foldername=foldername[foldername.index('"/"')+3:].lstrip()
        if foldername.startswith('"') and foldername.endswith('"'): foldername=foldername[1:-1] # TODO: check if any other unquoting is needed
        typ, data = imap.select(foldername)
        if not typ=='OK': continue
        yield foldername

def do_note(subject,ctype="",maybe=0):
    subject = subject.strip()
    if not subject: subject = "Note to self (via imapfix)"
    if isatty(sys.stdout): print "Type the note, then EOF"
    body = sys.stdin.read()
    if not body:
        if maybe: return
        body = " " # make sure there's at least one space in the message, for some clients that don't like empty body
    save_to(filtered_inbox,"From: imapfix.py\r\nSubject: "+subject+"\r\nDate: "+email.utils.formatdate(time.time())+ctype+"\r\n\r\n"+body+"\n")

def isatty(f): return hasattr(f,"isatty") and f.isatty()
if quiet==2: quiet = not isatty(sys.stdout)

def do_delete(foldername):
    foldername = foldername.strip()
    if not foldername:
        print "No folder name specified"
        return
    print "Deleting folder "+repr(foldername)
    make_sure_logged_in()
    check_ok(imap.delete(foldername))

def do_quicksearch(s):
    for foldername in yield_folders():
        typ, data = imap.search(None, 'TEXT', '"'+s.replace("\\","\\\\").replace('"',r'\"')+'"')
        if not typ=='OK': raise Exception(typ)
        for msgID in data[0].split():
            typ, data = imap.fetch(msgID, '(RFC822)')
            if not typ=='OK': continue
            message = data[0][1]
            matching_lines = filter(lambda l:s.lower() in l.lower(), message.split('\n'))
            for m in matching_lines:
                try_print(foldername,m.strip())
    if not archive_path: return
    for f in os.listdir(archive_path):
        f = archive_path+os.sep+f
        if f.endswith(compression_ext): f2 = open_compressed(f[:-len(compression_ext)],'r')
        else: f2 = open(f) # ??
        for l in f2:
            if s.lower() in l.lower(): try_print(f,l.strip())

def try_print(folder,line):
    try:
        sys.stdout.write(folder+": "+line+"\n")
        sys.stdout.flush()
    except IOError: # probably the pager quit on us
        raise SystemExit

def shell_quote(s):  return "'"+s.replace("'",r"'\''")+"'"

imap = None
def make_sure_logged_in():
    global imap, saveImap
    while imap==None:
        try:
            imap = saveImap = imaplib.IMAP4_SSL(hostname)
            check_ok(imap.login(username,password))
        except:
            if not login_retry: raise
            imap = None
            debug("Login failed; retry in 30 seconds")
            time.sleep(30)
def make_sure_logged_out():
    global imap, saveImap
    if not imap==None:
        imap.logout()
        imap = saveImap = None

if __name__ == "__main__":
  if '--archive' in sys.argv: do_archive()
  elif '--quicksearch' in sys.argv: do_quicksearch(' '.join(sys.argv[sys.argv.index('--quicksearch')+1:]))
  elif '--delete' in sys.argv: do_delete(' '.join(sys.argv[sys.argv.index('--delete')+1:]))
  elif '--note' in sys.argv: do_note(' '.join(sys.argv[sys.argv.index('--note')+1:]))
  elif '--maybenote' in sys.argv: do_note(' '.join(sys.argv[sys.argv.index('--maybenote')+1:]),maybe=1)
  elif '--htmlnote' in sys.argv: do_note(' '.join(sys.argv[sys.argv.index('--htmlnote')+1:]),"\r\nContent-type: text/html")
  else: mainloop()
