#!/usr/bin/env python2
# (Requires Python 2.x, not 3; search for "3.3+" in
# comment below to see how awkward forward-port would be)

"ImapFix v1.82 (c) 2013-24 Silas S. Brown.  License: Apache 2"

# Put your configuration into imapfix_config.py,
# overriding these options:

hostname = "imap4-ssl.example.org" # or host:port
username = "me"
password = "xxxxxxxx"
# (If you are likely to be editing configuration rules when
# others can see your screen, you might like to store the
# password in a separate file and do, for example,
#    password = open(".imapfix-pass").read().strip()
# instead, so that it won't be shown on-screen when you're
# editing other things.)

# You can also use OAuth2 by setting password like this:
# password = ("command to generate oauth2 string", 3500)
# where 3500 is the number of seconds before script is called again.
# (You'll then have to sort out calls to oauth2.py or whatever,
# and if you registered a 'test app' it is likely that refresh
# tokens will not persist more than a week or so and will need
# periodic renewal in a browser; this won't be the case if
# you use credentials from a production application.)

login_retry = False # True = don't stop on login failure
# (useful if your network connection is not always on)

filtered_inbox = "in" # or =None if you don't want to do
# any moving from inbox to filtered_inbox (i.e. no rules)
# but just use maildirs_to_imap or maildir_to_copyself,
# e.g. because you're on an auxiliary machine (which does
# not have your spamprobe database etc) but still want to
# use maildir_to_copyself for mutt (see notes below).
# You can also use environment variables with override
# e.g. import os; filtered_inbox = os.getenv("ImapFolder","in")
# so it can be overridden with ImapFolder for --upload

# If you want to keep your filtered_inbox on local maildir
# instead of IMAP server, set it to a tuple with the first
# item being "maildir": ("maildir","path/to/maildir")

leave_note_in_inbox = True # for "new mail" indicators

change_message_id = False # set this to True for
# providers like Gmail that refuse to accept new
# versions of messages with the same Message-ID.  Adds
# an extra digit to Message-ID (if present) when saving
# a changed version of the message to the same imap.
# This may result in a breakage of "In-Reply-To" (unless
# you edit the extra character out on the client side),
# but might be a necessary loss if you're using Gmail.

newmail_directory = None
# or newmail_directory = "/path/to/a/directory"
# - any new mail put into any folder by header_rules will
# result in a file being created in that local directory
# with the same name as the folder

max_size_of_first_part = None
# e.g. max_size_of_first_part = 48*1024
# any messages whose first part is longer than this will be
# converted into attachments.  This is for sync'ing in
# bandwidth-limited situations using a device that knows to
# not fetch attachments but doesn't necessarily know to not
# fetch more than a certain amount of text (especially if
# it's only HTML).

image_size = None # or e.g. image_size = (320,240)
# - adds scaled-down versions of any image attachment that
# exceeds this size, for previewing on low bandwidth
# (this option requires the PIL library).  The scaled-down
# versions are added only if the file is actually smaller.
# This option also tries to ensure that all images are set to
# an image/ rather than application/ Content-Type, which
# helps some mailers.

office_convert = None # or "html" or "pdf", to use
# LibreOffice/OpenOffice's 'soffice --convert-to' option
# to produce converted versions of office documents
# (beware, I have not checked soffice for vulnerabilities)
# - resulting HTML might not work on old WM phones as they
# don't support data: image URLs.
# This option also enables summary generation of
# Microsoft Calendar attachments.

pdf_convert = False # True = use "pdftohtml" on pdf files

use_tnef = False # True = use "tnef" command on winmail.dat

headers_to_delete = [] # prefixes of headers to delete from all
# messages, in case you use Mutt's "Edit Message" on notes to self
# e.g. headers_to_delete = ["X-MS","X-Microsoft"]
# (note however that extra_rules and spam detection runs first)

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
    # notification in newmail_directory, e.g. "*boxname"

    # For saving to local maildir instead of IMAP, set
    # folder name to ("maildir","path/to/maildir")
    # or to skip newmail_directory notification also,
    # set it to ("*","maildir","path/to/maildir")
    
]

def extra_rules(message_as_string): return False
# you can override this to any function you want, which
# returns the name of a folder (with or without a *), or
# None to delete the message, or False = no decision,
# or ("maildir","path/to/maildir") or ("*","maildir"...)
catch_extraRules_errors = True

def handle_authenticated_message(subject,firstPart,attach):
    return False
# - you can override this to any function you want, which
# does anything you want in response to messages that are
# SSL-authenticated as coming from yourself (see below).
# Returns the name of a folder (or maildir as above), or
# None to delete the message, or False = undecided (normal
# rules will apply, except spamprobe will be bypassed).
# If folder name starts with *, mail will be marked 'seen'.
# firstPart is a UTF-8 copy of the first part of the body
# (which will typically contain plain text even if you
# were using an HTML mailer); subject is also UTF-8 coded.
# attach is a dictionary of filename:contents.
# Note: although we do check for SSL authentication, you
# are advised not to give too much "power" to authenticated
# messages (e.g. don't let them run arbitrary shell commands)
# in case your configuration does end up with a loophole
# or a trusted IMAP server gets compromised.  The expected
# use of handle_authenticated_message is to save it in a
# folder it specifies, or add something to a database, or
# trigger a preconfigured build script, etc.
trusted_domain = None # or e.g. ".example.org" specifying
# the domain of "our" network whose Received headers we
# can trust for SMTPS authentication (below).  You may
# also set it to a list of strings, e.g.
# trusted_domain=["example.net","example.org"]
# in which case you might want to add IP addresses to the
# list if one of your machines fails to do reverse-DNS to
# the other one on its Received header (but domain names
# must also be provided on this list).
# Including a blank ("") entry causes "Received" headers
# that do not sperify a "from" to not interrupt the scan
# for trusted Received headers (some IMAP networks have
# one of those first, but use with caution).
smtps_auth = None # or e.g. " with esmtpsa (LOGIN:me)"
# - if a Received header generated by your trusted domain
# (and listed before any untrusted headers) contains this
# string, the message is considered authentically from you
# (this string should be generated by your network only if
# you really did authenticate over HTTPS).  You may also
# set smtps_auth to a list of strings, any one of which is
# acceptable, e.g. smtps_auth=["esmtpsa (LOGIN:me)","esmtpsa (PLAIN:me)"]
# If any item starts "from " then the next word is assumed to
# be a user ID that is trusted if the domain reports it as a
# local delivery (no IP address).
# Note: if trusted_domain and smtps_auth is set, any message
# that does NOT contain any Received headers will be assumed
# to be generated from your own account and therefore treated
# as though it had been authenticated by smtps_auth (which
# might be useful for using --multinote with the real inbox).
# You should therefore ensure that your local network ALWAYS
# adds at least one Received header to incoming mail.

# If handle_authenticated_message needs to send other mail
# via SMTP, it can call
# send_mail(to,subject_u8,txt,attachment_filenames=[],copyself=True)
# if the following SMTP options are set:
smtp_fromHeader = "Example Name <example@example.org>"
smtp_fromAddr = "example@example.org"
smtp_host = "localhost"
smtp_user = ""
smtp_password = "" # or e.g. ("oauth2 cmd",3600)
smtp_delay = 60 # seconds between each message
# (These smtp_ settings are not currently used by anything
# except user-supplied handle_authenticated_message functions)

rewrite_return_path_SRS=True # to undo the Sender Rewriting Scheme
# in the Return-Path: you might want this if you rely on
# Return-Path in extra rules and you want to be able to port
# them to be behind a different forwarder

spamprobe_command = "spamprobe -H all" # (or = None)
spam_folder = "spam"
# you can also set this to a local maildir: ("maildir","path/to/spam")

spamprobe_remove_images = True # work around a bug in some
# versions of spamprobe that causes them to crash when an
# image is present in the email to be tested

poll_interval = 4*60
# Note: set poll_interval=False if you want just one run,
# or poll_interval="idle" to use imap's IDLE command (this
# requires the imaplib2 module; you can add to sys.path from
# imapfix_config.py if you have it in your home directory).
# imaplib2 writes debug information to the console unless
# run with python -O; to suppress this, do
# sed -e s/__debug__/False/g < imaplib2.py > i && mv i imaplib2.py

logout_before_sleep = False # suggest set to True if using
# a long poll_interval (not "idle"), or if
# filtered_inbox=None, or if the server can't take more
# than one connection at a time

midnight_command = None
# or, midnight_command = "system command to run at midnight"
# (useful if you don't have crontab access on the machine)

calendar_file = None # set to run 'calendar' command on it
# and send output lines as messages

postponed_foldercheck = False
# if True, check for folders named YYYY-MM-DD according to
# the current date, and, if any are found, move their mail
# into filtered_inbox, updating Date lines (but inserting
# the original date into the message body in case it's
# needed for attribution in quoted replies, unless the
# message is from --note or --multinote below). This is so
# you can postpone a message for handling later, simply by
# saving it into a folder named according to the date you
# want to see it, in YYYY-MM-DD format.  The check is made
# after midnight for the new date, and on startup for all
# previous dates (in case imapfix hadn't been run every day).
# Additionally, messages that are SSL-authenticated as coming
# from yourself, and whose subject lines start with a date in
# YYYY-MM-DD format, will be saved into a folder of that name
# (with the date removed from the subject line to save screen space).

postponed_daynames = False
# If True, similar to postponed_foldercheck above, but checks
# for lower-case abbreviated month and weekday names
# (e.g. mon, tue, jan, feb - the current locale is used, so
# if you want non-English names then set a different locale).
# This check is performed after midnight, but not on startup
# because they're not absolute dates.  To avoid
# false positives, any use of these at the start of
# self-written Subject lines must be followed by : if
# anything else is on the line, e.g. mon: things to do today.
# You can set postponed_foldercheck and postponed_daynames in
# any combination.

postponed_maildir = None # or "path/to/maildir", will
# result in the above postponed_ options checking
# subfolders of this maildir as well as the IMAP server,
# and authenticated messages for postponing being written
# to subfolders of this maildir instead of the server

quiet = True # False = print messages (including quota)
# If you set quiet = 2, will be quiet if and only if the
# standand output is not connected to a terminal

maildirs_to_imap = None # or path to a local directory of
# maildirs; messages will be moved to their corresponding
# folders on IMAP (renaming inbox to filtered_inbox
# and spam to spam_folder, and converting character sets)
maildir_colon = ':'
maildir_delete_emacs_backup_files = True # in case need to
# edit any (e.g. postponed notes) directly in maildir

maildir_dedot = None # or path to a local directory of
# maildirs: any non-symlink Maildir++ "dot" folders
# in it will be moved to non-"dot" folders.  Use if
# sharing e.g. local mutt with Dovecot

imap_to_maildirs = None # or path to a local directory of
# maildirs; messages will be moved from IMAP folders to
# subfolders of these maildirs, converting character sets,
# except for filtered_inbox and spam_folder if these are
# on IMAP.  If you're using the 'postponed' options, you
# should set postponed_maildir above to the same value as
# imap_to_maildirs.

imap_maildir_exceptions = [] # or list folders like Drafts
# that should not be moved to maildirs

sync_command = None # or command to run after every cycle,
# e.g. "mbsync -a" or "~/.local/bin/offlineimap" if you
# want to maintain maildirs + remote IMAP folders in same state
# (if poll_interval is "idle" this can wait for the next
# change on the _remote_ side before it runs)

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
# Used as a destination folder for maildir_to_copyself
# and/or copyself_delete_attachments, etc.
# (I call it "copyself" because I first used email on a
# local-area network in 1995 with Pegasus Mail for DOS,
# which saved "copies to self" in "copyself.pmi";
# nowadays "sent" or "sent items" seems more common for
# new setups.)
# If you want to keep this on a local maildir instead, you
# can set it to ("maildir","path/to/maildir")
# (in which case also setting maildir_to_copyself will
# result in messages simply being moved from one maildir to
# another, but with copyself_delete_attachments still applied)

copyself_alt_folder = None # or the name of an IMAP
# folder, any messages found (if folder exists) will be
# moved to copyself_folder_name, with their attachments
# deleted if copyself_delete_attachments is True.  You can
# specify more than one folder by separating them with a
# comma.  Might be useful if some of your IMAP programs
# insist on doing their own sent-mail filing to folders of
# their own choice rather than yours.
check_copyself_alt_folder_on_secondary_too = False
# (see secondary_imap below)
auto_delete_folder = None # or "Trash" if you want everything
# in it to be automatically deleted periodically; useful if
# your IMAP client insists on moving messages there when you
# wanted them deleted permanently; use with caution

archive_path = "oldmail"
archive_rules = [
    # These rules are used when you run with --archive
    # Each rule is: ("folder-name", max-age (days), spamprobe-action)
    # If max-age is not None, older messages will be archived (so you can set it to 0 to archive all messages).  Independently of this, spamprobe-action (if specified) will be run on all messages.
    # Folder name can be ("maildir","path/to/maildir") if
    # you also want to archive from local maildirs to mbox
    ("spam-confirmed", 30, "train-spam"),
    ("some-folder", 90, None),
    ("some-other-folder", None, "train-good"),
    ]
compression = "bz2" # or "gz" or None
archived_attachments_path = "archived-attachments" # or None
save_attachments_for_confirmed_spam_too = False
attachment_filename_maxlen = 30

train_spamprobe_nightly = False # if true, will also run
# spamprobe training commands on yesterday's messages in
# these folders every midnight, not just during --archive,
# to catch any message-filing done the previous day

additional_inbox = None
# If you're using an IMAP server that runs its own spam
# filtering, but you want to replace this with yours, you
# can set additional_inbox to their spam folder to treat
# their spam folder as an extra inbox to be reclassified.
# Make sure additional_inbox does not equal spam_folder.
# Alternatively, you can leave additional_inbox at None
# and set spam_folder to match their spam folder to have
# 'or'-logic spam detection, but then you'd have to make
# any manual reviews / saves to spam-confirmed are done
# on the timetable set by the IMAP server (typically
# every 30 days will suffice), plus it may help to keep
# spam-confirmed off-IMAP to avoid accidentally telling
# their system that these messages are non-spam for you.

additional_inbox_train_spam = False # setting this
# to True is another way to get the 'or'-logic if you'd
# rather keep all spam elsewhere e.g. spam_folder is a
# local maildir.  header_rules and extra_rules still
# override this.

check_additional_inbox_on_secondary_too = False
# (see secondary_imap below)

additional_inbox_might_not_exist = False # set to True if
# the folder does not appear when it's empty, in which
# case folder not existing will not be treated as an error

forced_names = {} # you can set this to a dictionary
# mapping email address to From name, and whatever other
# From name is used will be replaced by the one specified;
# this is for when one of your contacts has their "From"
# name set to something confusing like their ISP's name

