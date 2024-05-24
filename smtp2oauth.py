#!/usr/bin/env python3

# smtp2oauth.py: for when you have an SMTP account
# that requires OAUTH2 (e.g. Exchange), and a
# client (possibly mobile) that can take only a
# fixed password.  Serves TLS SMTP with password
# access, and forwards using your OAUTH2.  You are
# responsible for ensuring the security of this.

# v1.0 (c) 2024 Silas S. Brown.  License: Apache 2

# This is a Python 3 program.
# It is NOT compatible with Python 2.

# You might need to run this with sudo, so as to
# open the port and read the TLS key files.  Set
# uid_to_set to release privileges afterwards.

smtp587 = "smtp.example.net" # port 587 assumed
oauth_usr = "whoever@example.net"
oauth_cmd = "./oauth2.py myToken"
localUser = "whoever"
localPass = "set this to a STRONG password!"
# Suggested: LC_ALL=C tr -c -d '[:alnum:]' < /dev/random|head -c 64
# - you don't want villains to be able to brute
# force it without you noticing the traffic first
localHost = "home-server.example.org"
fullchain_pem="/etc/letsencrypt/live/home-server.example.org/fullchain.pem"
key_pem="/etc/letsencrypt/live/home-server.example.org/privkey.pem"
uid_to_set = 1000 # or None: call setuid() after reading the above and opening the port
homedir_to_set = "/home/whoever" # ditto
from smtp2oauth_config import * # put your settings into smtp2oauth_config.py to override the above

# ------------------------------------------------

from aiosmtpd.controller import Controller # pip install aiosmtpd
from aiosmtpd.smtp import AuthResult, LoginPassword, SMTP
import asyncio,smtplib,ssl,base64,sys,os,re
from subprocess import getoutput
from time import asctime

class Authenticator:
    def __call__(self,_1,_2,_3,aType,auth): return AuthResult(success=aType in ("LOGIN","PLAIN") and isinstance(auth,LoginPassword) and (auth.login,auth.password)==(localUser.encode('latin1'),localPass.encode('latin1')), handled=False)

def getSMTP():
    access_bytes # if not set yet, genAuth first
    s = smtplib.SMTP(smtp587,587) ; s.ehlo()
    s.starttls(context=ssl.create_default_context())
    s.ehlo() ; s.docmd('AUTH','XOAUTH2')
    return s, s.docmd(base64.b64encode(access_bytes).decode('latin1'))

def genAuth():
    global access_bytes
    access_bytes = getoutput(oauth_cmd+" 2>/dev/null").strip().encode('latin1')
    if re.match(b"[A-Za-z0-9/+]+=*$",access_bytes): access_bytes = base64.decodebytes(access_bytes)
    if not access_bytes.startswith(b"user="): access_bytes=b"user="+oauth_usr.encode('latin1')+b"\x01auth=Bearer "+access_bytes+b"\x01\x01"

def log(*args): print(*args),sys.stdout.flush()

class Handler:
    async def handle_DATA(self, server, session, envelope):
        try: s,ret = getSMTP()
        except: s,ret = 0,(0,b"unsuccessful")
        if b"unsuccessful" in ret[1]:
            try: s.quit()
            except: pass
            genAuth() # regenerate
            s,ret = getSMTP()
            if b"unsuccessful" in ret[1]:
                raise Exception(ret[1].decode('latin1')) # this will propagate to the SMTP client
        s.sendmail(
            from_addr=envelope.mail_from,
            to_addrs=envelope.rcpt_tos,
            msg=envelope.original_content)
        log("Sent to",", ".join(envelope.rcpt_tos),"from",session.peer,asctime())
        return b'250 OK'
    async def handle_exception(self, error):
        try: peer = self.session.peer # works if we're in the SMTP object (see assignment below)
        except: peer="" # future versions might not take this override; peer is logged by default if we have no handle_exception, but so is a very verbose traceback
        log(f"Denying {repr(peer)}{' ' if peer else ''}due to {repr(error)}",asctime()) # It's most likely a Linode/CariNet/etc trial tenant probing for open SMTP relays and causing tracebacks in STARTTLS
        return '500 Nope'
SMTP.handle_exception = Handler.handle_exception

def main():
    loop = asyncio.new_event_loop()
    loop.set_exception_handler(handleException)
    asyncio.set_event_loop(loop)
    loop.create_task(amain())
    try:
        loop.run_forever()
        log("smtp2oauth stopping due to exception",asctime())
        raise exception # set by handleException
    except KeyboardInterrupt: log(" smtp2oauth shutdown") # typically printed after "^C"
def handleException(loop,context):
    global exception
    exception = context.get('exception')
    loop.stop()
async def amain():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(fullchain_pem,key_pem)
    cont = Controller(Handler(),
                      tls_context=context,
                      hostname="0.0.0.0",
                      port=587, # not 465 because we do STARTTLS
                      server_hostname=localHost,
                      ident="private SMTP server: account needed!",
                      require_starttls=True,
                      auth_required=True,
                      data_size_limit=150*1048576,
                      authenticator=Authenticator())
    cont.start()
    if uid_to_set: os.setuid(uid_to_set)
    if homedir_to_set: os.environ["HOME"]=homedir_to_set
    log("smtp2oauth started",asctime())

if __name__ == '__main__': main()
