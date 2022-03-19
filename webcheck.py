#!/usr/bin/env python
# (compatible with both Python 2 and Python 3)

# webcheck.py v1.521 (c) 2014-22 Silas S. Brown.
# See webcheck.html for description and usage instructions

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

# CHANGES
# -------
# If you want to compare this code to old versions, most old
# versions are being kept on SourceForge's E-GuideDog SVN repository
# http://sourceforge.net/p/e-guidedog/code/HEAD/tree/ssb22/setup/
# and on GitHub at https://github.com/ssb22/web-imap-etc
# and on GitLab at https://gitlab.com/ssb22/web-imap-etc
# and on Bitbucket https://bitbucket.org/ssb22/web-imap-etc
# and at https://gitlab.developers.cam.ac.uk/ssb22/web-imap-etc
# and in China: https://gitee.com/ssb22/web-imap-etc
# To check out the repository, you can do:
# git clone https://github.com/ssb22/web-imap-etc.git
# or
# git clone https://gitlab.com/ssb22/web-imap-etc.git
# or
# git clone https://bitbucket.org/ssb22/web-imap-etc.git
# or
# git clone https://gitlab.developers.cam.ac.uk/ssb22/web-imap-etc
# or
# git clone https://gitee.com/ssb22/web-imap-etc
# or
# svn co http://svn.code.sf.net/p/e-guidedog/code/ssb22/setup

max_threads = 10
delay = 2 # seconds
keep_etags = False # if True, will also keep any ETag headers as well as Last-Modified
verify_SSL_certificates = False # webcheck's non-Webdriver URLs are for monitoring public services and there's not a lot of point in SSL authentication; failures due to server/client certificate misconfigurations are more trouble than they're worth

import traceback, time, pickle, gzip, re, os, sys, socket, hashlib
try: import htmlentitydefs # Python 2
except ImportError: import html.entities as htmlentitydefs # Python 3
try: from HTMLParser import HTMLParser # Python 2
except ImportError: # Python 3
  from html.parser import HTMLParser as _HTMLParser
  class HTMLParser(_HTMLParser):
    def __init__(self): _HTMLParser.__init__(self,convert_charrefs=False)
try: from commands import getoutput
except: from subprocess import getoutput
try: import urlparse # Python 2
except ImportError: import urllib.parse as urlparse # Python 3
try: from StringIO import StringIO # Python 2
except: from io import BytesIO as StringIO # Python 3
try: import Queue # Python 2
except: import queue as Queue # Python 3
try: unichr # Python 2
except: unichr,xrange = chr,range # Python 3
try: from urllib2 import quote,HTTPCookieProcessor,HTTPErrorProcessor,build_opener,HTTPSHandler,urlopen,Request,HTTPError,URLError # Python 2
except: # Python 3
  from urllib.parse import quote
  from urllib.request import HTTPCookieProcessor,build_opener,HTTPSHandler,urlopen,Request,HTTPErrorProcessor
  from urllib.error import HTTPError,URLError
def B(s): # byte-string from "" literal
  if type(s)==type("")==type(u""): return s.encode('utf-8') # Python 3
  else: return s # Python 2
def U(s):
  if type(s)==type(u""): return s
  return s.decode('utf-8')
def getBuf(f):
  try: return f.buffer # Python 3
  except: return f # Python 2
try: import ssl
except: # you won't be able to check https:// URLs
  ssl = 0 ; verify_SSL_certificates = False
if '--single-thread' in sys.argv: max_threads = 1 # use --single-thread if something gets stuck and you need Ctrl-C to generate a meaningful traceback
if max_threads > 1:
  try: import thread # Python 2
  except ImportError: import _thread as thread # Python 3

default_filename = "webcheck" + os.extsep + "list"
def read_input_file(fname=default_filename):
  if os.path.isdir(fname): # support webcheck.list etc as a directory
    ret = [] ; files = os.listdir(fname)
    if default_filename in files: # do this one first
      ret += read_input_file(fname+os.sep+default_filename)
      files.remove(default_filename)
    for f in files:
      if f.endswith("~") or f.lower().endswith(".bak"): continue # ignore
      ret += [(l+" # from "+f) for l in read_input_file(fname+os.sep+f)]
    return ret
  try: o = open(fname)
  except: return [] # not a file or resolvable link to one, e.g. lockfile in a webcheck.list dir
  lines = o.read().replace("\r","\n").split("\n")
  lines.reverse() # so can pop() them in order
  return lines