important_regexps = [
    # List here any regular expressions that will result in
    # the "Importance" flag of a message being set.  If the
    # list is empty then Importance is unchanged.
    # The default rule here marks as 'important' any message
    # that seems to include a phone number, as an aid to
    # quickly finding these when processing email on a phone
    # (if you'd rather call than type and would therefore
    # like to find messages that contain phone numbers)
    r"0(?:\s*[0-9]){10}",
    ]

# Set secondary_imap_hostname if you also want to check
# some other IMAP server and treat its messages as being
# in the inbox of the main server (i.e. copied over and
# processed as normal).  You can check this less often by
# setting secondary_imap_delay.  (Will NOT stay logged in
# between checks.)  It's also possible to set the first
# three of these options to lists, in order to check
# multiple secondary IMAP servers or multiple identities.
secondary_imap_hostname = "" # host or host:port
secondary_imap_username = "me"
secondary_imap_password = "xxxxxxxx"
secondary_imap_delay = 24 * 3600

report_secondary_login_failures = False # if True, put a
# message in filtered_inbox about any login failures for
# any of the secondary_imap boxes (default just ignores &
# tries again next time)

secondary_is_insecure = False # if True, the --copy option
# will remove all email addresses (but not names) when
# copying to secondary.  This is for when the secondary
# IMAP server is easier to log in to than the primary, but
# is less secure.  E.g. your old WM6.5 phone can't do the
# modern TLS version of IMAPS, and the only other option
# is a completely unencrypted connection to some throwaway
# account somewhere.  Using --copy to copy over messages
# to read on that phone, but with secondary_is_insecure as
# True, will mean anyone who breaks into that throwaway
# account can see the messages but won't easily be able to
# reply to them for scamming purposes.  It will of course
# mean you can't reply so easily as well, but the idea is
# that the throwaway account is only for READING messages
# on the mobile, not for actual replying or management.

first_secondary_is_copy_only = False # if True, the first
# server listed in secondary will be used ONLY for --copy
# and not for periodic checking.

secLimit = 99999 # max number of bytes checked for email
# addresses by secondary_is_insecure (to prevent holdups
# if you have multi-megabyte attachments)

insecure_login = [] # set to a list of host names (or host:port)
# not expected to support SSL.  This speeds things up by
# trying the non-SSL login first on those hosts.  See also
# secondary_is_insecure option above.

exit_if_imapfix_config_py_changes = False # if True, does
# what it says, on the assumption that a wrapper script
# will restart it (TODO: make it restart by itself?)
# - and if this is set to the special value "stamp", it
# will additionally try to update the timestamp of the
# config file before starting, so that any other instance
# (even on another machine in a cluster) will stop; this
# can be more reliable than exit_if_other_running below
# if running on a cluster.

failed_address_to_subject = True # try to rewrite delivery
# failure reports so that failed addresses are included in
# the Subject line and are therefore visible from a table
# of subjects without having to go in to the message.
# Not all delivery failure reports can be adjusted in this
# way; it depends on how the bouncing relay formats them.

imap_8bit = False # set to True if your IMAP server & clients
# will accept raw 8-bit UTF-8 strings in message bodies (but
# this is not universal, so make sure it re-encodes as MIME
# when forwarding messages to others).  Raw UTF-8 messages
# (if supported) save a little bandwidth and allow characters
# to be more readily displayed in Mutt's "Edit Message" etc.
archive_8bit = False # similar if you want --archive as 8bit

exit_if_other_running = True # when run without options,
# try to detect if another no-options imapfix is running
# as the same user, and exit if so.  Not guaranteed (for
# example, it can't protect against instances being run on
# different machines of a cluster), but might help to
# reduce the build-up of processes if there is a runaway
# situation with whatever you're using to start them.
# Multiple imapfix instances are sort-of OK but may lead
# to messages being processed in duplicate and/or load the
# IMAP server too much; on the other hand lock files etc
# can have the problem of 'stale' locks.  At least a limit
# of 1 process per server in the cluster is better than no
# limit at all.  On the other hand you might want to set
# this to False if you run different instances of imapfix
# with different configuration files as the same user and
# don't want to rename (or symlink) imapfix so that these
# look different in the process table.
# (exit_if_other_running needs the Unix 'ps' command.)
# The newer exit_if_imapfix_config_py_changes="stamp"
# option (above) is likely better if you don't mind
# changing the timestamp of your imapfix_config.py.

alarm_delay = 0 # with some Unix networked filesystems it is
# possible for imapfix or one of its subprocesses to get
# "stuck" - if this happens, set alarm_delay to a number of
# seconds (preferably thousands) after which to terminate the
# process using the Unix "alarm clock" mechanism.  The clock
# will be reset every half that number of seconds if imapfix
# is still functioning.  Note that a long-running filter etc
# could also cause imapfix to become "stuck" this long.

# Command-line options
# --------------------

# Run with no options = process mail as normal

# Run with --once = as if poll_interval=False

# Run with --quicksearch (search string) to search both
# archive_path and the server (all folders), but "quick"
# in that it doesn't decode MIME attachments etc
# (TODO: implement more thorough search, with regexps, but
# it would have to download all messages from the server)
# TODO: this does not yet search local maildirs

# Run with --delete (folder name) to delete a folder
# --delete-secondary to do it on secondary_imap_hostname
# (if there's more than one secondary, the first is used)

# --create (folder name) to create an empty folder
# (e.g. "Sent", some Android apps e.g. K-9 Mail require the
# folder to already exist before they can save messages to it
# (if the folder has been deleted, to get the functionality
# back do Manage folders / Refresh folder list, and Account
# Settings / Folders / Sent folder - set it to Sent)
# --create-secondary to do this on secondary_imap_hostname

# Run with --backup to take a full backup of ALL folders to local .mbox files
# without separating off attachments.  Use this for example if your account is
# about to be cancelled and you want to be able to restore things as-is after
# reinstatement or migration to a new service, Read/Answered flags preserved.

# Run with --copy (folder name) to copy a folder onto secondary_imap_hostname
# (updating any that already exists of that name: may delete
# messages on secondary_imap_hostname that aren't on the primary;
# 1st secondary is used if there's a list of many)

# Run with --note (subject) to put a note to yourself
# (taken from standard input) directly into filtered_inbox
# - useful from scripts etc (you can get the note without
# having to wait for it to go through SMTP and polling).
# If filtered_inbox is None, --note uses real inbox,
# or use --note-inbox for the same effect.
# Run with --htmlnote to do the same but send as HTML.
# Run with --maybenote to do --note only if standard input
# has text (no mail left if your script printed nothing).
# Use --from=X to override the From name to X for notes
# (quote it for the shell if it's more than one word)

# Run with --multinote (files) to transfer a group of text
# files into filtered_inbox notes.  The first line of each
# file is the subject line of the note.  Files will be
# deleted after being successfully uploaded to IMAP.
# Directories are processed recursively but not deleted.
# Backup files (with names ending ~) are deleted without
# being uploaded to IMAP.
# If handle_authenticated_message has been redefined, this
# will be called as well when using --multinote.  (If you
# are using this function on a machine that is different
# from the one that does your mail processing, you may
# want to define handle_authenticated_message to
# return "" which will result in the messages being placed
# in the real inbox for processing by the other machine.
# Alternatively you can use --multinote-inbox for the same effect.)
# Use --multinote-fname (files) to use each file's filename
# instead of its first line as the subject, or --multinote-inbox-fname.

# All note options assume that any non-ASCII characters in
# the input will be encoded as UTF-8.

# Run with --upload (files) to upload as attachments into
# filtered_inbox messages, e.g. for transfer to a mobile
# (likely more efficient than SMTP and bypasses filtering)
# - recurses into directories if specified; won't delete
# files after uploading.

# End of options - non-developers can stop reading now :)
# -------------------------------------------------------

# CHANGES
# -------
# If you want to compare this code to old versions, most old
# versions are being kept on SourceForge's E-GuideDog SVN repository
# http://sourceforge.net/p/e-guidedog/code/HEAD/tree/ssb22/setup/
# use: svn co http://svn.code.sf.net/p/e-guidedog/code/ssb22/setup
# and on GitHub at https://github.com/ssb22/web-imap-etc
# and on GitLab at https://gitlab.com/ssb22/web-imap-etc
# and on Bitbucket https://bitbucket.org/ssb22/web-imap-etc
# and at https://gitlab.developers.cam.ac.uk/ssb22/web-imap-etc
# and in China: https://gitee.com/ssb22/web-imap-etc

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from imapfix_config import *
import email,email.utils,time,os,sys,re,base64,quopri,mailbox,traceback,mimetypes
if not sys.version_info[0]==2:
    print ("ERROR: ImapFix is a Python 2 program and should be run with 'python2'.\nIt needs major revision for Python 3's version of the email library.\nTry compiling Python 2.7 in your home directory if it's no longer installed on your system.")
    # In particular, Python 3.3+ revised the Message class into an EmailMessage class (with Message as a compatibility option), need to use as_bytes rather than as_string; set_payload available only in compatibility mode and works in Python3 Unicode-strings so we'd need to figure out how to handle other charsets including invalid coding.
    # That's on top of the usual 'make sure all our code works whether or not type("")==type(u"")' issue.
    sys.exit(1)
from email import encoders
from cStringIO import StringIO
if poll_interval=="idle":
    import imaplib2 as imaplib
    assert not logout_before_sleep, "Can't logout_before_sleep when poll_interval==\"idle\""
else: import imaplib
assert not secondary_imap_delay=="idle", "'idle' polling not implemented for secondary"

if filtered_inbox==None: spamprobe_command = None

if compression=="bz2":
    import bz2
    compression_ext = ".bz2"
elif compression=="gz":
    import gzip
    compression_ext = ".gz"
else: compression_ext = ""

if image_size:
    from PIL import Image
    import imghdr

import commands

def debug(*args):
    if not quiet:
        print (reduce((lambda a,b:a+str(b)), args, ""))
    
def check_ok(r):
    "Checks that the return value of an IMAP call 'r' is OK, raises exception if not"
    typ, data = r
    if not typ=='OK': raise Exception(typ+' '+repr(data))

def spamprobe_rules(message,already_spam=False):
  if already_spam: # additional_inbox_train_spam
      run_spamprobe("train-spam",message) # might help our own classifier to spot other features that weren't what the IMAP server's classifier picked up on (as long as we train-good if it wasn't)
      return spam_folder # (if JUST doing this, rename additional_inbox_train_spam to additional_inbox_direct_to_spam or something)
  elif run_spamprobe("train",message).startswith("SPAM"): return spam_folder # "train" = classify + maybe update database if wasn't already confident ("receive" = always update database)
  else: return filtered_inbox

def run_spamprobe(action,message):
  if not spamprobe_command: return ""
  if spamprobe_remove_images:
      msg = email.message_from_string(message)
      if delete_images(msg):
          message=myAsString(msg)
  cIn, cOut = os.popen2(spamprobe_command+" "+action)
  cIn.write(message); cIn.close()
  return cOut.read()

def spamprobe_cleanup():
    if not spamprobe_command: return
    debug("spamprobe cleanup")
    os.system(spamprobe_command+" cleanup")

def process_header_rules(header):
  for box,matchList in header_rules:
    for headerLine in header.split("\n"):
      for m in matchList:
        i=re.finditer(m,headerLine.rstrip())
        try: i.next()
        except StopIteration: continue
        if box:
            if box[0]=='*': box=box[1:] # just save it without indication
            elif newmail_directory:
                if type(box)==tuple: bStr=re.sub(".*/","",box[1])
                else: bStr = box
                open(newmail_directory+os.sep+bStr,'a')
        return rename_folder(box)
  return False

def myAsString(msg):
    message = msg.as_string()
    if not "\r" in message: message=message.replace("\n","\r\n") # in case it came in from Maildir and the library didn't add the CRs back in
    if not "\r\n\r\n" in message or ("\n\n" in message and message.index("\n\n")<message.index("\r\n\r\n")):
        # oops, broken library?
        message=message.replace("\n\n","\r\n\r\n",1)
        a,b = message.split("\r\n\r\n",1)
        message = re.sub('\r*\n','\r\n',a)+"\r\n\r\n"+b
    # Bug in python2.7/email/header.py: CRLF + whitespace sometimes added by _split_ascii after semicolons or commas, but if this occurs inside quoted-printable strings it'll break the display in some versions of alpine & mutt (RFC 2822 says CRLF + whitespace is interpreted as whitespace, and that's not allowed inside ?=..?= sections)
    a,b = message.split("\r\n\r\n",1)
    message = re.sub(header_charset_regex,lambda x:re.sub(r"\s_","_",re.sub("\r\n\s","",x.group())),a,flags=re.DOTALL)+"\r\n\r\n"+b
    return message
def headers(msg):
    # some Python libraries buggy, so do it ourselves
    return set(l.split(None,1)[0][:-1] for l in myAsString(msg).split("\r\n\r\n",1)[0].split("\n") if l and l[0].strip())

imapfix_name = sys.argv[0]
if os.sep in imapfix_name: imapfix_name=imapfix_name[imapfix_name.rindex(os.sep)+1:]
if not imapfix_name: imapfix_name = "imapfix.py"
from_name = imapfix_name
for i in range(1,len(sys.argv)):
    if sys.argv[i].startswith('--from='):
        from_name = sys.argv[i][len('--from='):]
        del sys.argv[i] ; break
try: _a,_b = imapfix_name.split('.',1)
except: _a,_b = imapfix_name,'0'
from_addr = " <%s@%s>" % (_a,_b) # (the part that doesn't change under --from=)
from_line = from_name+from_addr # previously just imapfix_name, but K-9 Mail Version 5.8 started to require this to be formatted with an @ or it would just say "Unknown Sender"; imapfix 1.76+ supports any name before the address
del _a,_b

def postponed_match(subject):
    if postponed_foldercheck:
        m = re.match(isoDate,subject)
        if m and m.group() >= isoToday(): return m.end() # TODO: Y10K (lexicographic comparison)
    if postponed_daynames:
        m = re.match(weekMonth,subject)
        if m: return m.end()

