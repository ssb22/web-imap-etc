
# webcheck.py v1.02 (c) 2014 Silas S. Brown.  License: GPL
# See website for description and usage instructions

# CHANGES
# -------
# If you want to compare this code to old versions, most old
# versions are being kept on SourceForge's E-GuideDog SVN repository
# http://sourceforge.net/p/e-guidedog/code/HEAD/tree/ssb22/setup/
# To check out the repository, you can do:
# svn co http://svn.code.sf.net/p/e-guidedog/code/ssb22/setup

max_threads = 10
delay = 2 # seconds

import htmlentitydefs, traceback, HTMLParser, urllib2, urlparse, time, pickle, gzip, StringIO, re, Queue, sys
if max_threads > 1: import thread

def read_input():
  ret = {} # domain -> { url -> [(days,text)] }
  days = 0
  for line in open("webcheck.list").read().replace("\r","\n").split("\n"):
    line = line.strip()
    if not line or line[0]=='#': continue

    if line.endswith(':'): freqCmd = line[:-1]
    else: freqCmd = line
    if freqCmd.lower()=="daily": days = 1
    elif freqCmd.lower()=="weekly": days = 7
    elif freqCmd.lower()=="monthly": days = 30
    elif freqCmd.startswith("days"): days=int(freqCmd.split()[1])
    else: freqCmd = None
    if freqCmd: continue
    
    url, text = line.split(None,1)
    mainDomain = '.'.join(urlparse.urlparse(url).netloc.rsplit('.',2)[-2:])
    if not mainDomain in ret:
        ret[mainDomain] = {}
    if not url in ret[mainDomain]:
        ret[mainDomain][url] = []
    ret[mainDomain][url].append((days,text))
  return ret

class HTMLStrings(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.theTxt = []
    def handle_data(self, data):
        if not data: return
        elif not data.strip(): self.ensure(' ')
        else:
          d2 = data.lstrip()
          if not d2==data: self.ensure(' ') # (always collapse multiple spaces, even across tags)
          if d2: self.theTxt.append(re.sub('[ \t\r\n]+',' ',d2.replace(unichr(160).encode('utf-8'),' ')))
    def ensure(self,thing):
        if self.theTxt and self.theTxt[-1].endswith(thing): return
        self.theTxt.append(thing)
    def handle_starttag(self, tag, attrs):
        if tag in "p br div h1 h2 h3 h4 h5 h6 tr td table".split(): self.ensure(' ') # space rather than newline because we might want to watch for a string that goes across headings etc
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag,attrs)
    def handle_charref(self,ref):
        if ref.startswith('x'): self.handle_data(unichr(int(ref[1:],16)).encode('utf-8'))
        else: self.handle_data(unichr(int(ref)).encode('utf-8'))
    def handle_entityref(self, ref):
        if ref in htmlentitydefs.name2codepoint: self.handle_data(unichr(htmlentitydefs.name2codepoint[ref]).encode('utf-8'))
        else: self.handle_data('&'+ref+';')
    def text(self): return ''.join(self.theTxt).strip()
def htmlStrings(text):
    try:
        parser = HTMLStrings()
        parser.feed(text) ; parser.close()
        return parser.text()
    except:
        sys.stdout.write("Problem extracting strings from HTML\n"+traceback.format_exc())
        return text # might still work for 'was that text still there' queries

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
    except: pass # ignore if can't write etc

def worker_thread(*args):
    opener = None
    while True:
        try: job = jobs.get(False)
        except: return # no more jobs left
        if opener==None:
            opener = urllib2.build_opener()
            opener.addheaders = [('User-agent',
                                  'Mozilla/5.0'), # TODO: ?
                         ('Accept-Encoding', 'gzip')]
        last_fetch_finished = 0 # or time.time()-delay
        for url,daysTextList in sorted(job.items()): # sorted will group http and https together
          if (url,'lastFetch') in previous_timestamps:
              minDays = min(d for d,_ in daysTextList)
              if minDays and previous_timestamps[(url,'lastFetch')]+minDays >= dayNo(): continue
          previous_timestamps[(url,'lastFetch')] = dayNo() # (keep it even if minDays==0, because that might be changed by later edits of webcheck.list)
          time.sleep(max(0,last_fetch_finished+delay-time.time()))
          u,content = tryRead(url,opener)
          last_fetch_finished = time.time()
          if content==None: continue # not modified
          if u:
              lm = u.info().getheader("Last-Modified",None)
              if lm: previous_timestamps[(url,'lastMod')] = lm
          textContent = None
          for _,t in daysTextList:
              if t.startswith('>'):
                  check(t[1:],content,"Source of "+url)
                  continue
              elif textContent==None:
                  textContent = htmlStrings(content)
              check(t,textContent,url)
        jobs.task_done()

def dayNo(): return int(time.mktime(time.localtime()[:3]+(0,)*6))/(3600*24)

def tryRead(url,opener):
    if (url,'lastMod') in previous_timestamps:
        opener.addheaders.append(("If-Modified-Since",previous_timestamps[(url,'lastMod')]))
        ret = tryRead0(url,opener)
        opener.addheaders.pop()
        return ret
    else: return tryRead0(url,opener)

def tryRead0(url,opener):
    u = None
    try:
        u = opener.open(url).read()
        return u,tryGzip(u.read())
    except urllib2.HTTPError, e:
        if e.code==304: return None,None # not modified
        return None,tryGzip(e.fp.read()) # as might want to monitor some phrase on a 404 page
    except: # try it with a fresh opener and no headers
        try:
            u = urllib2.build_opener().open(url)
            return u,tryGzip(u.read())
        except urllib2.HTTPError, e: return u,tryGzip(e.fp.read())
        except:
            sys.stdout.write("Problem retrieving "+url+"\n"+traceback.format_exc())
            return None,""

def tryGzip(t):
    try: return gzip.GzipFile('','rb',9,StringIO.StringIO(t)).read()
    except: return t

def check(text,content,url):
    if ' #' in text: text,comment = text.split(' #',1) # TODO: document this (comments must be preceded by a space, otherwise interpreted as part of the text as this is sometimes needed in codes)
    else: comment = ""
    comment = comment.strip()
    if comment: comment="\n  ("+comment+")"
    text = text.strip()
    if not text: return # TODO: print error?
    if text.startswith("!"):
        if len(text)==1: return # TODO: print error?
        if text[1:] in content:
            sys.stdout.write(url+" contains "+text[1:]+comment+"\n") # don't use 'print' or can have problems with threads
    elif not text in content:
        sys.stdout.write(url+" no longer contains "+text+comment+"\n")

if __name__=="__main__": main()