def read_input():
  ret = {} # domain -> { url -> [(days,text)] }
  days = 0 ; extraHeaders = []
  url = mainDomain = None
  lines = read_input_file()
  while lines:
    line = line_withComment = " ".join(lines.pop().split())
    if " #" in line: line = line[:line.index(" #")].strip()
    if not line or line_withComment[0]=='#': continue
    
    if line.startswith(":include"):
      lines += [(l+" # from "+line) for l in read_input_file(line.split(None,1)[1])]
      continue

    if line.endswith(':'): freqCmd = line[:-1]
    else: freqCmd = line
    if freqCmd.lower()=="daily": days = 1
    elif freqCmd.lower()=="weekly": days = 7
    elif freqCmd.lower()=="monthly": days = 30
    elif freqCmd.startswith("days"): days=int(freqCmd.split()[1])
    else: freqCmd = None
    if freqCmd: continue

    if line.startswith("PYTHONPATH="):
      sys.path = line.split("=",1)[1].replace("$PYTHONPATH:","").replace(":$PYTHONPATH","").split(":") + sys.path # for importing selenium etc, if it's not installed system-wide
      continue
    if line.startswith("PATH="):
      os.environ["PATH"] = ":".join(line.split("=",1)[1].replace("$PATH:","").replace(":$PATH","").split(":") + os.environ.get("PATH","").split(":"))
      continue

    if line.startswith('also:') and url:
      text = line_withComment[5:].strip()
      # and leave url and mainDomain as-is (same as above line)
    elif ':' in line and not line.split(':',1)[1].startswith('//'):
      if not line.split(':',1)[1]: # deleting a header
        for e in extraHeaders:
          if e.startswith(line): extraHeaders.remove(e)
      else: extraHeaders.append(line)
      continue
    elif line.startswith("c://") and ' ; ' in line_withComment: # shell command
      url, text = line_withComment.split(' ; ',1)
      # mainDomain = url # if can parallelise
      mainDomain = "" # might be better not to, if it's ssh commands etc
    elif line.startswith('{') and '}' in line_withComment: # webdriver
      actions = line_withComment[1:line_withComment.index('}')].split()
      balanceBrackets(actions)
      text = line_withComment[line_withComment.index('}')+1:].strip()
      mainDomain = '.'.join(urlparse.urlparse(actions[0]).netloc.rsplit('.',2)[-2:]) # assumes 1st action is a URL
      url = "wd://"+chr(0).join(actions)
    else: # not webdriver
      lSplit = line_withComment.split(None,1)
      if len(lSplit)==1: url, text = lSplit[0],"" # RSS only
      else: url, text = lSplit
      mainDomain = '.'.join(urlparse.urlparse(url).netloc.rsplit('.',2)[-2:])
      if extraHeaders: url += '\n'+'\n'.join(extraHeaders)
    ret.setdefault(mainDomain,{}).setdefault(url,[]).append((days,text))
  return ret

def balanceBrackets(wordList):
    "For webdriver instructions: merge adjacent items of wordList so each item has balanced square brackets (currently checks only start and end of each word; if revising this, be careful about use on URLs).  Also checks quotes (TODO: make sure that doesn't interfere with brackets)."
    bracketLevel = 0 ; i = 0
    while i < len(wordList)-1:
        blOld = bracketLevel
        if wordList[i][0] in '["': bracketLevel += 1
        elif not bracketLevel and (('->"' in wordList[i] and not wordList[i].endswith('->"')) or '="' in wordList[i]): bracketLevel += 1
        if wordList[i][-1] in ']"': bracketLevel -= 1
        if bracketLevel > 0:
            wordList [i] += " "+wordList[i+1]
            del wordList[i+1] ; bracketLevel = blOld
        else:
            i += 1 ; bracketLevel = 0

class HTMLStrings(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.theTxt = []
        self.omit = False
    def handle_data(self, data):
        if self.omit or not data: return
        elif not data.strip(): self.ensure(' ')
        else:
          d2 = data.lstrip()
          if not d2==data: self.ensure(' ') # (always collapse multiple spaces, even across tags)
          if d2: self.theTxt.append(re.sub('[ \t\r\n]+',' ',d2.replace(unichr(160).encode('utf-8').decode('latin1'),' ')))
    def ensure(self,thing):
        if self.theTxt and self.theTxt[-1].endswith(thing): return
        self.theTxt.append(thing)
    def handle_starttag(self, tag, attrs):
        if tag in "p br div h1 h2 h3 h4 h5 h6 th tr td table".split(): self.ensure(' ') # space rather than newline because we might want to watch for a string that goes across headings etc
        elif tag in ["script","style"]: self.omit=True
    def handle_endtag(self, tag):
        if tag in ["script","style"]: self.omit=False
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag,attrs)
        self.handle_endtag(tag)
    def unescape(self,attr): return attr # as we don't use attrs above, no point trying to unescape them and possibly falling over if something's malformed
    def handle_charref(self,ref):
        if ref.startswith('x'): self.handle_data(unichr(int(ref[1:],16)).encode('utf-8').decode('latin1'))
        else: self.handle_data(unichr(int(ref)).encode('utf-8').decode('latin1'))
    def handle_entityref(self, ref):
        if ref in htmlentitydefs.name2codepoint:
          self.handle_data(unichr(htmlentitydefs.name2codepoint[ref]).encode('utf-8').decode('latin1'))
        else: self.handle_data(('&'+ref+';'))
    def text(self): return u''.join(self.theTxt).strip()
def htmlStrings(html):
    parser = HTMLStrings()
    try:
        parser.feed(html.decode("latin1")) ; parser.close()
        return parser.text().encode("latin1"), ""
    except: return html, "\n- problem extracting strings from HTML at line %d offset %d\n%s" % (parser.getpos()+(traceback.format_exc(),)) # returning html might still work for 'was that text still there' queries; error message is displayed only if it doesn't