def authenticated_wrapper(subject,firstPart,attach={}):
    subject = subject.replace('\n',' ').replace('\r','') # in case the original header is corrupt (c.f. globalise_charsets)
    mLen = postponed_match(subject)
    if mLen:
        newSubj = re.sub("^:","",subject[mLen:]).lstrip() # take the date itself out of the subject line before putting the message in that folder: it could take up valuable screen real-estate in summaries on large-print or mobile devices, and just duplicates information that can be found in the folder name (or in the Date: field after it's put back into filtered_inbox)
        if not newSubj: # oops, subject contained only the date and nothing else: take from 1st line of text instead
            newSubj = firstPart.lstrip().split('\n')[0]
            if len(newSubj) > 60: newSubj = newSubj[:57] + "..." # TODO: configurable abbreviation length?
        if postponed_maildir: box=('maildir',postponed_maildir+os.sep+subject[:mLen])
        else: box=subject[:mLen] # don't resolve weekday/month names to a date here, because user might actually rely on the "doesn't check for past days on startup" behaviour to postpone to after a trip or something
        return box, newSubj
    try: r=handle_authenticated_message(subject,firstPart,attach)
    except:
        if not catch_extraRules_errors: raise # TODO: document it's also catch_authMsg_errors, or have another variable for that
        o = StringIO() ; traceback.print_exc(None,o)
        save_to(filtered_inbox,"From: "+from_line+"\r\nSubject: imapfix_config exception in handle_authenticated_message, treating it as return False\r\nDate: %s\r\n\r\n%s\n" % (email.utils.formatdate(localtime=True),o.getvalue()))
        r=False
    return r, None

def yield_all_messages(searchQuery=None,since=None):
    "Generator giving (message ID, flags, message) for each message in the current folder of 'imap', without setting the 'seen' flag as a side effect.  Optional searchQuery limits to a text search."
    if searchQuery: typ, data = imap.search(None, 'TEXT', '"'+searchQuery.replace("\\","\\\\").replace('"',r'\"')+'"')
    elif since: typ, data = imap.search(None, 'SINCE', since)
    else: typ, data = imap.search(None, 'ALL')
    if not typ=='OK': raise Exception(typ)
    bodyPeek_works = True # will set to False if it doesn't
    dList = data[0].split(); count = 1
    lastTime = time.time()
    for msgID in dList:
        if not quiet and time.time() > lastTime + 2:
            sys.stdout.write("  %d%%\r" % (100*count/len(dList))) ; sys.stdout.flush()
            lastTime = time.time()
        count += 1
        typ, data = imap.fetch(msgID, '(FLAGS)')
        if not typ=='OK': continue
        flags = data[0]
        if not flags: flags = ""
        if '\\Deleted' in flags: continue # we don't mark messages deleted until they're processed; if imapfix was interrupted in the middle of a run, then don't process this message a second time
        if '(' in flags: flags=flags[flags.rindex('('):flags.index(')')+1] # so it's suitable for imap.store below
        if bodyPeek_works:
            typ, data = imap.fetch(msgID, '(BODY.PEEK[])')
            if not typ=='OK': bodyPeek_works = False
        if not bodyPeek_works: # fall back to older RFC822:
            typ, data = imap.fetch(msgID, '(RFC822)')
            if not "seen" in flags.lower(): # fetching RFC822 will set 'seen' flag, so we'll need to clear it again
                try: imap.store(msgID, 'FLAGS', flags)
                except: imap.store(msgID, 'FLAGS', "()") # gmail can give a \Recent flag but not accept setting it
        if not typ=='OK': continue
        try: yield msgID, flags, data[0][1] # data[0][0] is e.g. '1 (RFC822 {1015}'
        except: continue # data==None or data[0]==None

def rewrite_deliveryfail(msg):
    if not failed_address_to_subject: return
    subj = msg.get("Subject","")
    if not subj.lower().startswith("mail delivery") or not msg.get("From","").lower().startswith("mail delivery"): return
    fr = msg.get("X-Failed-Recipients","")
    if not fr: return
    del msg['Subject'] ; msg['Subject']=fr+' '+subj
    return True

for k in forced_names.keys():
    if not k==k.lower():
        forced_names[k.lower()]=forced_names[k]
        del forced_names[k]
def forced_from(msg):
    def f(fr):
        if fr.lower() in forced_names:
            del msg['From']
            msg["From"] = forced_names[fr.lower()] + ' <'+fr.lower()+'>'
            return True
    fr = msg.get("From","").strip()
    if f(fr): return True
    if fr.endswith('>') and '<' in fr and f(fr[fr.rindex('<')+1:-1]): return True
    # TODO: any other formats to check?

def quote_display_name_if_needed(msg):
    # 'From: Testing @ ZOE COVID Study <...>'
    # gave 'Unknown Sender' in K9, please quote it
    def ensureQuoted(dnMatch):
        displayName = dnMatch.group()
        if re.match("^[A-Za-z0-9 .]*$",displayName):
            # should be OK to leave unchanged if it didn't use @ etc
            return displayName
        else: return '"'+displayName+'"'
    f = msg.get("From","").strip()
    f2 = re.sub(r'^[^<"]*(?= <[^>]*>$)',ensureQuoted,f)
    if not f==f2:
        del msg['From'] ; msg['From'] = f2 ; return True

def body_text(msg):
    "Returns a representation of the message's body text (all parts), for rules"
    if msg.is_multipart(): return "\n".join(body_text(p) for p in msg.get_payload())
    if not msg.get_content_type().startswith("text/"): return ""
    return msg.get_payload(decode=True).strip()

def rewrite_importance(msg):
    if not important_regexps: return
    changed = False
    for h in ['Priority', # e.g. Urgent
              'X-Priority', # 1 is highest
              'X-MSMail-Priority', # e.g. High
              'Importance']: # e.g. High; clients that recognise the previous 3 tend to recognise this one as well, and other clients recognise only this one, so we'll clear all but set only this one
        if h in msg:
            del msg[h] ; changed = True
    bTxt = body_text(msg)
    for r in important_regexps:
        if re.search(r,bTxt):
            msg['Importance'] = 'High'; changed=True; break
    return changed

def rewrite_return_path(msg):
    if not rewrite_return_path_SRS or not 'Return-Path' in msg: return
    rp = msg["Return-Path"]
    rp2 = re.sub(r"(?i)^<SRS(?:0|(?:1.*=))=[0-9a-z]+=[0-9a-z]+=([^=]+)=([^@]+)@.*$",r"\2@\1",rp)
    if not rp==rp2:
        del msg["Return-Path"]
        msg["Return-Path"] = rp2 ; return True

def process_imap_inbox():
  make_sure_logged_in()
  doneSomething = True
  while doneSomething:
   doneSomething = False # if we do something on 1st loop, we'll loop again before handing control back to the delay or IMAP-event wait.  This is to catch the case where new mail comes in WHILE we are processing the last batch of mail (e.g. another imapfix is running with --multinote and some of the processing calls send_mail() with a callSMTP_time delay: we don't want the rest of the notes to be delayed 29 minutes for the next IMAP-wait to time out)
   for is_additional in [False,True]:
    if is_additional:
        if not additional_inbox: break
        if additional_inbox_might_not_exist:
            typ, data = imap.select(additional_inbox)
            if not typ=='OK': break
        else: check_ok(imap.select(additional_inbox))
    else: check_ok(imap.select()) # the inbox
    imapMsgid = None ; newMail = False
    for msgID,flags,message in yield_all_messages():
        if not is_additional and leave_note_in_inbox and imap==saveImap and isImapfixNote(message):
            if imapMsgid: # somehow ended up with 2, delete one
                imap.store(imapMsgid, '+FLAGS', '\\Deleted')
            imapMsgid = msgID ; continue
        doneSomething = True
        msg = email.message_from_string(message)
        box = changed = bypass_spamprobe = False ; seenFlag=""
        if authenticates(msg):
          # do auth'd-msgs processing before any convert-to-attachment etc
          debug("Message authenticates")
          bypass_spamprobe = True
          box,newSubj = authenticated_wrapper(re.sub(header_charset_regex,header_to_u8,msg.get("Subject",""),flags=re.DOTALL),getFirstPart(msg).lstrip(),get_attachments(msg))
          if newSubj: # for postponed_foldercheck
            del msg["Subject"]
            msg["Subject"] = utf8_to_header(newSubj)
            changed = True
          if box and box[0]=='*':
              box=box[1:] ; seenFlag="\\Seen"
        if not box==None:
         # globalise charsets BEFORE the filtering rules
         # (especially if they've been developed based on
         # post-charset-conversion saved messages) - but
         # no point doing preview images or Office
         # conversions for spam or to-delete messages
         changed = globalise_charsets(msg,imap_8bit) or changed
         changed = remove_blank_inline_parts(msg) or changed
         changed = rewrite_deliveryfail(msg) or changed
         changed = forced_from(msg) or changed
         changed = quote_display_name_if_needed(msg) or changed
         changed = rewrite_importance(msg) or changed
         changed = rewrite_return_path(msg) or changed
         if max_size_of_first_part and size_of_first_part(msg) > max_size_of_first_part: msg,changed = turn_into_attachment(msg),True
         if changed: message = myAsString(msg)
         changed0 = changed # for change_message_id
         if box==False:
          header = message[:message.find("\r\n\r\n")]
          box = process_header_rules(header)
          if box==False:
            try: box = rename_folder(extra_rules(message))
            except:
                if not catch_extraRules_errors: raise
                o = StringIO() ; traceback.print_exc(None,o)
                save_to(filtered_inbox,"From: "+from_line+"\r\nSubject: imapfix_config exception in extra_rules (message has been saved to '%s')\r\nDate: %s\r\n\r\n%s\n" % (filtered_inbox,email.utils.formatdate(localtime=True),o.getvalue()))
                box = filtered_inbox
            if box==False:
                if bypass_spamprobe: box = filtered_inbox
                else: box = spamprobe_rules(message,is_additional and additional_inbox_train_spam)
        if box:
            if not box==spam_folder:
                if headers_to_delete and delete_headers(msg):
                    changed0 = changed = True # for change_message_id
                    added = True # so myAsString happens
                else: added = False
                if use_tnef: added = add_tnef(msg) or added
                if image_size: added = add_previews(msg) or added
                if office_convert: added = add_office(msg) or added
                if pdf_convert: added = add_pdf(msg) or added
                changed = added or changed # don't need to alter changed0 here, since if the only change is adding parts then change_message_id does not need to take effect (at least, not with Gmail January 2022)
                if added: message = myAsString(msg)
            if seenFlag: copyWorked = False # unless we can get copy_to to set the Seen flag on the copy, which means the IMAP server must have an extension that causes COPY to return the new ID unless we want to search for it
            elif type(box)==tuple: copyWorked = False # e.g. imap to maildir
            elif not changed and saveImap == imap and (not imap_to_maildirs or box in imap_maildir_exceptions):
                debug("Copying unchanged message to ",box)
                copyWorked = copy_to(box, msgID)
                if not copyWorked: debug("... failed; falling back to re-upload")
            else: copyWorked = False
            if not copyWorked:
                debug("Saving message to ",box)
                try: save_to(box, message, seenFlag, changed0 and saveImap==imap)
                except: # uh-oh
                    debug("Save FAIL: writing error and halting")
                    save_to(filtered_inbox,"From: "+from_line+"\r\nSubject: imapfix save error, HALTED\r\nDate: %s\r\n\r\nsave_to(%s) FAILED.\nThis can happen when you have quota issues with a very large message.\nFor safety, imapfix will now HALT processing.\nYou should terminate pid %s once you've sorted out the inbox.\n" % (email.utils.formatdate(localtime=True),box,str(os.getpid()))) # TODO: could try saving without attachments and quarantine the attachments somewhere; could try leaving it as 'seen' and checking for 'seen' on future loop iterations
                    imap.expunge() # the ones we did before this
                    make_sure_logged_out()
                    if sync_command: os.system(sync_command)
                    while True: time.sleep(60)
            if box==filtered_inbox: newMail = True
        else: debug("Deleting message")
        imap.store(msgID, '+FLAGS', '\\Deleted')
    if not is_additional and leave_note_in_inbox and imap==saveImap:
      if newMail:
        if imapMsgid: # delete the old one
            imap.store(imapMsgid, '+FLAGS', '\\Deleted')
        save_to("", imapfixNote())
      elif imapMsgid:
        # un-"seen" it (in case the IMAP server treats our fetching it as "seen"); TODO what if the client really read it but didn't delete?
        imap.store(imapMsgid, '-FLAGS', '\\Seen')
    check_ok(imap.expunge())
  if (not quiet) and imap==saveImap and not type(filtered_inbox)==tuple: debug("Quota ",repr(imap.getquotaroot(filtered_inbox)[1])) # RFC 2087 "All mailboxes that share the same named quota root share the resource limits of the quota root" - so if the IMAP server has been set up in a typical way with just one limit, this command should print the current and max values for that shared limit.  (STORAGE = size in Kb, MESSAGE = number)

def authenticates(msg):
    if not trusted_domain or not smtps_auth: return
    rxd = msg.get_all("Received",[])
    if not rxd: return True # no Received headers = put in by imapfix on another machine
    for rx in rxd:
      rx = re.sub(r'\s+',' ',rx)
      m=re.match(r"from ([^ ]+)( \([^)]*\))* by ([^ ]+)( .*)",rx) # RFC 2821 section 4.4 extended a bit (not everybody follows this, but trusting the machines on our network implies trusting they'll follow at least this regex and cannot be tricked into not doing so)
      if not m:
          # we can't process this one, but should it break the chain?
          if type(trusted_domain)==list and "" in trusted_domain:
              # option is set: non-"from" rx header doesn't interrupt scan
              continue
          else: break # if in doubt, don't trust this message
      claimed_from, tcp_from_and_other, receiving_machine, other = m.groups()
      # The identity of receiving_machine is trusted by induction: if all (0 or more) previous headers were trusted to correctly report both themselves and the next hop, and if said 'next hop' reports all identified trusted networks, then we trust the claim of the receiving machine on this header.  (This implies we always trust the claim of the first such header if any trusted_domain is set.)
      if type(trusted_domain)==list:
          if not any(receiving_machine.endswith(t) for t in trusted_domain if t): break # (not on any of our networks: this normally means there will have been 0 previous headers and this message has been introduced by some other method, so don't trust it)
      elif not receiving_machine.endswith(trusted_domain): break # (as above)
      # We are trusting all machines so far never to incorrectly report an authentication.  So if THIS machine reports an authentication (wherever the message came from on previous hop) then we pass it.
      if not tcp_from_and_other: tcp_from_and_other = ""
      if not other: other = ""
      check_for_auth_info = tcp_from_and_other + other # smtps_auth has been known to occur in EITHER of these places (Postfix puts it after the TCP info; Exim puts it after the receiver in the "with" section)
      if type(smtps_auth)==list:
          if any((s in check_for_auth_info or len(s.split())==2 and s.split()[0]=="from" and s.split()[1]==claimed_from and not tcp_from_and_other) for s in smtps_auth): return True
      elif smtps_auth in check_for_auth_info or len(smtps_auth.split())==2 and smtps_auth.split()[0]=="from" and smtps_auth.split()[1]==claimed_from and not tcp_from_and_other: return True
      # Now check next-older hop.  If it is not on any of our trusted networks, then stop trusting, no matter what is claimed in further Received headers.
      # We CANNOT trust claimed_from: we MUST check the first item in tcp_from_and_other.  If any server on your network fails to put a reverse-DNS in here then the IP address of the next hop must be included in the trusted_domain list.
      m = re.match(r" \(([^)\[]*)\[([^)\]]*)\][^)]*\)",tcp_from_and_other)
      if not m: break
      reverse_dns, ip = m.groups()
      reverse_dns = reverse_dns.strip()
      if reverse_dns.endswith('.'): reverse_dns=reverse_dns[:-1] # gmail bug
      if type(trusted_domain)==list:
          if not any((reverse_dns.endswith(t) or ip==t) for t in trusted_domain if t): break
      elif not reverse_dns.endswith(trusted_domain): break