def main():

    # 1 job per domain:
    global jobs ; jobs = Queue.Queue()
    for v in read_input().values(): jobs.put(v)
    
    global previous_timestamps
    try: previous_timestamps = pickle.Unpickler(open(".webcheck-last","rb")).load()
    except: previous_timestamps = {}
    old_previous_timestamps = previous_timestamps.copy()

    for i in xrange(1,max_threads):
        if jobs.empty(): break # enough are going already
        thread.start_new_thread(worker_thread,())
    worker_thread() ; jobs.join()
    
    if previous_timestamps == old_previous_timestamps: return # no point saving if no changes
    try: pickle.Pickler(open(".webcheck-last","wb")).dump(previous_timestamps)
    except: sys.stdout.write("Problem writing .webcheck-last (progress was NOT saved):\n"+traceback.format_exc()+"\n")

def default_opener():
    if sys.version_info >= (2,7,9) and not verify_SSL_certificates: opener = build_opener(HTTPCookieProcessor(),HTTPSHandler(context=ssl._create_unverified_context())) # HTTPCookieProcessor needed for some redirects
    else: opener = build_opener(HTTPCookieProcessor())
    opener.addheaders = [('User-agent', default_ua),
                         ('Accept-Encoding', 'gzip')]
    return opener

default_ua = 'Mozilla/5.0 or whatever you like (actually Webcheck)'
# you can override this on a per-site basis with "User-Agent: whatever"
# and undo again with "User-Agent:" on a line by itself.
# Please override sparingly or with webmaster permission.
# Let's not even mention it in the readme: we don't want to encourage
# people to hide their tools from webmasters unnecessarily.