def imapfixNote(): return "From: "+from_line+"\r\nSubject: Folder "+repr(filtered_inbox)+" has new mail\r\nDate: "+email.utils.formatdate(localtime=True)+"\r\n\r\n \n" # make sure there's at least one space in the message, for some clients that don't like empty body
# (and don't put a date in the Subject line: the message's date is usually displayed anyway, and screen space might be in short supply)
def isImapfixNote(msg): return ("From: "+from_name) in msg and ("Subject: Folder "+repr(filtered_inbox)+" has new mail") in msg

def get_maildir(dirName,create=True):
    if maildir_delete_emacs_backup_files:
      for c in ['cur','new']:
        try: l=os.listdir(dirName+os.sep+c)
        except: l = []
        for f in l:
            if f.endswith('~'): tryRm(dirName+os.sep+c+os.sep+f)
    return mailbox.Maildir(dirName,None,create)

def archive(foldername, mboxpath, age, spamprobe_action):
    if not age==None:
      if spamprobe_action: extra = ", spamprobe="+spamprobe_action
      else: extra = ""
      toDbg="Archiving from "+str(foldername)+" to "+str(mboxpath)+extra+"..."
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
      toDbg = "Processing "+str(foldername)+"..."
      mbox = None
    is_maildir = type(foldername)==tuple and foldername[0]=='maildir'
    if is_maildir:
        try: maildir = get_maildir(foldername[1])
        except: return # couldn't select that folder
        debug(toDbg)
        def generator():
            for m in maildir.iteritems():
                k,v = m
                yield k,v.get_flags(),myAsString(v)
        toDel = []
    else:
        make_sure_logged_in() ; debug(toDbg)
        typ, data = imap.select(foldername)
        if not typ=='OK': return # couldn't select folder
        generator = yield_all_messages
    for msgID,flags,message in generator():
        if spamprobe_action:
            # TODO: combine multiple messages first?
            run_spamprobe(spamprobe_action, message)
        if age==None: continue
        if type(message)==type(''):
            msg = email.message_from_string(message)
        else: # maildir returns it as a Message etc
            msg,message = message,myAsString(message)
        try: t = email.utils.mktime_tz(email.utils.parsedate_tz(msg['Date']))
        except: t = time.time() # undated message or invalid date (sometimes happens in spam for example)
        if t >= time.time() - age: continue
        if not message.startswith("From "): # needed for Unix mbox, otherwise mbox lib fills it in with MAILER-DAEMON
            f = []
            if 'From' in msg:
                fr = msg['From']
                if '<' in fr and '>' in fr[fr.index('<'):]:
                    fr = fr[fr.index('<')+1:fr.rindex('>')]
                if not fr: fr = 'unknown'
                f.append(fr)
                f.append(time.asctime(time.gmtime(t))) # must be THIS format for at least some versions of mutt to parse the message
                message="From "+' '.join(f)+"\r\n"+message
                msg = email.message_from_string(message)
        globalise_charsets(msg,archive_8bit) # in case wasn't done on receive (this also makes sure UTF-8 is quopri if it would be shorter, which can make archives easier to search)
        if archived_attachments_path and (save_attachments_for_confirmed_spam_too or not spamprobe_action or not "spam" in spamprobe_action): save_attachments_separately(msg)
        mbox.add(msg) # TODO: .set_flags A=answered R=read ?  (or doesn't it matter so much for old-message archiving; flags aren't always right anyway as you might have answered some using another method)
        if is_maildir: toDel.append(msgID)
        else: imap.store(msgID, '+FLAGS', '\\Deleted')
    if mbox:
        mbox.close()
        if not os.stat(mboxpath).st_size: tryRm(mboxpath) # ended up with an empty file - delete it
        else:
          if archive_8bit:
            d1 = open(mboxpath,'rb').read()
            d2 = quopri_to_u8_8bitOnly(d1) # TODO: the ENTIRE mbox in one operation? what if there's some non-MIME messages in there that just happen to contain URLs with =(hex digits) in them?
            if not d2==d1: open(mboxpath,'wb').write(d2)
          if compression:
            open_compressed(mboxpath,'wb').write(open(mboxpath,'rb').read()) # will write a .bz2 etc
            tryRm(mboxpath)
    # don't do this until got here without error:
    if is_maildir: # (don't del during iteritems)
        for msgID in toDel: del maildir[msgID]
    else: check_ok(imap.expunge())

def fix_archives_written_by_imapfix_v1_308():
    for f in listdir(archive_path):
        f = archive_path+os.sep+f
        if f.endswith(compression_ext): f2 = open_compressed(f[:-len(compression_ext)],'r')
        else: f2 = open(f)
        r = [] ; changed = False
        for l in f2:
          if l.startswith("From "):
            l2 = l.replace('<','')
            try: t = email.utils.mktime_tz(email.utils.parsedate_tz(' '.join(l2.split()[-6:])))
            except: t = None
            if t:
                l2 = ' '.join(l2.split()[:-6])+' '+time.asctime(time.gmtime(t))+'\r\n'
                r.append(l2) ; changed = True ; continue
          r.append(l)
        if changed:
          print ("Fixing "+f)
          if f.endswith(compression_ext): open_compressed(f[:-len(compression_ext)],'wb').write(''.join(r))
          else: open(f,'wb').write(''.join(r))
        else: print ("No need to fix "+f)

def get_attachments(msg):
    if msg.is_multipart():
        d = {}
        for i in msg.get_payload():
            d.update(get_attachments(i))
        return d
    try: fname = msg.get_filename()
    except: fname="illegal-filename"
    if not fname: return {}
    data = msg.get_payload(None,True)
    if data: return {fname:data}
    else: return {}

def remove_blank_inline_parts(msg):
    # some mailers send HTML-only messages with completely blank text/plain alternatives.  In this case it's best to remove the blank alternative so that a client told to prefer text can display the HTML.  TODO: document that we do this?
    if not msg.is_multipart(): return
    ll = msg.get_payload()
    i = 0 ; changed = False
    while i < len(ll):
        if (not 'Content-Type' in ll[i] or ll[i]["Content-Type"].startswith("text/")) and not ll[i].get_payload(decode=True).strip() and len(ll)>1:
            del ll[i] ; changed = True
        else: i += 1
    return changed

def save_attachments_separately(msg):
    walk_msg(msg,save_attachment_separately)
def save_attachment_separately(msg):
    try: fname = msg.get_filename()
    except: return
    if not fname: return
    if fname.startswith("imapfix-preview"): return
    if not type(fname)==type(u""):
        try: fname = fname.decode('utf-8')
        except: pass
    try: fname=fname.encode("unicode-escape").replace(r"\u","_").replace("/"," ").replace("\\"," ")
    except: fname="illegal-filename-B"
    fname = re.sub(r'\s+',' ',fname)
    if '.' in fname: fext = fname[fname.rindex('.'):]
    else: fext = ""
    fname = fname.replace(os.sep,'.')
    if len(fext) > attachment_filename_maxlen:
        fname = fname[:attachment_filename_maxlen]
    else:
        if fext: fname = fname[:-len(fext)]
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
    walk_msg(msg,delete_attachment)
def delete_attachment(msg):
    if msg.get_filename(): msg.set_payload("")

def delete_images(msg):
    return walk_msg(msg,delete_image)
def delete_image(msg):
    if msg.get("Content-Type","").startswith("image/"):
        msg.set_payload("") # empty: this is enough to stop the spamprobe crash (don't need to remove the attachment altogether)
        return True

def nightly_train(foldername, spamprobe_action):
    if type(foldername)==tuple:
        try: maildir = get_maildir(foldername[1],False)
        except: return
        timeYesterday = time.time()-24*3600
        for msgID,msg in maildir.iteritems():
            try: t = email.utils.mktime_tz(email.utils.parsedate_tz(msg['Date']))
            except: t = 0
            if t >= timeYesterday: run_spamprobe(spamprobe_action, myAsString(msg)) # TODO: combine multiple messages first?
        return
    make_sure_logged_in()
    typ, data = imap.select(foldername)
    if not typ=='OK': return # couldn't select that folder
    for msgID,flags,message in yield_all_messages(since='-'.join(email.utils.formatdate(time.time()-24*3600,localtime=True).split()[1:4])): run_spamprobe(spamprobe_action, message) # TODO: combine multiple messages first?
    
def open_compressed(fname,mode):
    if compression=="bz2":
        return bz2.BZ2File(fname+".bz2",mode)
        # (compresslevel default is 9)
    elif compression=="gz":
        return gzip.open(fname+".gz",mode)
        # (again, compresslevel default is 9)
    elif compression: raise Exception("Unrecognised compression type") # essential, as archive() assumes it can delete the original file after calling open_compressed
    return open(fname,mode)

def copy_to(mailbox, message_id):
    "Try to save an unmodified message to a folder, using the imap COPY command instead of re-uploading the message"
    assert imap == saveImap, "Can't call copy_to if saveImap != imap"
    typ, data = imap.fetch(message_id, "(UID)")
    if not typ=='OK': return False
    uid = data[0]
    if '(' in uid:
        uid=uid[uid.index('(')+1:uid.rindex(')')]
    if uid.startswith("UID "): uid=uid[4:]
    maybe_create(mailbox)
    try: return imap.uid('COPY', uid, mailbox)[0]=='OK'
    except: return False

already_created = set()
def maybe_create(mailbox):
    if mailbox and not mailbox in already_created:
        assert not type(mailbox)==tuple, "maybe_create should not be called with a maildir mailbox"
        saveImap.create(mailbox) # error if exists OK
        already_created.add(mailbox)
def save_to(mailbox, message_as_string, flags="", mayNeedNewMsgID=True):
    "Saves message to a mailbox on the saveImap connection, creating the mailbox if necessary"
    if type(mailbox)==tuple and mailbox[0]=='maildir': return save_to_maildir(mailbox[1],message_as_string,flags)
    elif imap_to_maildirs and not mailbox in imap_maildir_exceptions: return save_to_maildir(imap_to_maildirs+os.sep+mailbox,message_as_string,flags) # might as well skip the intermediate step of putting it in an IMAP folder to be picked up by imap_to_maildirs on next cycle
    make_sure_logged_in() ; maybe_create(mailbox)
    msg = email.message_from_string(message_as_string)
    if 'Date' in msg:
        try: imap_timestamp = email.utils.mktime_tz(email.utils.parsedate_tz(msg['Date'])) # We'd better not set the IMAP timestamp to anything other than the Date line.  IMAP timestamps are sometimes used for ordering messages by Received (e.g. Mutt, Alpine, Windows Mobile 6), but not always (e.g. Android 4 can sort only by Date); they're sometimes displayed (e.g. WM6) but sometimes not (e.g. Alpine), and some IMAP servers have sometimes been known to set them to Date anyway, so we can't rely on a different value (e.g. for postponed_foldercheck) always working.
        except: imap_timestamp = time.time() # badly-formatted date (TODO: could try Received lines)
    else: imap_timestamp = time.time() # undated message ? (TODO: could parse Received lines)
    if change_message_id and mayNeedNewMsgID and 'Message-ID' in msg: message_as_string = message_as_string.replace("Message-ID: <","Message-ID: <2",1) # .muttrc editor default adds '1', so let's add a '2'
    if imap_8bit and re.search("(?i)Content-Transfer-Encoding: quoted-printable",message_as_string): message_as_string = quopri_to_u8_8bitOnly(message_as_string) # TODO: check the "Content-Transfer-Encoding" is in the header or one of the MIME parts (don't do it if it's a non-MIME ascii-only message that happens to contain that text and perhaps some URLs with =(hex digits) in them)
    check_ok(saveImap.append(mailbox, flags, imaplib.Time2Internaldate(imap_timestamp), message_as_string))
    return "Uploaded"

def save_to_maildir(maildir_path, message_as_string, flags=""):
    mailbox.Maildir.colon = maildir_colon
    m = mailbox.Maildir(maildir_path,None)
    if re.search("(?i)Content-Transfer-Encoding: quoted-printable",message_as_string): message_as_string = quopri_to_u8_8bitOnly(message_as_string)
    msg = mailbox.MaildirMessage(email.message_from_string(message_as_string.replace("\r\n","\n")))
    msg.set_flags(maildir_flags_from_imap(flags))
    m.add(msg)
    return "Processed" # not Uploaded if it's a local maildir

def rename_folder(folder):
    if not isinstance(folder,str): return folder
    if folder.lower()=="inbox":
        return filtered_inbox
    elif folder.lower()=="spam": return spam_folder
    else: return folder

def listdir(d): return sorted(os.listdir(d))

def do_maildirs_to_imap():
    mailbox.Maildir.colon = maildir_colon
    for d in listdir(maildirs_to_imap):
        d2 = maildirs_to_imap+os.sep+d
        if not os.path.exists(d2+os.sep+"cur"):
            continue # not a maildir
        to = rename_folder(d)
        debug("Moving messages from maildir ",d," to imap ",to)
        m = get_maildir(d2)
        for k,msg in m.items():
            globalise_charsets(msg,imap_8bit)
            save_to(to,myAsString(msg),imap_flags_from_maildir_msg(msg),False)
            del m[k]
        clean_empty_maildir(d2)
def clean_empty_maildir(md):
    try: mailbox.Maildir(md,None).clean()
    except: pass
    newcurtmp = ["new","cur","tmp"]
    if not any(listdir(md+os.sep+ntc) for ntc in newcurtmp):
        # folder is now empty: remove it
        for nct in newcurtmp: os.rmdir(md+os.sep+nct)
        for f in ['dovecot.index','dovecot.index.cache','dovecot.index.log','dovecot-keywords','dovecot-uidlist','maildirfolder']: tryRm(md+os.sep+f)
        try: os.rmdir(md)
        except: pass

def imap_flags_from_maildir_msg(msg): return " ".join(" ".join({'S':r'\Seen','D':r'\Deleted','R':r'\Answered','F':r'\Flagged'}.get(flag,"") for flag in msg.get_flags()).split())
def maildir_flags_from_imap(flags):
    r = ""
    if r"\Deleted" in flags: r += 'D'
    if r"\Flagged" in flags: r += 'F'
    if r"\Answered" in flags: r += 'R'
    if r"\Seen" in flags: r += 'S'
    return r