def worker_thread(*args):
    opener = None
    while True:
      try: job = jobs.get(False)
      except: return # no more jobs left
      try:
        last_fetch_finished = 0 # or time.time()-delay
        for url,daysTextList in sorted(job.items()): # sorted will group http and https together
          if '\n' in url:
              url = url.split('\n')
              extraHeaders = url[1:] ; url = url[0]
          else: extraHeaders = []
          if (url,'lastFetch') in previous_timestamps and not '--test-all' in sys.argv: # (--test-all is different from removing .webcheck.last because it shouldn't also re-output old items in RSS feeds)
              minDays = min(d for d,_ in daysTextList)
              if minDays and previous_timestamps[(url,'lastFetch')]+minDays >= dayNo(): continue
          previous_timestamps[(url,'lastFetch')] = dayNo() # (keep it even if minDays==0, because that might be changed by later edits of webcheck.list)
          time.sleep(max(0,last_fetch_finished+delay-time.time()))
          if sys.stderr.isatty(): sys.stderr.write('.'),sys.stderr.flush()
          if url.startswith("dns://"): # DNS lookup
              try: u,content = None, B(' '.join(sorted(set('('+x[-1][0]+')' for x in socket.getaddrinfo(url[6:],1))))) # TODO this 'sorted' is lexicographical not numeric; it should be OK for most simple cases though (keeping things in a defined order so can check 2 or 3 IPs on same line if the numbers are consecutive and hold same number of digits).  Might be better if parse and numeric sort
              except: u,content=None,B("DNS lookup failed")
              textContent = content
          elif url.startswith("wd://"): # run webdriver (this type of url is set internally: see read_input)
              u,content = None, run_webdriver(url[5:].split(chr(0)))
              textContent = None # parse 'content' if needed
              url = url[5:].split(chr(0),1)[0] # for display
          elif url.startswith("up://"): # just test if server is up, and no error if not
              try:
                if sys.version_info >= (2,7,9) and not verify_SSL_certificates: urlopen(url[5:],context=ssl._create_unverified_context(),timeout=60)
                else: urlopen(url[5:],timeout=60)
                u,content = None,B("yes")
              except: u,content = None,B("no")
              textContent = content
          elif url.startswith("e://"): # run edbrowse
              from subprocess import Popen,PIPE
              edEnv=os.environ.copy() ; edEnv["TMPDIR"]=getoutput("(TMPDIR=/dev/shm mktemp -d -t ed || mktemp -d -t ed) 2>/dev/null") # ensure unique cache dir if we're running several threads (TODO: what about edbrowse 3.7.6 and below, which hard-codes a single cache dir in /tmp: had we better ensure only one of these is run at a time, just in case?  3.7.7+ honours TMPDIR)
              try: child = Popen(["edbrowse","-e"],-1,stdin=PIPE,stdout=PIPE,stderr=PIPE,env=edEnv)
              except OSError:
                print ("webcheck misconfigured: couldn't run edbrowse")
                continue # no need to update last_fetch_finished
              u,(content,stderr) = None,child.communicate(B("b "+url[4:].replace('\\','\n')+"\n,p\nqt\n")) # but this isn't really the page source (asking edbrowse for page source would be equivalent to fetching it ourselves; it doesn't tell us the DOM)
              try:
                import shutil
                shutil.rmtree(edEnv["TMPDIR"])
              except: pass
              if child.returncode:
                print ("edbrowse failed on "+url)
                # Most likely the failure was some link didn't exist when it should have, so show the output for debugging
                print ("edbrowse output was: "+repr(content)+"\n")
                last_fetch_finished = time.time()
                continue
              textContent = content.replace(B('{'),B(' ')).replace(B('}'),B(' ')) # edbrowse uses {...} to denote links
              url = url[4:].split('\\',1)[0] # for display
          elif url.startswith("c://"): # run command
              content = getoutput(url[len("c://"):])
              u = textContent = None
          elif url.startswith("blocks-lynx://"):
              r=Request(url[len("blocks-lynx://"):])
              r.get_method=lambda:'HEAD'
              r.add_header('User-agent','Lynx/2.8.9dev.4 libwww-FM/2.14')
              u,content = None,B("no") # not blocking Lynx?
              try: urlopen(r,timeout=60)
              except Exception as e:
                if type(e) in [HTTPError,socket.error,socket.timeout,ssl.SSLError]: # MIGHT be blocking Lynx (SSLError can be raised if hit the timeout), check:
                  r.add_header('User-agent',default_ua)
                  try:
                    urlopen(r,timeout=60)
                    content = B("yes") # error ONLY with Lynx, not with default UA
                  except Exception as e: pass # error with default UA as well, so don't flag this one as a Lynx-test failure
                else:
                  print ("Info: "+url+" got "+str(type(e))+" (check the server exists at all?)")
                  try: print (e.message)
                  except: pass
              textContent = content
          elif url.startswith("head://"):
              r=Request(url[len("head://"):])
              r.get_method=lambda:'HEAD'
              for h in extraHeaders: r.add_header(*tuple(x.strip() for x in h.split(':',1)))
              if not any(h.lower().startswith("user-agent:") for h in extraHeaders): r.add_header('User-agent',default_ua)
              u=None
              if sys.version_info >= (2,7,9) and not verify_SSL_certificates: content=textContent=B(str(urlopen(r,context=ssl._create_unverified_context(),timeout=60).info()))
              else: content=textContent=B(str(urlopen(r,timeout=60).info()))
          elif url.startswith("gemini://"):
              u = None
              content,textContent = get_gemini(url)
          else: # normal URL
              if opener==None: opener = default_opener()
              u,content = tryRead(url,opener,extraHeaders,all(t and not t.startswith('#') for _,t in daysTextList)) # don't monitorError for RSS feeds (don't try to RSS-parse an error message)
              textContent = None
          last_fetch_finished = time.time()
          if content==None: continue # not modified (so nothing to report), or problem retrieving (which will have been reported by tryRead0)
          if u:
              lm = u.info().get("Last-Modified",None)
              if lm: previous_timestamps[(url,'lastMod')] = lm
              if keep_etags:
                e = u.info().get("ETag",None)
                if e: previous_timestamps[(url,'ETag')] = e
          for _,t in daysTextList:
              if t.startswith('>'):
                  check(t[1:],content,"Source of "+url,"")
              elif not t or t.startswith('#'):
                  parseRSS(url,content,t.replace('#','',1).strip())
              else:
                if textContent==None:
                  textContent,errmsg=htmlStrings(content)
                else: errmsg = ""
                check(t,textContent,url,errmsg)
      except Exception as e:
        print ("Unhandled exception processing job "+repr(job))
        print (traceback.format_exc())
      jobs.task_done()

class NoTracebackException(Exception): pass
def run_webdriver(actionList):
    global webdriver # so run_webdriver_inner has it
    try: from selenium import webdriver
    except:
        print ("webcheck misconfigured: can't import selenium (did you forget to set PYTHONPATH?)")
        return B("")
    try:
      from selenium.webdriver.chrome.options import Options
      opts = Options()
      opts.add_argument("--headless")
      opts.add_argument("--disable-gpu")
      opts.add_argument("--user-agent="+default_ua)
      try: from inspect import getfullargspec as getargspec # Python 3
      except ImportError:
        try: from inspect import getargspec # Python 2
        except ImportError: getargspec = None
      try: useOptions = 'options' in getargspec(webdriver.chrome.webdriver.WebDriver.__init__).args
      except: useOptions = False
      if useOptions: browser = webdriver.Chrome(options=opts)
      else: browser = webdriver.Chrome(chrome_options=opts)
    except Exception as eChrome: # probably no HeadlessChrome, try PhantomJS
      os.environ["QT_QPA_PLATFORM"]="offscreen"
      sa = ['--ssl-protocol=any']
      if not verify_SSL_certificates: sa.append('--ignore-ssl-errors=true')
      try: browser = webdriver.PhantomJS(service_args=sa,service_log_path=os.path.devnull)
      except Exception as jChrome:
        print ("webcheck misconfigured: can't create either HeadlessChrome (%s) or PhantomJS (%s).  Check installation.  (PATH=%s, cwd=%s, webdriver version %s)" % (str(eChrome),str(jChrome),repr(os.environ.get("PATH","")),repr(os.getcwd()),repr(webdriver.__version__)))
        return B("")
    r = ""
    try: r = run_webdriver_inner(actionList,browser)
    except NoTracebackException as e: print (e.message)
    except: print (traceback.format_exc())
    browser.quit()
    return r

def run_webdriver_inner(actionList,browser):
    browser.set_window_size(1024, 768)
    browser.implicitly_wait(2) # we have our own 'wait for text' and delay values, so the implicit wait does not have to be too high
    def findElem(spec):
        if spec.startswith('#'):
            try: return browser.find_element_by_id(spec[1:])
            except: return browser.find_element_by_name(spec[1:])
        elif spec.startswith('.'):
          if '#' in spec: return browser.find_elements_by_class_name(spec[1:spec.index('#')])[int(spec.split('#')[1])-1] # .class#1, .class#2 etc to choose the Nth element of that class
          else: return browser.find_element_by_class_name(spec[1:])
        else: return browser.find_element_by_link_text(spec)
    def getSrc():
      def f(b,switchBack=[]):
        try: src = b.find_element_by_xpath("//*").get_attribute("outerHTML")
        except: return u"getSrc webdriver exception but can retry" # can get timing-related WebDriverException: Message: Error - Unable to load Atom 'find_element'
        for el in ['frame','iframe']:
          for frame in b.find_elements_by_tag_name(el):
            b.switch_to.frame(frame)
            src += f(b,switchBack+[frame])
            b.switch_to.default_content()
            for fr in switchBack: b.switch_to.frame(fr)
        return src
      return f(browser).encode('utf-8')
    snippets = []
    for a in actionList:
        if a.startswith('http'): browser.get(a)
        elif a.startswith('"') and a.endswith('"'):
            # wait for "string" to appear in the source
            tries = 30
            while tries and not myFind(a[1:-1],getSrc()):
              time.sleep(delay) ; tries -= 1
            if not tries: raise NoTracebackException("webdriver timeout while waiting for %s, current URL is %s content \"%s\"\n" % (repr(a[1:-1]),browser.current_url,repr(getSrc()))) # don't quote current URL: if the resulting email is viewed in (at least some versions of) MHonArc, a bug can result in &quot being added to the href
        elif a.startswith('[') and a.endswith(']'): # click
            findElem(a[1:-1]).click()
        elif a.startswith('/') and '/' in a[1:]: # click through items in a list to reveal each one (assume w/out Back)
            start = a[1:a.rindex('/')]
            delayAfter = int(a[a.rindex('/')+1:])
            if start.startswith('.'): # TODO: document this: /.class/delay to match an exact class rather than the start of an ID, also /.class.closeClass/delay if it pops up a 'modal' box which then needs to be dismissed before clicking the next one
              startClass = start[1:]
              if '.' in startClass: startClass,closeClass = startClass.split('.')
              else: closeClass = None
              for m in browser.find_elements_by_class_name(startClass):
                try: m.click()
                except: continue # can't click on that one for some reason (don't propagate exception here because the partial output will likely help diagnose)
                if sys.stderr.isatty(): sys.stderr.write('*'),sys.stderr.flush() # webdriver's '.' for click-multiple
                time.sleep(delayAfter)
                snippets.append(getSrc())
                if closeClass:
                  for c in browser.find_elements_by_class_name(closeClass):
                    try: c.click()
                    except: pass # maybe it wasn't that one
                  if sys.stderr.isatty(): sys.stderr.write('x'),sys.stderr.flush()
                  time.sleep(delayAfter)
            else:
             l = re.findall(B(' [iI][dD] *="('+re.escape(start)+'[^"]*)'),getSrc()) + re.findall(B(' [iI][dD] *=('+re.escape(start)+'[^"> ]*)'),getSrc())
             for m in l:
              browser.find_element_by_id(m).click()
              if sys.stderr.isatty(): sys.stderr.write('*'),sys.stderr.flush() # webdriver's '.' for click-multiple
              time.sleep(delayAfter)
              snippets.append(getSrc())
        elif '->' in a: # set a selection box
            spec, val = a.split('->',1)
            e = webdriver.support.ui.Select(findElem(spec))
            if val.startswith('"') and val.endswith('"'): val=val[1:-1]
            if val: e.select_by_visible_text(val)
            else: e.deselect_all()
        elif a.endswith('*0'): # clear a checkbox
            e = findElem(a[:-2])
            if e.is_selected(): e.click()
        elif a.endswith('*1'): # check a checkbox
            e = findElem(a[:-2])
            if not e.is_selected(): e.click()
        elif '=' in a: # put text in an input box
            spec, val = a.split('=',1)
            if val.startswith('"') and val.endswith('"'): val=val[1:-1]
            findElem(spec).send_keys(val)
        else: sys.stdout.write("Ignoring webdriver unknown action "+repr(a)+'\n')
        if sys.stderr.isatty(): sys.stderr.write(':'),sys.stderr.flush() # webdriver's '.'
        time.sleep(delay)
    snippets.append(getSrc())
    return B('\n').join(snippets)