def do_maildir_to_copyself():
    mailbox.Maildir.colon = maildir_colon
    m = get_maildir(maildir_to_copyself)
    said = False
    for k,msg in m.items():
        if not said:
            debug("Moving messages from ",maildir_to_copyself," to imap ",copyself_folder_name)
            said = True
        globalise_charsets(msg,imap_8bit)
        if copyself_delete_attachments:
            delete_attachments(msg)
        save_to(copyself_folder_name,myAsString(msg),imap_flags_from_maildir_msg(msg),False)
        del m[k]
    m.clean()
assert not copyself_folder_name == ('maildir', maildir_to_copyself), "this can lead to loops"
assert not (maildirs_to_imap and imap_to_maildirs), "Setting both maildirs_to_imap and imap_to_maildirs at the same time is not supported"

def do_copyself_to_copyself():
    for folder in copyself_alt_folder.split(","):
        if folder==copyself_folder_name:
            debug("Cannot specify copyself_folder_name in copyself_alt_folder: skipping ",folder)
            continue
        make_sure_logged_in()
        typ, data = imap.select(folder)
        if not typ=='OK': continue # skip non-selectable folder, without output: it may appear later if the relevant MUA is used
        said = False
        for msgID,flags,message in yield_all_messages():
            if not said: # don't say until we know there's at least some messages in the folder
                debug("Moving messages from ",folder," to ",copyself_folder_name)
                said = True
            msg = email.message_from_string(message)
            charsets_changed = globalise_charsets(msg,imap_8bit)
            if copyself_delete_attachments:
                delete_attachments(msg) # apparently deleting an attachment does not affect mayNeedNewMsgID, at least Gmail Jan 2022: use only charsets_changed for that
            save_to(copyself_folder_name,myAsString(msg),"\\Seen",charsets_changed) # can't use copy_to even if msg hasn't changed, because we can't get copy_to to set the Seen flag on the copy (unless an IMAP extension that can help us do that is installed)
            imap.store(msgID, '+FLAGS', '\\Deleted')
        if said: check_ok(imap.expunge())

def do_auto_delete():
    for folder in auto_delete_folder.split(","):
        make_sure_logged_in()
        typ, data = imap.select(folder)
        if not typ=='OK':
            debug("Skipping non-selectable folder ",folder)
            continue
        said = False
        for msgID,flags,message in yield_all_messages():
            if not said:
                debug("Deleting messages from ",folder)
                said = True
            imap.store(msgID, '+FLAGS', '\\Deleted')
        if said: check_ok(imap.expunge())

header_charset_regex = r'=\?(.*?)\?(.*?)\?(.*?)\?=' # RFC 2047
def header_to_u8(match):
    charset = match.group(1).lower()
    if charset in ['gb2312','gbk']: charset='gb18030'
    encoding = match.group(2)
    text = match.group(3)
    try:
        if encoding.upper()=='Q': text = quopri.decodestring(text,header=True)
        else: text = base64.decodestring(text)
        text = text.decode(charset)
    except:
        debug("Bad header line: exception decoding ",repr(text)," in ",charset,", leaving unchanged")
        return match.group()
    return text.encode('utf-8')
def globalise_header_charset(match):
    #if match.group(1).lower()=="utf-8":
    #    return match.group() # no changes needed
    # - actually, do it anyway, because some UTF8 headers might be
    # quopri-encoded when they're only ASCII, etc, and "normalising"
    # these might help the writing of filtering rules.
    # Also, we want to de-"stylise" Unicode 1D400..1D6A3
    # so it works better with speech synths and rules.
    hu8 = header_to_u8(match)
    if hu8 == match.group(): return hu8 # something went wrong; at least don't double-encode it
    return utf8_to_header(destylise_u8_header(hu8))
def destylise_u8_header(u8):
    def sub(match):
        m=match.group()
        aNum = ((ord(m[2])-0x90)*(0xc0-0x80)+ord(m[3])-0x80) % 52
        if aNum>=26: return chr(ord('a')+aNum-26)
        else: return chr(ord('A')+aNum)
    u8 = re.sub("\xf0\x9d[\x90-\x99][\x80-\xbf]",sub,re.sub("\xf0\x9d\x9a[\x80-\xa3]",sub,u8)) # U+1D400..U+1D6A3 (works even if Python is narrow build)
    if re.search("\xef[\xbc\xbd]",u8): u8=re.sub(u"[\uFF01-\uFF5E]",lambda m:chr(ord(m.group())-0xFF01+ord('!')),u8.decode('utf-8')).encode('utf-8') # full-width ASCII
    return u8
def utf8_to_header(u8):
    if not ('=?' in u8 or re.search(r"[^ -~]",u8)): return u8 # ASCII and no encoding needed
    ret = "B?"+base64.encodestring(u8).replace("\n","")
    qp = "Q?"+re.sub("=?\n","",quopri.encodestring(u8,header=True)).replace('?','=3F') # must have header=True for alpine (although mutt and Outlook etc may work either way, especially if the with-spaces version is not wrapped, but alpine fails to decode the quopri if any space is present)
    if len(qp) <= len(ret): ret = qp
    return "=?UTF-8?"+ret+"?="

import email.mime.multipart,email.mime.message,email.mime.text,email.mime.image,email.charset,email.mime.base
def turn_into_attachment(message,covering_text=None,attach_raw=False):
    if covering_text==None: covering_text = "Large message converted to attachment" # by imapfix, but best not mention this as it might bias the filters?
    m2 = email.mime.multipart.MIMEMultipart()
    for k,v in message.items():
        if not k.lower() in ['content-length','content-type','content-transfer-encoding','lines','mime-version','content-disposition']: m2[k]=v
    m2.attach(email.mime.text.MIMEText(covering_text))
    if attach_raw: m2.attach(message)
    else: m2.attach(email.mime.message.MIMEMessage(message))
    return m2
def size_of_first_part(message):
    if message.is_multipart():
        for i in message.get_payload():
            return size_of_first_part(i)
        return 0
    return len(message.get_payload())

def getFirstPart(message):
    if message.is_multipart():
        for i in message.get_payload():
            return getFirstPart(i)
        return ""
    try: pl = message.get_payload(decode=True)
    except: return ""
    cs = message.get_content_charset(None)
    if cs in [None,'us-ascii','utf-8']: return pl
    if cs in ['gb2312','gbk']: cs = 'gb18030'
    return pl.decode(cs).encode('utf-8')

def globalise_charsets(message,will_use_8bit=False,force_change=False):
    """'Globalises' the character sets of all parts of
        email.message.Message object 'message'.
        Only us-ascii and utf-8 charsets are 'global'.
        Also tries to use quoted-printable rather than
        base64 if doing so won't increase the length.
        Returns True if any changes were made.
        (Use force_change if you need to ensure encoding
        options are set correctly in case you want to do
        setPayload yourself to change the text.)"""
    changed = False
    for line in ["From","To","Cc","Subject","Reply-To"]:
        if not line in message: continue
        l = message[line]
        l2 = l.replace(" ?utf-8?q?"," =?utf-8?q?") # bug observed in mail generated by "SOGoMail 2.3.23"
        l2 = re.sub(header_charset_regex,globalise_header_charset,l2,flags=re.DOTALL).replace('\n',' ').replace('\r','') # the \n and \r replacements are in case the original header is corrupt
        if l==l2: continue
        # debug("Changing ",line," from ",l," to ",l2)
        # message["X-Imapfix-Old-"+line] = l
        del message[line]
        message[line] = l2
        changed = True
    if message.is_multipart():
        for i in message.get_payload():
            if globalise_charsets(i,will_use_8bit,force_change): changed = True
        return changed
    cType = message.get_content_type()
    if not cType.startswith("text/") and ('Content-Disposition' in message or cType.startswith("image/")): return changed # don't risk messing up PDF attachments, images etc
    is_html = cType and cType.startswith("text/html")
    specified_charset = message.get_content_charset(None)
    while specified_charset and specified_charset.startswith("charset="):
        # bug in some mailers: charset=charset=
        specified_charset = specified_charset[len("charset="):]
        force_change = True
    is_unspecified = cType and cType.startswith("text/") and not specified_charset
    try: p0 = message.get_payload(decode=True) # in most cases we need it (TODO: in a few small cases we don't, but low-priority as the entire message has probably been loaded into RAM already)
    except:
        message['X-ImapFix-Globalise-Charset-Decode-Error'] = str(sys.exc_info()[1])
        return True
    if specified_charset=='us-ascii' and re.search('[\x80-\xff]',p0): # mislabelled ASCII
        force_change = is_unspecified = True
        specified_charset = None
        message.set_payload(p0,None)
        changed = True
    if is_unspecified:
        if p0.startswith('\xfe\xff'): specified_charset = 'utf-16be'
        elif p0.startswith('\xff\xfe'): specified_charset = 'utf-16le'
        elif p0.startswith('\xef\xbb\xbf'): specified_charset = 'utf-8'
        else:
            try:
                import chardet
                d = chardet.detect(p0)
                threshold = 0.99
                if d['confidence'] >= threshold:
                    specified_charset = d['encoding']
                else:
                    message['X-ImapFix-Chardet']=d['encoding']+"; confidence="+str(d['confidence'])+" does not meet threshold "+str(threshold)+" so not setting charset"
                    changed = True
            except: pass # no chardet or sthg
    if not force_change: # should we SET force_change? :
      if 'Content-Transfer-Encoding' in message and not message['Content-Transfer-Encoding']=='quoted-printable': force_change = True # if it's base64, always see if we can change it
      elif specified_charset=='utf-8':
       if p0.startswith('\xef\xbb\xbf'): force_change = True # we'll want to remove that "BOM"
       elif will_use_8bit:
        try:
          if re.search("[^\x00-\x80]",message.get_payload(decode=True)): force_change = True
        except: pass # we would full back to return anyway on the 'problems decoding this message' below
    if specified_charset:
      if not force_change and specified_charset in ['us-ascii','utf-8'] and not is_html: return changed # no further conversion required
      if specified_charset in ['gb2312','gbk']: specified_charset = 'gb18030'
      try: p = p0.decode(specified_charset)
      except:
        message['X-ImapFix-Globalise-Charset-Error'] = str(sys.exc_info()[1])
        return True
      if is_html:
        q = '[\'"]' # could use either " or ' quotes
        p = re.sub(r'(?i)<meta\s+http[_-]equiv='+q+r'?content-type'+q+r'?\s+content='+q+'[^\'"]*'+q+r'>','',p) # better remove charset meta tags after we changed the charset (TODO: what if they conflict with the message header anyway?)
        p = re.sub(r'(?i)<meta\s+content='+q+'[^\'"]*'+q+r'\s+http[_-]equiv='+q+r'?content-type'+q+r'?>','',p) # some authoring tools emit the attributes in THIS order
      if p.startswith(u"\ufeff"): p=p[1:]
      specified_charset = 'utf-8'
      p = p.encode(specified_charset)
    else: # no specified_charset and we couldn't detect
      p = p0
      specified_charset = 'x-unknown' # contrary to the documentation, at least some versions of the library add 'us-ascii' if set to None
    if not force_change and p==p0: return changed # didn't fix meta tags or change charset so don't need to re-encode
    return setPayload(message,p,specified_charset,will_use_8bit)
def setPayload(message,p,charset,will_use_8bit=False):
    if 'Content-Transfer-Encoding' in message:
        isQP = (message['Content-Transfer-Encoding']=='quoted-printable')
        del message['Content-Transfer-Encoding']
    else: isQP = False
    if not isQP: # not already decided on quoted-printable; SHOULD we?
        b64len = len(base64.encodestring(p))
        pp = quopri.encodestring(p)
        isQP = (len(pp) <= b64len or (will_use_8bit and len(quopri_to_u8_8bitOnly(pp)) <= b64len)) # use Quoted-Printable rather than Base64 for UTF-8 if the original was quopri or if doing so is shorter (besides anything else it's easier to search emails without tools that way)
    for i in [1,2]: # before AND after, just in case
        if isQP: email.charset.add_charset(charset,email.charset.SHORTEST,email.charset.QP,charset)
        else: email.charset.add_charset(charset,email.charset.SHORTEST,email.charset.BASE64,charset)
        if i==2: return True
        message.set_payload(p,charset)
def quopri_to_u8_8bitOnly(s): # used by imap_8bit and archive_8bit (off by default).  Must ensure any header blocks in s are not touched!  (or imap server may substitute Xs etc)
    if re.search('[\x80-\xff]',s): return s # message already contains 8-bit stuff: we probably shouldn't redo this in case of coincidental UTF-8 quoted-printable in a binary attachment (TODO: what if such an attachment happens to lack any bytes with the high bit set)
    avoid = set()
    def avoidAdd(m):
        avoid.add((m.start(),m.end()))
        return m.group()
    re.sub(header_charset_regex,avoidAdd,s,flags=re.DOTALL) # don't want to interfere with MIME 'charset' etc in subject lines
    re.sub(r'h(=\r?\n)?t(=\r?\n)?t(=\r?\n)?p(=\r?\n)?(s(=\r?\n)?)?:(=\r?\n)?/(=\r?\n)?/(=\r?\n)?([^ "<>^'+"`'"+'](=\r?\n)?)+',avoidAdd,s) # and don't want to interfere with =hex in URLs (the '=' of which should have been double-encoded anyway, but sometimes isn't)
    def maybeDecode(m):
        for start,end in avoid: # TODO: improve efficiency when dealing with a very large archive with many headers?
            if start <= m.start() < end: return m.group()
        return quopri.decodestring(m.group())
    return re.sub(r"(=(([C][2-9A-F]|[D][0-9A-F])|E0=[AB][0-9A-F]|(E[1-9A-CEF]|F0=[9AB][0-9A-F]|F4=8[0-F])(=\r?\n)?=[89AB][0-9A-F]|ED=[89][0-9A-F]|F[1-3]=[89AB][0-9A-F]=[89AB][0-9A-F])(=\r?\n)?=[89AB][0-9A-F])+",maybeDecode,s) # decodes only 8-bit utf-8 characters from the quoted-printable string, leaving alone any 7-bit characters that are encoded as quoted-printable ("^From" etc)

def walk_msg(message,partFunc,*args):
    if message.is_multipart():
        changed = False
        global to_attach # for add_preview: it needs to add previews to the container immediately above, not necessarily the top-level container (as we might have a multipart/related within a multipart/alternative or something)
        try: to_attach
        except: to_attach = None # not called from add_preview
        o,to_attach = to_attach,[]
        for i in message.get_payload():
          changed = walk_msg(i,partFunc,*args) or changed
        if to_attach and message.get("Content-Type","").startswith("multipart/alternative"): # can happen with Exchange clients even if only one attachment
            ct = message["Content-Type"].replace("multipart/alternative","multipart/mixed",1)
            del message["Content-Type"]
            message["Content-Type"] = ct
        for i in to_attach: message.attach(i)
        to_attach = o ; return changed
    else: return partFunc(message,*args)