def get_gemini(url,nestLevel=0):
    if nestLevel > 9: return B("Too many redirects"),B("Too many redirects")
    url = B(url)
    host0 = host = re.match(B("gemini://([^/?#]*)"),url).groups(1)[0]
    port = re.match(B(".*:([0-9]+)$"),host)
    if port:
        port = int(port.groups(1)[0])
        host = host[:host.rindex(B(":"))]
    else: port = 1965
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.settimeout(60) ; s=ssl.wrap_socket(s)
    s.connect((host,port)) ; s.send(url+B("\r\n"))
    g=[]
    while not g or g[-1]: g.append(s.recv())
    s.close() ; g=B("").join(g)
    if B("\r\n") in g:
        header,body = g.split(B("\r\n"),1)
    else: header,body = g,B("")
    if B(" ") in header: status,meta = header.split(B(" "),1)
    else: status,meta = B("?"),header
    try: status = int(status)
    except: status = 0
    if 20 <= status <= 29:
        if meta.startswith(B("text/gemini")):
            txtonly = re.sub(B("\n *=> +[^ ]*"),B("\n"),body)
        elif B("html") in meta: txtonly = None # will result in htmlStrings
        else: txtonly = body
        return body,txtonly
    elif 30 <= status <= 39:
        if meta.startswith(B("gemini://")):
            return get_gemini(meta,nestLevel+1)
        elif meta.startswith(B("/")):
            return get_gemini(B("gemini://")+host0+meta,nestLevel+1)
        else: return get_gemini(url[:url.rindex(B("/"))+1]+meta,nestLevel+1) # TODO: handle ../ ourselves?  or let server do it?  (early protocol specification and practice unclear)
    else: return meta,meta # input prompt, error message, or certificate required

def dayNo(): return int(time.mktime(time.localtime()[:3]+(0,)*6))/(3600*24)

def tryRead(url,opener,extraHeaders,monitorError=True,refreshTry=5):
    oldAddHeaders = opener.addheaders[:]
    for h in extraHeaders:
        if h.lower().startswith("user-agent") and opener.addheaders[0][0]=="User-agent": del opener.addheaders[0] # User-agent override (will be restored after by oldAddHeaders) (TODO: override in run_webdriver also)
        opener.addheaders.append(tuple(x.strip() for x in h.split(':',1)))
    if (url,'lastMod') in previous_timestamps and not '--test-all' in sys.argv:
        opener.addheaders.append(("If-Modified-Since",previous_timestamps[(url,'lastMod')]))
    if keep_etags and (url,'ETag') in previous_timestamps and not '--test-all' in sys.argv:
        opener.addheaders.append(("If-None-Match",previous_timestamps[(url,'lastMod')]))
    ret = tryRead0(url,opener,monitorError)
    opener.addheaders = oldAddHeaders
    if refreshTry: # meta refresh redirects
      u,content = ret
      if content: m = re.search(br'(?is)<head>.*?<meta http-equiv="refresh" content="0; *url=([^"]*)".*?>.*?</head>',content) # TODO: if string found, remove comments and re-check (or even parse properly) ?
      else: m = None # content==None if 304 not modified
      if m:
        m = m.groups(1)[0]
        if type(u"")==type(""): m=m.decode('latin1')
        return tryRead(urlparse.urljoin(url,m),opener,extraHeaders,monitorError,refreshTry-1)
    return ret

def tryRead0(url,opener,monitorError):
    url = re.sub("[^!-~]+",lambda m:quote(m.group()),url) # it seems some versions of the library do this automatically but others don't
    u = None
    try:
        u = opener.open(url,timeout=60)
        return u,tryGzip(u.read())
    except HTTPError as e:
        if e.code==304: return None,None # not modified
        elif monitorError: return None,tryGzip(e.fp.read()) # as might want to monitor some phrase on a 404 page
        sys.stdout.write("Error "+str(e.code)+" retrieving "+linkify(url)+"\n") ; return None,None
    except: # try it with a fresh opener and no headers
        try:
            if sys.version_info >= (2,7,9) and not verify_SSL_certificates: u = build_opener(OurRedirHandler(),HTTPCookieProcessor(),HTTPSHandler(context=ssl._create_unverified_context())).open(url,timeout=60)
            else: u = build_opener(OurRedirHandler(),HTTPCookieProcessor()).open(url,timeout=60)
            return u,tryGzip(u.read())
        except HTTPError as e:
          if monitorError: return u,tryGzip(e.fp.read())
          sys.stdout.write("Error "+str(e.code)+" retrieving "+linkify(url)+"\n") ; return None,None
        except URLError as e: # don't need full traceback for URLError, just the message itself
            sys.stdout.write("Problem retrieving "+linkify(url)+"\n"+str(e)+"\n")
            return None,None
        except socket.timeout:
            sys.stdout.write("Timed out retrieving "+linkify(url)+"\n")
            return None,None
        except: # full traceback by default
            sys.stdout.write("Problem retrieving "+linkify(url)+"\n"+traceback.format_exc())
            return None,None