def add_previews(message):
    global to_attach ; to_attach = None
    accum = [1]
    return walk_msg(message,add_preview,accum)
def add_preview(message,accum):
    if to_attach == None: return False # TODO? (non-multipart message sent with a single image and nothing else)
    if not 'Content-Type' in message or message["Content-Type"].startswith("text/"): return False
    payload = message.get_payload(decode=True)
    try: img=Image.open(StringIO(payload))
    except: return False # not an image, or corrupt
    changed = False
    if message["Content-Type"].startswith("application/"):
        try: what = imghdr.what(None,payload)
        except: what = None
        if what:
            del message["Content-Type"]
            message["Content-Type"]="image/"+what
            changed = True
    try:
      exif=dict(img._getexif().items())
      if 274 in exif:
        if exif[274]==3:
            img=img.rotate(180)
        elif exif[274]==6:
            img=img.rotate(270)
        elif exif[274]==8:
            img=img.rotate(90)
    except: pass # no EXIF data, or can't de-rotate
    try: img.thumbnail(image_size,Image.ANTIALIAS)
    except: return changed # probably a JPEG-variant decoder not available
    try:
      s1 = StringIO();img.save(s1,'JPEG');s1=s1.getvalue()
    except: s1 = None
    try:
      s2 = StringIO();img.save(s2,'PNG'); s2=s2.getvalue()
    except: s2 = None
    if s1==None and s2==None: return changed
    elif s1==None: s,ext = s2,"png"
    elif s2==None or len(s2) > len(s1): s,ext = s1,"jpg"
    else: s,ext = s2,"png"
    if len(s) > len(payload): return changed # we failed to actually compress the image
    if ext=="png": subtype = "png"
    else: subtype = "jpeg"
    i = email.mime.image.MIMEImage(s,_subtype=subtype) # _subtype defaults to auto-detect but it can fail
    if not i['Content-Type'].lower().startswith('image/'): i['Content-Type']='image/'+i['Content-Type'] # depends on version of PIL?
    i['Content-Disposition']='attachment; filename=imapfix-preview'+str(accum[0])+'.'+ext # needed for some clients to show it
    to_attach.append(i) ; accum[0] += 1
    return True
def add_office(message):
    global to_attach ; to_attach = None
    accum = [1]
    return walk_msg(message,add_office0,accum)
def filename_ext(message):
    if not 'Content-Disposition' in message: return False
    fn = str(message['Content-Disposition'])
    s = re.search('filename="([^"]*)"',fn)
    if s: fn = s.group(1)
    else:
        s = re.search("filename=([^;]*)",fn)
        if s: fn = s.group(1)
        else: return False
    fn = re.sub(header_charset_regex,header_to_u8,fn)
    if not '.' in fn: return False
    ext = fn[fn.rindex('.'):].lower()
    return fn,ext
def add_office0(message,accum):
    if to_attach == None: return False # TODO? (non-multipart message sent with a single document and nothing else)
    if "Content-Type" in message and (str(message['Content-Type']).startswith("text/calendar") or str(message['Content-Type']).startswith("application/ics")):
        cal = ["Calendar file:"]
        for l in re.sub("LANGUAGE=[a-zA-Z-]*:","",message.get_payload(decode=True).replace("\r\n","\n").replace("\n "," ").replace("\nX-MICROSOFT-","\n").replace(";ROLE=REQ-PARTICIPANT","").replace(";PARTSTAT=NEEDS-ACTION","").replace(";RSVP=TRUE","").replace(";VALUE=DATE","").replace("mailto:","")).split("\n"):
            if any(l.startswith(f) for f in ["TZID:","ORGANIZER","ATTENDEE","SUMMARY","DTSTART:2","DTEND:2","DTSTART;TZID=","DTEND;TZID=","LOCATIONDISPLAYNAME","LOCATIONSTREET","LOCATIONCITY"]) and ':' in l and l[l.index(':')+1:].replace(r'\n','').strip(): cal.append(" ".join(l.replace(";","; ").replace(":",": ").split()))
        if len(cal)==1: return False # no details found
        b = email.mime.base.MIMEBase("text","plain")
        b.set_payload("\n".join(cal))
        to_attach.append(b) ; return True
    fn = filename_ext(message)
    if fn==False: return False
    fn,ext = fn
    if not ext in ".doc .docx .rtf .odt .xls .xlsx .ods .ppt .odp".split(): return False
    debug("Getting payload for ",fn)
    payload = message.get_payload(decode=True)
    infile = "tmpdoc-%d%s" % (os.getpid(),ext)
    outfile = "tmpdoc-%d.%s"%(os.getpid(),office_convert)
    open(infile,"wb").write(payload)
    debug("Running soffice to get ",outfile," from ",infile)
    if os.system("soffice --convert-to %s %s" % (office_convert, infile)) or not os.path.exists(outfile): # conversion error, or soffice not found
        debug("soffice run returned failure (is the install complete?)")
        clean_tmpdoc() ; return False
    mimeType = {"html":"text/html; charset=utf-8","pdf":"application/pdf"}.get(office_convert,"application/binary")
    mT,subT = mimeType.split("/")
    b = email.mime.base.MIMEBase(mT,subT)
    b.set_payload(open(outfile,"rb").read())
    if not office_convert=="html": encoders.encode_base64(b)
    clean_tmpdoc()
    if office_convert in ["html"] and not (max_size_of_first_part and len(b.get_payload) > max_size_of_first_part): pass # show it inline
    else: b['Content-Disposition']='attachment; filename=imapfix-preview'+str(accum[0])+'.'+office_convert
    to_attach.append(b) ; accum[0] += 1
    return True
def add_pdf(message):
    global to_attach ; to_attach = None
    accum = [1]
    return walk_msg(message,add_pdf0,accum)
def add_pdf0(message,accum):
    if to_attach == None: return False # TODO? (non-multipart message sent with a single pdf and nothing else)
    fn = filename_ext(message)
    if fn==False: return False
    fn,ext = fn
    if not ext==".pdf": return False
    debug("Getting payload for ",fn)
    payload = message.get_payload(decode=True)
    infile = "tmpdoc-%d.pdf" % (os.getpid(),)
    outfile = "tmpdoc-%ds.html" % (os.getpid(),)
    open(infile,"wb").write(payload)
    debug("Running pdftohtml")
    if os.system("pdftohtml -i -enc UTF-8 %s" % (infile,)): # (-i = ignore images, TODO: allow images and also attach them?  may need temporary directory.  Also what if libreoffice creates images in its html in add_office0?)  (Do not use -s for single page, it results in only the last PDF page being output, it does not mean combine all to a single HTML page, which happens anyway)
        # conversion error
        debug("pdftohtml run returned failure")
        clean_tmpdoc() ; return False
    b = email.mime.base.MIMEBase("text","html; charset=utf-8")
    b.set_payload(open(outfile,"rb").read())
    clean_tmpdoc()
    if not (max_size_of_first_part and len(b.get_payload) > max_size_of_first_part): pass # show it inline
    else: b['Content-Disposition']='attachment; filename=imapfix-preview'+str(accum[0])+'.html'
    to_attach.append(b) ; accum[0] += 1
    return True
def clean_tmpdoc():
    # soffice sometimes leaves images also, so check all
    prefix = re.compile("tmpdoc-%d[^0-9]" % (os.getpid(),))
    for f in os.listdir('.'):
        if re.match(prefix,f): tryRm(f)
def add_tnef(message):
    global to_attach ; to_attach = None
    accum = [1]
    return walk_msg(message,add_tnef0,accum)
def add_tnef0(message,accum):
    if to_attach == None: return False # TODO? (non-multipart message sent with winmail.dat and nothing else?)
    if not 'Content-Disposition' in message: return False
    fn = str(message['Content-Disposition'])
    if not 'winmail.dat' in fn.lower(): return False
    ret = False
    debug("Getting winmail.dat")
    payload = message.get_payload(decode=True)
    debug("Running tnef on winmail.dat")
    outdir = "tnefout-%d" % (os.getpid(),)
    os.mkdir(outdir)
    os.popen("tnef -C "+outdir+" --number-backups --unix-paths --save-body --ignore-checksum --ignore-encode --ignore-cruft","wb").write(payload)
    for f in listdir(outdir):
        debug("Adding ",repr(f))
        origF,f = f,outdir+os.sep+f
        b = getMimeBase(f)
        b.set_payload(open(f,"rb").read())
        tryRm(f)
        b['Content-Disposition']='attachment; filename='+origF
        encoders.encode_base64(b)
        to_attach.append(b) ; accum[0] += 1 ; ret = True
    try: os.rmdir(outdir)
    except: debug("Could not remove ",outdir)
    if ret: message.set_payload("") # no point keeping the winmail.dat itself if we successfully got its contents out
    return ret

def delete_headers(msg):
    changed = False
    for h in headers(msg):
        if any(h.startswith(hd) for hd in headers_to_delete):
            while h in msg: del msg[h]
            changed = True
    return changed

def getMimeBase(f):
    mimeType = mimetypes.guess_type(f)[0]
    if not mimeType: mimeType = "application/binary"
    mT,subT = mimeType.split("/")
    return email.mime.base.MIMEBase(mT,subT)

def folderList(pattern="*"):
    make_sure_logged_in()
    typ,data = imap.list(pattern=pattern)
    if not typ=='OK': return []
    return [re.sub('.*"." ','',i).replace('"','') for i in data if i and not r"\Noselect" in i]

isoDate = "[1-9][0-9][0-9][0-9]-[0-1][0-9]-[0-3][0-9]"
if postponed_daynames:
    # use the current locale's idea of the abbreviated names
    weekdays = [time.strftime("%a",time.gmtime(time.mktime((2001,1,i,0,0,0,0,0,0)))).lower() for i in range(1,8)]
    months = [time.strftime("%b",time.gmtime(time.mktime((2001,i,1,0,0,0,0,0,0)))).lower() for i in range(1,13)]
    weekMonth = "("+"|".join(weekdays+months)+")(?=$|:)"
def isoToday(): return "%04d-%02d-%02d" % time.localtime()[:3]
def check_todays_dayname():
    if postponed_daynames:
        do_postponed_foldercheck(time.strftime("%a").lower()) # weekday
        if time.localtime()[2]==1: # 1st of the month
            do_postponed_foldercheck(time.strftime("%b").lower()) # month
def do_postponed_foldercheck(dayToCheck="today"):
    today = isoToday()
    if dayToCheck=="old": # called only on startup (and only if postponed_foldercheck)
        if postponed_daynames and time.localtime()[3:5] < (0,30):
            # If we restarted less than half an hour after midnight, check dayname folders on startup (because it might not have happened if we were in the middle of a 29-minute imap idle when the server rebooted)
            check_todays_dayname()
        # and regardless of what time of day we are doing this (re)start, check for dated folders of today and older
        if postponed_maildir: mList=os.listdir(postponed_maildir)
        else: mList = []
        for f in folderList()+mList: # if we're sharing a maildir with an IMAP server like Dovecot (which uses Maildir++ i.e. folder directories start with dot) then mList might have dot + date
            if re.match("[.]?"+isoDate+'$',f) and f <= today: # TODO: Y10K (lexicographic comparison)
                do_postponed_foldercheck(f)
        return
    elif dayToCheck=="today": # called at midnight rollover (if postponed_foldercheck or postponed_daynames)
        check_todays_dayname()
        if postponed_foldercheck: dayToCheck = today
        else: return
    if postponed_maildir:
        try: maildir = get_maildir(postponed_maildir+os.sep+dayToCheck,False) # don't create if not exist
        except: maildir = None
        if maildir:
            said = False ; toDel = []
            for msgID,msg in maildir.iteritems():
                if not said:
                    debug("Moving messages from maildir ",postponed_maildir+os.sep+dayToCheck," to ",filtered_inbox)
                    said = True
                reDate(msg)
                save_to(filtered_inbox,myAsString(msg),mayNeedNewMsgID=False)
                toDel.append(msgID)
            for msgID in toDel: del maildir[msgID]
            clean_empty_maildir(postponed_maildir+os.sep+dayToCheck)
    f = folderList(dayToCheck)
    if not len(f)==1: return # no folder of that name
    folder = f[0] ; imap.select(folder) ; said = False
    for msgID,flags,message in yield_all_messages():
        if not said:
            debug("Moving messages from ",folder," to ",filtered_inbox)
            said = True
        msg = email.message_from_string(message)
        reDate(msg)
        save_to(filtered_inbox,myAsString(msg))
        imap.store(msgID, '+FLAGS', '\\Deleted')
    if said: check_ok(imap.expunge())
    check_ok(imap.select()) ; do_delete(folder)

def reDate(msg):
    theFrom = msg.get('From','').replace('"','').strip()
    if theFrom==imapfix_name: # pre v1.5
        del msg['From'] ; msg['From'] = from_line # K-9 5.8+
    old_date = msg.get("Date","")
    if old_date:
        if theFrom.endswith(from_addr): pass # no need to add old date if it's a --note or --multinote
        elif authenticates(msg) and 'To' in msg and (username in msg['To'] or getAddr(msg['To'])==getAddr(msg.get('From',''))): pass # probably no need to add old date if it's a message from yourself to yourself (similar to --note/--multinote)
        else: walk_msg(msg,addOldDateFunc(old_date))
        del msg['Date']
    msg['Date'] = email.utils.formatdate(localtime=True)
def getAddr(a): return ''.join(a.split()[-1:]).replace('<','').replace('>','')
def addOldDateFunc(old_date):
    def addOldDate(message):
        newPara = ""
        if 'Content-Type' in message:
            if not message["Content-Type"].startswith("text/"): return False
            if message["Content-Type"].startswith("text/html"): newPara = "<p>" # TODO: might end up being before the HTML tag; depends which browser you use
        if 'Content-Disposition' in message and message['Content-Disposition'].startswith('attachment'): return False
        changed = globalise_charsets(message, imap_8bit) # just in case
        dateIntro = from_name+": original Date: "
        if message.get_payload(decode=True).startswith(dateIntro): return changed
        if not changed: globalise_charsets(message, imap_8bit, True) # ensure set up for:
        return setPayload(message,dateIntro + old_date + newPara + "\n\n" + message.get_payload(decode=True),'utf-8') # Fixed in v1.498: postponing a message previously caused quopri to be decoded but still declared, invalidating URLs that had = followed by hex code in them, breaking links on commercial mailing-list trackers like MailChimp
    return addOldDate

def do_calendar():
    for l in os.popen("calendar -A 0 -f \"%s\"" % calendar_file):
        if not l.strip(): continue
        subj = l.split()[1:]
        if not subj: continue
        if re.match("^[0-9*]*$",subj[0]): subj=subj[1:] # month day txt
        subj = ' '.join(l.split()[2:])
        if len(subj)>60: subj=subj[:57]+"..."
        save_to(filtered_inbox,"From: "+from_line.replace(from_name,"calendar",1)+"\r\nSubject: "+subj+"\r\nDate: "+email.utils.formatdate(localtime=True)+"\r\n\r\n"+l+"\n")

setAlarmAt = 0
def checkAlarmDelay():
    global setAlarmAt
    if time.time() > setAlarmAt:
        import signal
        signal.setitimer(signal.ITIMER_REAL,alarm_delay)
        setAlarmAt = time.time() + alarm_delay/2

def mainloop():
  newDay = oldDay = time.localtime()[:3] # for midnight
  done_spamprobe_cleanup_today = False
  secondary_imap_due = 0
  if exit_if_imapfix_config_py_changes:
    if exit_if_imapfix_config_py_changes=="stamp":
      try: os.utime("imapfix_config.py",None) # open with "a" doesn't always update timestamp
      except: pass
    import imapfix_config
    mfile = imapfix_config.__file__ # might be in different directory on sys.path
    if mfile.endswith("pyc"): mfile=mfile[:-1]
    mtime = os.stat(mfile).st_mtime
  debug(__doc__)
  try:
   if postponed_foldercheck or postponed_daynames: do_postponed_foldercheck("old")
   if poll_interval: debug("Starting loop at %d-%02d-%02d %d:%02d" % time.localtime()[:5])
   while True:
    if alarm_delay: checkAlarmDelay()
    if maildirs_to_imap: do_maildirs_to_imap()
    if maildir_to_copyself: do_maildir_to_copyself()
    if copyself_alt_folder: do_copyself_to_copyself()
    if auto_delete_folder: do_auto_delete()
    if imap_to_maildirs: do_imap_to_maildirs()
    if maildir_dedot: do_maildir_dedot()
    global filtered_inbox
    if filtered_inbox: process_imap_inbox()
    if time.time() > secondary_imap_due and secondary_imap_hostname:
        fiO = filtered_inbox
        if not filtered_inbox:
            make_sure_logged_in()
            filtered_inbox="" # rather than None
        process_secondary_imap()
        filtered_inbox = fiO
        secondary_imap_due = time.time() + secondary_imap_delay
    if logout_before_sleep: make_sure_logged_out()
    if sync_command: os.system(sync_command) # might make a separate login, hence after logout_before_sleep
    if not poll_interval: break # --once
    if not done_spamprobe_cleanup_today:
        spamprobe_cleanup()
        done_spamprobe_cleanup_today = True
    if poll_interval=="idle":
        make_sure_logged_in() ; imap.select()
        debug("Waiting for IMAP event")
        try: imap.idle() # Can take a timeout parameter, default 29 mins.  TODO: allow shorter timeouts for clients behind NAT boxes or otherwise needing more keepalive?  IDLE can still be useful in these circumstances if the server's 'announce interval' is very short but we don't want across-network polling to be so short, e.g. slow link (however you probably don't want to be running imapfix over slow/wobbly links - it's better to run it on a well-connected server)
        except: # e.g. imaplib2.abort, fall back on delay
            debug("Wait failed: falling back to logout + 5 minutes")
            make_sure_logged_out()
            time.sleep(300)
    else:
        debug("Sleeping for ",poll_interval," seconds")
        time.sleep(poll_interval)
    newDay = time.localtime()[:3]
    if not oldDay==newDay:
      oldDay=newDay
      if midnight_command: os.system(midnight_command)
      if calendar_file: do_calendar()
      if postponed_foldercheck or postponed_daynames:
          do_postponed_foldercheck()
      if train_spamprobe_nightly: do_nightly_train()
      done_spamprobe_cleanup_today = False
    if exit_if_imapfix_config_py_changes and not near_equal(mtime,os.stat(mfile).st_mtime):
        debug("Config change detected")
        break
  finally: make_sure_logged_out()

def near_equal(time1,time2):
    # allow small difference due to filesystem quirks
    # (e.g. if the server caches file times at a higher
    # resolution than the underlying filesystem, which can
    # be the case in some Linux+NetWare setups)
    if time1 > time2: time2,time1 = time1,time2
    return (time2-time1) <= 5

if secondary_imap_hostname:
    assert type(secondary_imap_hostname) == type(secondary_imap_username) == type(secondary_imap_password) and type(secondary_imap_hostname) in [str,list], "Invalid combination of types in secondary_imap settings"
    if type(secondary_imap_hostname) == str:
        secondary_imap_hostname = [secondary_imap_hostname]
        secondary_imap_username = [secondary_imap_username]
        secondary_imap_password = [secondary_imap_password]
    else: assert len(secondary_imap_hostname) == len(secondary_imap_username) == len(secondary_imap_password), "secondary_imap lists have differing lengths"

def get_logged_in_imap(host,user,pwd,insecureFirst=False):
    debug("Logging in to ",host)
    if host in insecure_login: # expect no SSL
        order = [imaplib.IMAP4, imaplib.IMAP4_SSL]
    else: order = [imaplib.IMAP4_SSL,imaplib.IMAP4]
    for Class in order:
        try:
            if len(host.split(':'))==2:
                host,port = host.split(':')
                imap = Class(host, int(port))
            else: imap = Class(host)
            if type(pwd)==tuple: # OAuth2
                cmd,secs = pwd
                if oauth2_string_cache.setdefault(cmd,(None,0))[1] < time.time():
                    debug("Generating OAuth2 access string")
                    access_string = commands.getoutput(cmd).strip()
                    try: access_string = base64.decodestring(access_string)
                    except: pass # maybe it wasn't base64
                    oauth2_string_cache[cmd] = (access_string,time.time()+secs)
                debug("Using OAuth2 access string") # if hangs here, refresh token might have been invalidated (e.g. in GMail 'testing-only apps' the refresh tokens are short-lived) and the server is delaying it after repeated use
                check_ok(imap.authenticate('XOAUTH2', lambda _:oauth2_string_cache[cmd][0]))
            else: check_ok(imap.login(user,pwd))
            debug("Logged in")
            return imap
        except: pass
    raise Exception("Could not log in to "+host)
oauth2_string_cache = {}

def process_secondary_imap():
  global imap ; first=True
  for sih,siu,sip in zip(secondary_imap_hostname, secondary_imap_username, secondary_imap_password):
    if first_secondary_is_copy_only and first:
      first = False ; continue
    try: imap = get_logged_in_imap(sih,siu,sip)
    except:
        msg = "Could not log in as %s to secondary IMAP %s: skipping it this time" % (siu,sih)
        debug(msg)
        if report_secondary_login_failures:
            imap = saveImap # for make_sure_logged_in
            save_to(filtered_inbox,"From: "+from_line+"\r\nSubject: imapfix_config secondary_imap problem or server down\r\nDate: %s\r\n\r\n%s\n" % (email.utils.formatdate(localtime=True),msg))
        imap = None
    if imap:
        global additional_inbox
        oAI = additional_inbox
        if not check_additional_inbox_on_secondary_too:
            additional_inbox = None
        process_imap_inbox()
        additional_inbox = oAI
        if check_copyself_alt_folder_on_secondary_too:
            do_copyself_to_copyself()
  imap = saveImap

def do_archive():
    try: os.mkdir(archive_path)
    except: pass # no error if exists
    for foldername,age,action in archive_rules:
        if not age==None: age = age*24*3600
        if type(foldername)==tuple: bStr=foldername[1]
        else: bStr = foldername
        if os.sep in bStr:
            bStr=bStr[bStr.rindex(os.sep)+1:]
            assert bStr, "shouldn't end mbox with /"
        archive(foldername, archive_path+os.sep+bStr, age, action)

def do_nightly_train():
    for foldername,age,action in archive_rules:
        nightly_train(foldername, action)
        
def yield_folders():
    "iterates through folders in imap, selecting each one as it goes"
    make_sure_logged_in()
    for foldername in imap.list()[1]:
        if '"/"' in foldername: foldername=foldername[foldername.index('"/"')+3:].lstrip()
        if foldername.startswith('"') and foldername.endswith('"'): foldername=foldername[1:-1] # TODO: check if any other unquoting is needed
        typ, data = imap.select(foldername)
        if not typ=='OK': continue
        yield foldername

def do_note(subject,ctype="text/plain",maybe=0,to_real_inbox=False):
    subject = subject.strip()
    if not subject: subject = "Note to self (via imapfix)"
    if isatty(sys.stdin):
        sys.stderr.write("Type the note, then EOF\n")
    body = sys.stdin.read()
    if maybe and not body.strip(): return
    if not body: body = " " # make sure there's at least one space in the message, for some clients that don't like empty body
    if filtered_inbox==None or to_real_inbox:
        saveTo = ""
    else: saveTo = filtered_inbox
    save_to(saveTo,"From: "+from_line+"\r\nSubject: "+utf8_to_header(subject)+"\r\nDate: "+email.utils.formatdate(localtime=True)+"\r\nMIME-Version: 1.0\r\nContent-type: "+ctype+"; charset=utf-8\r\n\r\n"+from_mangle(body)+"\n")
def from_mangle(body): return re.sub('(?<![^\n])From ','>From ',body) # (Not actually necessary for IMAP, but might be useful if the message is later processed by something that expects a Unix mailbox.  Could MIME-encode instead, but not so convenient for editing.)

def upload(filelist):
    for f in filelist:
        if os.path.isdir(f): upload([(f+os.sep+g) for g in listdir(f)])
        elif not os.path.isfile(f): debug("Ignoring non-file non-directory ",f)
        elif not f.endswith('~'): debug(do_upload(open(f,"rb").read(),os.stat(f).st_mtime,f)+" ",f)
        else: tryRm(f),debug("Deleting "+f)

def multinote(filelist,to_real_inbox,use_filename=False):
    if not filtered_inbox: to_real_inbox = True
    for f in filelist:
        if os.path.isdir(f):
            multinote([(f+os.sep+g) for g in listdir(f)],to_real_inbox,use_filename)
            continue
        if not os.path.isfile(f):
            debug("Ignoring non-file non-directory ",f)
            continue
        if not f.endswith('~'):
            if use_filename:
                subj = f
                if os.sep in subj: subj=subj[subj.rindex(os.sep)+1:]
            else: subj = None
            r = do_multinote(open(f).read(),os.stat(f).st_mtime,to_real_inbox,subj)
            if r: debug(r+" ",f)
        tryRm(f)

def tryRm(f):
    try: os.remove(f)
    except: pass

def do_upload(data,theDate,fname):
    b = getMimeBase(fname)
    b.set_payload(data)
    b['Content-Disposition']='attachment; filename='+(os.sep+fname)[(os.sep+fname).rindex(os.sep)+1:]
    encoders.encode_base64(b)
    message = turn_into_attachment(b,"Attached "+fname,True)
    message["From"] = from_line
    message["Subject"] = fname
    message["Date"] = email.utils.formatdate(theDate,localtime=True)
    return save_to(filtered_inbox,myAsString(message))

def do_multinote(body,theDate,to_real_inbox,subject):
    body = re.sub("\r\n?","\n",body.strip())
    if not body and not subject:
        debug("Not creating message from blank file")
        return False
    if not subject: subject,body = (body+"\n").split("\n",1)
    seenFlag = ""
    if to_real_inbox: box = ""
    else:
        box,newSubj = authenticated_wrapper(subject,body)
        if box and box[0]=='*':
            box=box[1:] ; seenFlag="\\Seen"
        if newSubj: subject = newSubj
    if box==False: box=filtered_inbox
    if box==None: return "Deleted" # (if this happens on multinote, you might want to check your authenticated_wrapper rules)
    else: return save_to(box,"From: "+from_line+"\r\nSubject: "+utf8_to_header(subject)+"\r\nDate: "+email.utils.formatdate(theDate,localtime=True)+"\r\nMIME-Version: 1.0\r\nContent-type: text/plain; charset=utf-8\r\n\r\n"+from_mangle(body)+"\n",seenFlag)

def isatty(f): return hasattr(f,"isatty") and f.isatty()
if quiet==2: quiet = not isatty(sys.stdout)

def do_delete(foldername):
    foldername = foldername.strip()
    if not foldername:
        print ("No folder name specified")
        return
    make_sure_logged_in()
    print ("Deleting folder "+repr(foldername))
    typ, data = imap.delete(foldername)
    if not typ=='OK': # some folders can't be deleted, so just log
        print("Ignoring failed folder delete: "+str(typ)+' '+repr(data))

def do_create(foldername):
    foldername = foldername.strip()
    if not foldername:
        print ("No folder name specified")
        return
    make_sure_logged_in()
    print ("Creating folder "+repr(foldername))
    check_ok(imap.create(foldername))

def secondary_security(message_as_string):
    oms = message_as_string
    if imap_8bit and re.search("(?i)Content-Transfer-Encoding: quoted-printable",message_as_string): message_as_string = quopri_to_u8_8bitOnly(message_as_string) # because saveTo will do this (same TODO as there) so normalise for comparing across servers
    if secondary_is_insecure: message_as_string = re.sub(addr_regex,"email.removed@example.org",message_as_string[:secLimit])+message_as_string[secLimit:] # NB the substitute email MUST fit into the original pattern: in particular the top-level domain must be between 2 and 5 letters, otherwise reapplying this function will get different text (e.g. ".removeded" if using @email.removed)
    if not message_as_string == oms: message_as_string = re.sub("\r\nContent-Length: [0-9]+\r\n","\r\n",message_as_string) # secondary IMAP will likely fix or delete this anyway
    return message_as_string
def ccnl(c): return c+r'+(?:=\r?\n'+c+'*)?' # character class + maybe newline: for speed we limit the number of line breaks that occur in each ccnl to one
def cnl(c): return c+r'(?:=\r?\n)?' # char + opt newline
addr_regex = re.compile("".join([
    # TODO: need to make this faster.  (Or can we be more selective about which parts of the message get it i.e. not images etc)
    ccnl('[a-zA-Z0-9_\-\.]'),
    cnl('@'),
    '(?:'+ccnl('[a-zA-Z0-9\-]')+cnl(r'(?:\.|=2E)')+')+',
    '(?:'+cnl('[a-zA-Z]')+'){2,5}(?![a-zA-Z])'])) # TODO: this deals with the header easily, and with SOME quoted-printable-in-long-HTML-line situations, but should also rm from Base64 in body (if quoting) (+ email at very end of msg w. no trailing \n)