class OurRedirHandler(HTTPErrorProcessor):
  def __init__(self,nestLevel=0): self.nestLevel = nestLevel
  def our_response(self,request,response,prefix):
    try: code=response.code
    except: return response
    if code not in [301,302,303,307]: return response
    url = re.sub("[^!-~]+",lambda m:quote(m.group()),response.headers['Location']) # not all versions of the library do this, so we'll do it here if simple-open failed
    if self.nestLevel>9: raise Exception("too many redirects")
    if url.startswith("//"): url=prefix+url
    if sys.version_info >= (2,7,9) and not verify_SSL_certificates: return build_opener(OurRedirHandler(self.nestLevel+1),HTTPCookieProcessor(),HTTPSHandler(context=ssl._create_unverified_context())).open(url,timeout=60)
    else: return build_opener(OurRedirHandler(self.nestLevel+1),HTTPCookieProcessor()).open(url,timeout=60)
  def http_response(self,request,response):
    return self.our_response(request,response,"http:")
  def https_response(self,request,response):
    return self.our_response(request,response,"https:")

def tryGzip(t):
    try: return gzip.GzipFile('','rb',9,StringIO(t)).read()
    except: return t

def check(text,content,url,errmsg):
    if ' #' in text: text,comment = text.split(' #',1) # (comments must be preceded by a space, otherwise interpreted as part of the text as this is sometimes needed in codes)
    else: comment = ""
    orig_comment = comment = comment.strip()
    if comment: comment="\n  "+paren(comment)
    text = text.strip()
    assert text # or should have gone to parseRSS instead
    if text.startswith('{') and text.endswith('}') and '...' in text: extract(url,content,text[1:-1].split('...'),orig_comment)
    elif text.startswith("!"): # 'not', so alert if DOES contain
        if len(text)==1: return # TODO: print error?
        if myFind(text[1:],content):
            sys.stdout.write(url+" contains "+text[1:]+comment+errmsg+"\n") # don't use 'print' or can have problems with threads
    elif not myFind(text,content): # alert if DOESN'T contain
        sys.stdout.write(linkify(url)+" no longer contains "+text+comment+errmsg+"\n")
        if '??show?' in orig_comment: getBuf(sys.stdout).write(content+B('\n')) # TODO: document this (for debugging cases where the text shown in Lynx is not the text shown to Webcheck, and Webcheck says "no longer contains" when it still does)

def parseRSS(url,content,comment):
  from xml.parsers import expat
  parser = expat.ParserCreate()
  items = [[[],[],[],[]]] ; curElem = [None]
  def StartElementHandler(name,attrs):
    if name in ['item','entry']: items.append([[],[],[],[]])
    if name=='title': curElem[0]=0
    elif name=='link': curElem[0]=1
    elif name in ['description','summary']: curElem[0]=2
    elif name=='pubDate': curElem[0]=3
    else: curElem[0]=None
    if name=='link' and 'href' in attrs: # (note this isn't the ONLY way an href could get in: <link>http...</link> is also possible, and is handled by CharacterDataHandler below, hence EndElementHandler is important for separating links)
      items[-1][curElem[0]].append(attrs['href']+' ')
  def EndElementHandler(name):
    if name in ['item','entry']: # ensure any <link>s outside <item>s are separated
      items.append([[],[],[],[]])
      curElem[0]=None
    elif name in ['description','summary','title','link']:
      if not curElem[0]==None: items[-1][curElem[0]].append(' ') # ensure any additional ones are space-separated
      curElem[0]=None
  def CharacterDataHandler(data):
    if data and not curElem[0]==None:
      items[-1][curElem[0]].append(data)
  parser.StartElementHandler = StartElementHandler
  parser.EndElementHandler = EndElementHandler
  parser.CharacterDataHandler = CharacterDataHandler
  if type(u"")==type(""): content = content.decode("utf-8") # Python 3 (expat needs 'strings' on each platform)
  try: parser.Parse(re.sub("&[A-Za-z]*;",entityref,content),1)
  except expat.error as e: sys.stdout.write("RSS parse error in "+url+paren(comment)+":\n"+repr(e)+"\n(Check if this URL is still serving RSS?)\n\n") # and continue with handleRSS ?  (it won't erase our existing items if the new list is empty, as it will be in the case of the parse error having been caused by a temporary server error)
  for i in xrange(len(items)):
    items[i][1] = "".join(urlparse.urljoin(url,w) for w in "".join(items[i][1]).strip().split()).strip() # handle links relative to the RSS itself
    for j in [0,2,3]: items[i][j]=re.sub(r"\s+"," ",u"".join(U(x) for x in items[i][j])).strip()
  handleRSS(url,items,comment)
def entityref(m):
  m=m.group()[1:-1] ; m2 = None
  try: m2=unichr(htmlentitydefs.name2codepoint[m])
  except:
    try:
      if m.startswith("#x"): m2=unichr(int(m[2:],16))
      elif m.startswith("#"): m2=unichr(int(m[1:]))
    except: pass
  if m2 and not m2 in "<>&":
    if type(u"")==type(""): return m2
    else: return m2.encode('utf-8')
  return "&"+m+";"