def do_backup():
    for foldername in folderList():
        check_ok(imap.select(foldername))
        fname = foldername.replace("/","-").replace('"','')+"-backup.mbox"
        if os.path.exists(fname): # must create new
            os.rename(fname,fname+"~")
        mbox = mailbox.mbox(fname)
        print ("Backing up "+foldername+" to "+fname)
        for msgID,flags,message in yield_all_messages():
            msg = email.message_from_string(message)
            if not message.startswith("From "): # as above
                if 'From' in msg:
                    fr = msg['From']
                    if '<' in fr and '>' in fr[fr.index('<'):]: fr = fr[fr.index('<')+1:fr.rindex('>')]
                    if not fr: fr = 'unknown'
                    message="From "+fr+"\r\n"+message
                    msg = email.message_from_string(message)
            globalise_charsets(msg,archive_8bit)
            k=mbox.add(msg)
            newFlags = ""
            if "\\seen" in flags.lower() and not "old" in flags.lower(): newFlags += "R"
            if "\\answered" in flags.lower(): newFlags += "A"
            if newFlags:
                msg = mbox.get(k) # to mailbox.mboxMessage
                msg.set_flags(newFlags)
                mbox[k] = msg
        mbox.close()

imap_maildir_exceptions += ["","INBOX",filtered_inbox,
                            additional_inbox,
                            spam_folder]
if auto_delete_folder: imap_maildir_exceptions += auto_delete_folder.split(",")
if copyself_alt_folder: imap_maildir_exceptions += copyself_alt_folder.split(",")
def do_imap_to_maildirs():
    mailbox.Maildir.colon = maildir_colon
    for foldername in folderList():
        if foldername in imap_maildir_exceptions: continue
        typ, data = imap.select(foldername)
        if not typ=='OK': continue
        m = None
        for msgID,flags,message in yield_all_messages():
            if m == None:
                debug("Moving ",foldername+" to ",imap_to_maildirs)
                foldr = foldername.replace(os.sep,'-')
                # case-remembering, in case IMAP server changes capitalisation:
                for f in os.listdir(imap_to_maildirs):
                    if f.lower() == foldr.lower():
                        foldr = f ; break
                m = mailbox.Maildir(imap_to_maildirs+os.sep+foldr,None)
            msg = email.message_from_string(message)
            globalise_charsets(msg,imap_8bit)
            msg = myAsString(msg)
            if re.search("(?i)Content-Transfer-Encoding: quoted-printable",msg): msg = quopri_to_u8_8bitOnly(msg)
            msg = mailbox.MaildirMessage(email.message_from_string(msg.replace("\r\n","\n")))
            msg.set_flags(maildir_flags_from_imap(flags))
            m.add(msg)
            imap.store(msgID, '+FLAGS', '\\Deleted')
        if not m==None: check_ok(imap.expunge())
        folders_to_keep = [copyself_folder_name]+[f[0] for f in header_rules] # (no point deleting THOSE folders, even if empty, if on imap: will be re-used soon enough)
        if copyself_alt_folder: folders_to_keep += copyself_alt_folder.split(',') # deleting these could result in some applications failing to save sent mail
        if not foldername in folders_to_keep:
            check_ok(imap.select())
            do_delete(foldername)

def do_maildir_dedot():
    for poss in os.listdir(maildir_dedot):
        if poss.startswith(".") and not os.path.islink(maildir_dedot+os.sep+poss) and os.path.exists(maildir_dedot+os.sep+poss+os.sep+"cur"):
            debug("Moving messages from maildir ",poss," to maildir ",poss[1:])
            m = get_maildir(maildir_dedot+os.sep+poss)
            for k,msg in m.items():
                globalise_charsets(msg,imap_8bit)
                save_to(('maildir',maildir_dedot+os.sep+poss[1:]),myAsString(msg),imap_flags_from_maildir_msg(msg),False)
                del m[k]
            clean_empty_maildir(maildir_dedot+os.sep+poss)
    
def do_copy(foldername):
    foldername = foldername.strip()
    if not foldername:
        print ("No folder name specified")
        return
    make_sure_logged_in()
    global imap,saveImap,imap_to_maildirs
    imap_to_maildirs = None
    check_ok(imap.select(foldername))
    # Work out which messages need to be deleted:
    do_not_delete = set() ; do_not_copy = set()
    debug("Checking primary messages")
    def zapSpace(m): return re.sub(r"\s+","",m) # for comparing modulo trailing newlines, different line splitting in the header, etc
    for msgID,flags,message in yield_all_messages():
        do_not_delete.add(zapSpace(secondary_security(message)))
    make_sure_logged_out() # as the next step might cause the first imap to time out on us while it's waiting
    try: imap = get_logged_in_imap(secondary_imap_hostname[0],secondary_imap_username[0],secondary_imap_password[0])
    except:
        debug("Could not log in to secondary IMAP")
        return
    debug("Checking secondary messages; removing old ones")
    imap.create(foldername) # error if exists OK
    check_ok(imap.select(foldername))
    tot=rm=0
    for msgID,flags,message in yield_all_messages():
        tot += 1
        message = secondary_security(message) # for comparisons to work
        if zapSpace(message) in do_not_delete and not zapSpace(message) in do_not_copy: do_not_copy.add(zapSpace(message)) # already there (and not a duplicate; latter check added to help clean up damage due to multiple imapfix processes running on a cluster)
        else:
            imap.store(msgID, '+FLAGS', '\\Deleted')
            rm += 1
    debug("... ",rm," of ",tot," removed")
    imap,_saveImap = None,imap
    make_sure_logged_in() ; saveImap=_saveImap
    debug("Copying new messages to secondary")
    check_ok(imap.select(foldername))
    tot = cp = 0
    for msgID,flags,message in yield_all_messages():
        tot += 1
        message = secondary_security(message)
        if not zapSpace(message) in do_not_copy:
            flags2 = [] # don't just copy them over, as the secondary IMAP might not understand all the same flags
            if "\\answered" in flags.lower(): flags2.append("\\Answered")
            if "\\seen" in flags.lower() and not "old" in flags.lower(): flags2.append("\\Seen")
            # Not sure if all secondary IMAPs will understand \Flagged (called "star" in some clients e.g. K9 Mail; mutt default keybindings set with w ! and clear with W ! )
            flags = " ".join(flags2)
            save_to(foldername,message,flags,False)
            cp += 1
    debug("... ",cp," of ",tot," added")
    check_ok(saveImap.expunge())

def do_quicksearch(s):
    global quiet ; quiet = True # don't need "Logging in" etc
    for foldername in yield_folders():
        for msgID, flags, message in yield_all_messages(s):
            matching_lines = filter(lambda l:s.lower() in l.lower(), message.split('\n'))
            for m in matching_lines:
                try_print(foldername,m.strip())
    if not archive_path: return
    try: dirlist = listdir(archive_path)
    except:
        debug("Can't open ",archive_path,", omitting")
        dirlist = []
    for f in dirlist:
        f = archive_path+os.sep+f
        if f.endswith(compression_ext): f2 = open_compressed(f[:-len(compression_ext)],'r')
        else: f2 = open(f) # ?? (shouldn't happen, as all the files we put there should end with compression_ext, but just in case; TODO other forms of compression?)
        for l in f2:
            if s.lower() in l.lower(): try_print(f,l.strip())

def try_print(folder,line):
    try:
        sys.stdout.write(folder+": "+line+"\n")
        sys.stdout.flush()
    except IOError: # probably the pager quit on us
        raise SystemExit

def shell_quote(s): return "'"+s.replace("'",r"'\''")+"'"

imap = None
def make_sure_logged_in():
    global imap, saveImap
    while imap==None:
        try: imap = saveImap = get_logged_in_imap(hostname,username,password)
        except:
            if not login_retry: raise
            imap = None
            debug("Login failed; retry in 30 seconds")
            time.sleep(30)
def make_sure_logged_out():
    global imap, saveImap
    if not imap==None:
        debug("Logging out")
        imap.logout()
        imap = saveImap = None

def other_running():
    ps = commands.getoutput("ps auxwww").split('\n')
    numCols = len(ps[0].split())
    lineFormat = r"^(.*[^\s])\s+([0-9]+)"+r"\s+[^\s]+"*(numCols-3)+r"\s+([^\s].*)$" # this assumes the PID will be the first numeric thing that comes after whitespace (which should cope with usernames that have whitespace in them as long as they don't have whitespace followed by number)
    thisPIDuser = "" ; otherPIDusers = set()
    for p in ps:
        m = re.match(lineFormat,p)
        if not m: continue
        user,pid,command = m.groups()
        start = command.find(sys.argv[0])
        if start<0: continue # it's not an imapfix process
        if command[start+len(sys.argv[0]):].strip(): continue # ignore imapfix process with options (or a shell command like 'imapfix;something-else')
        if start:
            before_arg0 = command[:start].strip()
            if ' ' in before_arg0 or ';' in before_arg0 or '&' in before_arg0: continue # some kind of shell command that ends up running imapfix
        # if get this far, it's *probably* an imapfix process (but not guaranteed - I did say exit_if_other_running wasn't perfect
        if pid==str(os.getpid()): thisPIDuser = user
        else: otherPIDusers.add(user)
    return thisPIDuser in otherPIDusers

callSMTP_time = None
def send_mail(to_u8,subject_u8,txt,attachment_filenames=[],copyself=True,ttype="plain",charset="utf-8"):
    global callSMTP_time
    if callSMTP_time:
        toSleep = max(0,callSMTP_time-time.time())
        if toSleep: debug("Sleeping for another ",toSleep," seconds before reconnecting to SMTP")
        time.sleep(toSleep)
    debug("SMTP to ",repr(to_u8))
    msg = email.mime.text.MIMEText(re.sub('\r?\n','\r\n',txt),ttype,charset) # RFC 2822 says MUST use CRLF; some mail clients get confused by just \n (e.g. some versions of MPro on RISC OS when replying with quote)
    if attachment_filenames:
        from email.mime.multipart import MIMEMultipart
        msg2 = msg
        msg = MIMEMultipart()
        msg.attach(msg2)
    msg['Subject'] = utf8_to_header(subject_u8)
    msg['From'] = smtp_fromHeader
    msg['To'] = ' '.join(utf8_to_header(h) for h in to_u8.split()) # just the name part needs utf8_to_header, TODO: parse properly instead of going through every word?  + what if it's a list?
    msg['Date'] = email.utils.formatdate(localtime=True)
    msg['X-Mailer'] = __doc__[:__doc__.index(" (c)")] # in case somebody needs to audit
    for f in attachment_filenames:
        subMsg = getMimeBase(f)
        subMsg.set_payload(open(f,'rb').read())
        encoders.encode_base64(subMsg)
        if os.sep in f: f=f[f.rindex(os.sep)+1:]
        subMsg.add_header('Content-Disposition', 'attachment', filename=f)
        msg.attach(subMsg)
    import smtplib
    if smtp_host=="localhost": s = smtplib.SMTP(smtp_host)
    else: s = smtplib.SMTP_SSL(smtp_host)
    if smtp_user:
        if type(smtp_password)==tuple:
            cmd,secs = smtp_password
            if oauth2_string_cache.setdefault(cmd,(None,0))[1] < time.time():
                debug("Generating OAuth2 access string for SMTP")
                access_string = commands.getoutput(cmd).strip()
                try: access_string = base64.decodestring(access_string)
                except: pass # maybe it wasn't base64
                oauth2_string_cache[cmd] = (access_string,time.time()+secs)
            s.docmd('AUTH','XOAUTH2 '+base64.b64encode(access_string))
        else: s.login(smtp_user, smtp_password)
    ret = s.sendmail(smtp_fromAddr,to_u8,myAsString(msg))
    assert len(ret)==0, "Some (but not all) recipients were refused: "+repr(ret)
    s.quit()
    if smtp_delay: callSMTP_time = time.time()+smtp_delay
    if copyself:
        if copyself_delete_attachments:
            delete_attachments(msg)
        save_to(copyself_folder_name,myAsString(msg),"\\Seen")
import imapfix_config
imapfix_config.send_mail = send_mail

if __name__ == "__main__":
  if '--archive' in sys.argv: do_archive()
  elif '--quicksearch' in sys.argv: do_quicksearch(' '.join(sys.argv[sys.argv.index('--quicksearch')+1:]))
  elif '--delete' in sys.argv: do_delete(' '.join(sys.argv[sys.argv.index('--delete')+1:]))
  elif '--delete-secondary' in sys.argv:
      hostname,username,password = secondary_imap_hostname[0],secondary_imap_username[0],secondary_imap_password[0]
      do_delete(' '.join(sys.argv[sys.argv.index('--delete-secondary')+1:]))
  elif '--create' in sys.argv: do_create(' '.join(sys.argv[sys.argv.index('--create')+1:]))
  elif '--create-secondary' in sys.argv:
      hostname,username,password = secondary_imap_hostname[0],secondary_imap_username[0],secondary_imap_password[0]
      do_create(' '.join(sys.argv[sys.argv.index('--create-secondary')+1:]))
  elif '--copy' in sys.argv: do_copy(' '.join(sys.argv[sys.argv.index('--copy')+1:]))
  elif '--backup' in sys.argv: do_backup()
  elif '--note' in sys.argv: do_note(' '.join(sys.argv[sys.argv.index('--note')+1:]))
  elif '--note-inbox' in sys.argv: do_note(' '.join(sys.argv[sys.argv.index('--note-inbox')+1:]),to_real_inbox=True)
  elif '--maybenote' in sys.argv: do_note(' '.join(sys.argv[sys.argv.index('--maybenote')+1:]),maybe=1)
  elif '--htmlnote' in sys.argv: do_note(' '.join(sys.argv[sys.argv.index('--htmlnote')+1:]),"text/html")
  elif '--multinote' in sys.argv: multinote(sys.argv[sys.argv.index('--multinote')+1:],False)
  elif '--multinote-inbox' in sys.argv: multinote(sys.argv[sys.argv.index('--multinote-inbox')+1:],True)
  elif '--multinote-fname' in sys.argv: multinote(sys.argv[sys.argv.index('--multinote-fname')+1:],False,True)
  elif '--multinote-inbox-fname' in sys.argv: multinote(sys.argv[sys.argv.index('--multinote-inbox-fname')+1:],True,True)
  elif '--upload' in sys.argv: upload(sys.argv[sys.argv.index('--upload')+1:])
  elif '--once' in sys.argv:
      poll_interval = False ; mainloop()
  elif '--fix-archives' in sys.argv: fix_archives_written_by_imapfix_v1_308() # TODO: document this? (use if mutt can't read archives written by v1.308, and some earlier versions, TODO: check which version was the first to have the 'writes a malformed envelope-From' problem)
  elif len(sys.argv)>1:
      sys.stderr.write(imapfix_name+": unrecognised command-line argument\n") ; sys.exit(1)
  elif exit_if_other_running and other_running(): sys.stderr.write("Another "+imapfix_name+" already running - exitting\n(Use "+imapfix_name+" --once if you want to force a run now)\n")
  else: mainloop()
  make_sure_logged_out()