def paren(comment):
  comment = " ".join(comment.replace("??track-links-only?","").split())
  if not comment or (comment.startswith('(') and comment.endswith(')')): return comment
  else: return " ("+comment+")"
def handleRSS(url,items,comment,itemType="RSS/Atom"):
  newItems = [] ; pKeep = set()
  for title,link,txt,date in items:
    if not title: continue # valid entry must have title
    if "??track-links-only?" in comment: hashTitle,hashTxt = date,"" # TODO: document this, it's for when text might change because for example we're fetching it through an add-annotation CGI that can change, but don't ignore if the publication date has changed due to an update (TODO: might be better to do this via a 'pipe to postprocessing' option instead?)
    else: hashTitle,hashTxt = title,re.sub("</?[A-Za-z][^>]*>","",txt) # (ignore HTML markup in RSS, since it sometimes includes things like renumbered IDs)
    k = (url,'seenItem',hashlib.md5(repr((hashTitle,link,hashTxt)).encode("utf-8")).digest()) # TODO: option not to call hashlib, in case someone has the space and is concerned about the small probability of hash collisions?  (The Python2-only version of webcheck just used Python's built-in hash(), but in Python 3 that is no longer stable across sessions, so use md5)
    pKeep.add(k)
    if k in previous_timestamps and not '--show-seen-rss' in sys.argv: continue # seen this one already
    previous_timestamps[k] = True
    txt = re.sub("&#x([0-9A-Fa-f]*);",lambda m:unichr(int(m.group(1),16)),re.sub("&#([0-9]*);",lambda m:unichr(int(m.group(1))),txt)) # decode &#..; HTML entities (sometimes used for CJK), but leave &lt; etc as-is (in RSS it would have originated with a double-'escaped' < within 'escaped' html markup)
    txt = re.sub("</?[A-Za-z][^>]*>",simplifyTag,txt) # avoid overly-verbose HTML (but still allow some)
    txt = re.sub("<[pP]></[pP]>","",txt).strip() # sometimes left after simplifyTag removes img
    if txt: txt += '\n'
    newItems.append(title+'\n'+txt+linkify(link))
  if not pKeep: return # if the feed completely failed to fetch, don't erase what we have
  for k in list(previous_timestamps.keys()):
    if k[:2]==(url,'seenItem') and not k in pKeep:
      del previous_timestamps[k] # dropped from the feed
  if newItems: getBuf(sys.stdout).write((str(len(newItems))+" new "+itemType+" items in "+url+paren(comment)+' :\n'+'\n---\n'.join(n.strip() for n in newItems)+'\n\n').encode('utf-8'))
def simplifyAttr(match):
  m = match.group()
  if m.lower().startswith(" href="): return m
  else: return ""
def simplifyTag(match):
  m = match.group()
  t = m.split()[0].replace('<','').replace('>','').replace('/','')
  if t=='a': return re.sub(' [A-Za-z]+="[^"]*"',simplifyAttr,m)
  elif t in ['p','br','em','strong','b','i','u','s']:
    if ' ' in m: return m.split()[0]+'>' # strip attributes
    else: return m
  else: return "" # strip entire tag
def linkify(link): return link.replace("(","%28").replace(")","%29") # for email clients etc that terminate URLs at parens

def extract(url,content,startEndMarkers,comment):
  assert len(startEndMarkers)==2, "Should have exactly one '...' between the braces when extracting items"
  start,end = startEndMarkers
  start,end = B(start),B(end)
  i=0 ; items = []
  while True:
    i = content.find(start,i)
    if i==-1: break
    j = content.find(end,i+len(start))
    if j==-1: break
    c = content[i+len(start):j].decode('utf-8').strip()
    if c: items.append(('Auto-extracted text:','',c,"")) # NB the 'title' field must not be empty (unless we relocate that logic to parseRSS instead of handleRSS)
    i = j+len(end)
  if not items: print ("No items were extracted from "+url+" via "+start+"..."+end+" (check that site changes haven't invalidated this extraction rule)")
  handleRSS(url,items,comment,"extracted")

def myFind(text,content):
  text,content = B(text),B(content)
  if text[:1]==B("*"): return re.search(text[1:],content)
  elif text in content: return True
  return normalisePunc(text) in normalisePunc(content)
def normalisePunc(t):
  "normalise apostrophes; collapse (but don't ignore) whitespace and &nbsp; ignore double-quotes because they might have been <Q> elements; fold case"
  for s,r in [
      (u"\u2013".encode('utf-8'),B("-")), # en-dash
      (u"\u2019".encode('utf-8'),B("'")),
      (u"\u2018".encode('utf-8'),B("'")),
      (u"\u201C".encode('utf-8'),B("")),
      (u"\u201D".encode('utf-8'),B("")),
      (B('"'),B("")),
      (u"\u00A0".encode('utf-8'),B(" ")),
      (u"\uFEFF".encode('utf-8'),B("")),
      (u"\u200B".encode('utf-8'),B(""))
      ]: t=t.replace(s,r)
  return re.sub(B(r"(\s)\s+"),B(r"\1"),t).lower()

if __name__=="__main__": main()
