
# webcheck.py v1.2 (c) 2014-15 Silas S. Brown.  License: GPL
# See webcheck.html for description and usage instructions

# CHANGES
# -------
# If you want to compare this code to old versions, most old
# versions are being kept on SourceForge's E-GuideDog SVN repository
# http://sourceforge.net/p/e-guidedog/code/HEAD/tree/ssb22/setup/
# To check out the repository, you can do:
# svn co http://svn.code.sf.net/p/e-guidedog/code/ssb22/setup

max_threads = 10
delay = 2 # seconds
keep_etags = False # if True, will also keep any ETag headers as well as Last-Modified

import htmlentitydefs, traceback, HTMLParser, urllib2, urlparse, time, pickle, gzip, StringIO, re, Queue, sys, socket
if max_threads > 1: import thread

def read_input():
  ret = {} # domain -> { url -> [(days,text)] }
  days = 0 ; extraHeaders = []
  url = mainDomain = None
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

    if line.startswith('also:') and url:
      text = line[5:].strip()
      # and leave url and mainDomain as-is (same as above line)
    elif ':' in line and not line.split(':',1)[1].startswith('//'):
      extraHeaders.append(line) ; continue
    elif line.startswith('{') and '}' in line: # webdriver
      actions = line[1:line.index('}')].split()
      balanceBrackets(actions)
      text = line[line.index('}')+1:].strip()
      mainDomain = '.'.join(urlparse.urlparse(actions[0]).netloc.rsplit('.',2)[-2:]) # assumes 1st action is a URL
      url = "wd://"+chr(0).join(actions)
    else: # not webdriver
      lSplit = line.split(None,1)
      if len(lSplit)==1: url, text = lSplit[0],"" # RSS only
      else: url, text = lSplit
      mainDomain = '.'.join(urlparse.urlparse(url).netloc.rsplit('.',2)[-2:])
      if extraHeaders: url += '\n'+'\n'.join(extraHeaders)
    if not mainDomain in ret:
        ret[mainDomain] = {}
    if not url in ret[mainDomain]:
        ret[mainDomain][url] = []
    ret[mainDomain][url].append((days,text))
  return ret

def balanceBrackets(wordList):
    "For webdriver instructions: merge adjacent items of wordList so each item has balanced square brackets (currently checks only start and end of each word; if revising this, be careful about use on URLs).  Also checks quotes (TODO: make sure that doesn't interfere with brackets)."
    bracketLevel = 0 ; i = 0
    while i < len(wordList)-1:
        blOld = bracketLevel
        if wordList[i][0] in '["': bracketLevel += 1
        if wordList[i][-1] in ']"': bracketLevel -= 1
        if bracketLevel > 0:
            wordList [i] += " "+wordList[i+1]
            del wordList[i+1] ; bracketLevel = blOld
        else:
            i += 1 ; bracketLevel = 0

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
    def unescape(self,attr): return attr # as we don't use attrs above, no point trying to unescape them and possibly falling over if something's malformed
    def handle_charref(self,ref):
        if ref.startswith('x'): self.handle_data(unichr(int(ref[1:],16)).encode('utf-8'))
        else: self.handle_data(unichr(int(ref)).encode('utf-8'))
    def handle_entityref(self, ref):
        if ref in htmlentitydefs.name2codepoint: self.handle_data(unichr(htmlentitydefs.name2codepoint[ref]).encode('utf-8'))
        else: self.handle_data('&'+ref+';')
    def text(self): return ''.join(self.theTxt).strip()
def htmlStrings(html):
    parser = HTMLStrings()
    try:
        parser.feed(html) ; parser.close()
        return parser.text(), ""
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
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor()) # HTTPCookieProcessor needed for some redirects
    opener.addheaders = [('User-agent', 'Mozilla/5.0 or Lynx or whatever you like (actually Webcheck)'), # TODO: ? (just Mozilla/5.0 is not always acceptable to all servers)
                         ('Accept-Encoding', 'gzip')]
    return opener

def worker_thread(*args):
    opener = None
    while True:
        try: job = jobs.get(False)
        except: return # no more jobs left
        last_fetch_finished = 0 # or time.time()-delay
        for url,daysTextList in sorted(job.items()): # sorted will group http and https together
          if '\n' in url:
              url = url.split('\n')
              extraHeaders = url[1:] ; url = url[0]
          else: extraHeaders = []
          if (url,'lastFetch') in previous_timestamps:
              minDays = min(d for d,_ in daysTextList)
              if minDays and previous_timestamps[(url,'lastFetch')]+minDays >= dayNo(): continue
          previous_timestamps[(url,'lastFetch')] = dayNo() # (keep it even if minDays==0, because that might be changed by later edits of webcheck.list)
          time.sleep(max(0,last_fetch_finished+delay-time.time()))
          if sys.stderr.isatty(): sys.stderr.write('.')
          if url.startswith("dns://"):
              u,content = None, ' '.join(sorted(set('('+x[-1][0]+')' for x in socket.getaddrinfo(url[6:],1)))) # TODO this 'sorted' is lexicographical not numeric; it should be OK for most simple cases though (keeping things in a defined order so can check 2 or 3 IPs on same line if the numbers are consecutive and hold same number of digits).  Might be better if parse and numeric sort
              textContent = content
          elif url.startswith("wd://"):
              u,content = None, run_webdriver(url[5:].split(chr(0)))
              textContent = None # parse 'content' if needed
              url = url[5:].split(chr(0),1)[0] # for display
          else:
              if opener==None: opener = default_opener()
              u,content = tryRead(url,opener,extraHeaders)
              textContent = None
          last_fetch_finished = time.time()
          if content==None: continue # not modified
          if u:
              lm = u.info().getheader("Last-Modified",None)
              if lm: previous_timestamps[(url,'lastMod')] = lm
              if keep_etags:
                e = u.info().getheader("ETag",None)
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
        jobs.task_done()

def run_webdriver(actionList):
    from selenium import webdriver
    browser = webdriver.PhantomJS()
    browser.set_window_size(1024, 768)
    browser.implicitly_wait(30)
    def findElem(spec):
        if spec.startswith('#'):
            return browser.find_element_by_id(spec[1:])
        # TODO: other patterns?
        else: return browser.find_element_by_link_text(spec)
    snippets = []
    for a in actionList:
        if a.startswith('http'): browser.get(a)
        elif a.startswith('"') and a.endswith('"'):
            # wait for "string" to appear in the source
            tries = 30
            while tries and not a[1:-1] in browser.page_source:
              time.sleep(delay) ; tries -= 1
            if sys.stderr.isatty() and not a[1:-1] in browser.page_source:
                sys.stderr.write("webdriver timeout while waiting for \"%s\"\n" % (a[1:-1],))
                # sys.stderr.write("Current source:\n"+browser.page_source+"\n\n") # this can produce a LOT of output
        elif a.startswith('[') and a.endswith(']'): # click
            findElem(a[1:-1]).click()
        elif a.startswith('/') and '/' in a[1:]: # click through items in a list to reveal each one (assume w/out Back)
            start = a[1:a.rindex('/')]
            delayAfter = int(a[a.rindex('/')+1:])
            l = re.findall(' [iI][dD] *="('+re.escape(start)+'[^"]*)',browser.page_source) + re.findall(' [iI][dD] *=('+re.escape(start)+'[^"> ]*)',browser.page_source)
            for m in l:
              browser.find_element_by_id(m).click()
              if sys.stderr.isatty(): sys.stderr.write('*') # webdriver's '.' for click-multiple
              time.sleep(delayAfter)
              snippets.append(browser.page_source.encode('utf-8'))
        elif '=' in a: # set a form control
            spec, val = a.split('=',1)
            findElem(spec).send_keys(val)
        else: sys.stderr.write("Ignoring webdriver unknown action "+repr(a)+'\n')
        if sys.stderr.isatty(): sys.stderr.write(':') # webdriver's '.'
        time.sleep(delay)
    snippets.append(browser.page_source.encode('utf-8'))
    browser.quit()
    return '\n'.join(snippets)

def dayNo(): return int(time.mktime(time.localtime()[:3]+(0,)*6))/(3600*24)

def tryRead(url,opener,extraHeaders):
    for h in extraHeaders: opener.addheaders.append(tuple(x.strip() for x in h.split(':',1)))
    need2pop = len(extraHeaders)
    if (url,'lastMod') in previous_timestamps:
        opener.addheaders.append(("If-Modified-Since",previous_timestamps[(url,'lastMod')]))
        need2pop += 1
    if keep_etags and (url,'ETag') in previous_timestamps:
        opener.addheaders.append(("If-None-Match",previous_timestamps[(url,'lastMod')]))
        need2pop += 1
    ret = tryRead0(url,opener)
    for h in xrange(need2pop): opener.addheaders.pop()
    return ret

def tryRead0(url,opener):
    u = None
    try:
        u = opener.open(url)
        return u,tryGzip(u.read())
    except urllib2.HTTPError, e:
        if e.code==304: return None,None # not modified
        return None,tryGzip(e.fp.read()) # as might want to monitor some phrase on a 404 page
    except: # try it with a fresh opener and no headers
        try:
            u = urllib2.build_opener(urllib2.HTTPCookieProcessor()).open(url)
            return u,tryGzip(u.read())
        except urllib2.HTTPError, e: return u,tryGzip(e.fp.read())
        except:
            sys.stdout.write("Problem retrieving "+url+"\n"+traceback.format_exc())
            return None,""

def tryGzip(t):
    try: return gzip.GzipFile('','rb',9,StringIO.StringIO(t)).read()
    except: return t

def check(text,content,url,errmsg):
    if ' #' in text: text,comment = text.split(' #',1) # TODO: document this (comments must be preceded by a space, otherwise interpreted as part of the text as this is sometimes needed in codes)
    else: comment = ""
    orig_comment = comment = comment.strip()
    if comment:
      if comment.startswith('(') or comment.endswith(')'): pass
      else: comment = '('+comment+')'
      comment="\n  "+comment
    text = text.strip()
    assert text # or should have gone to parseRSS instead
    if text.startswith('{') and text.endswith('}') and '...' in text: extract(url,content,text[1:-1].split('...'),orig_comment)
    elif text.startswith("!"): # 'not', so alert if DOES contain
        if len(text)==1: return # TODO: print error?
        if myFind(text[1:],content):
            sys.stdout.write(url+" contains "+text[1:]+comment+errmsg+"\n") # don't use 'print' or can have problems with threads
    elif not myFind(text,content): # alert if DOESN'T contain
        sys.stdout.write(url+" no longer contains "+text+comment+errmsg+"\n")
        if '??show?' in comment: sys.stdout.write(content+'\n') # TODO: document this (for debugging cases where the text shown in Lynx is not the text shown to Webcheck, and Webcheck says "no longer contains" when it still does)

def parseRSS(url,content,comment):
  from xml.parsers import expat
  parser = expat.ParserCreate()
  items = [[[],[],[]]] ; curElem = [None]
  def StartElementHandler(name,attrs):
    if name in ['item','entry']: items.append([[],[],[]])
    if name=='title': curElem[0]=0
    elif name=='link': curElem[0]=1
    elif name in ['description','summary']: curElem[0]=2
    else: curElem[0]=None
    if name=='link' and 'href' in attrs:
      items[-1][curElem[0]].append(attrs['href']+' ')
  def CharacterDataHandler(data):
    data=data.strip()
    if data and not curElem[0]==None:
      items[-1][curElem[0]].append(data)
  parser.StartElementHandler = StartElementHandler
  parser.CharacterDataHandler = CharacterDataHandler
  try: parser.Parse(content,1)
  except expat.error: pass # TODO: print error?
  handleRSS(url,items,comment)
def handleRSS(url,items,comment,itemType="RSS/Atom"):
  newItems = [] ; pKeep = set()
  for title,link,txt in items:
    def f(t): return "".join(t).strip()
    title,link,txt=f(title),f(link),f(txt)
    if not title: continue # valid entry must have title
    k = (url,'seenItem',hash((title,link,txt))) # TODO: option to keep the whole thing in case someone has the space and is concerned about the small probability of hash collisions?
    pKeep.add(k)
    if k in previous_timestamps: continue
    previous_timestamps[k] = True
    if txt: txt += '\n'
    newItems.append(title+'\n'+txt+link)
  for k in previous_timestamps.keys():
    if k[:2]==(url,'seenItem') and not k in pKeep:
      del previous_timestamps[k] # dropped from the feed
  if comment: comment=" ("+comment+")"
  if newItems: sys.stdout.write(str(len(newItems))+" new "+itemType+" items in "+url+comment+' :\n'+'\n---\n'.join(newItems).encode('utf-8')+'\n\n')

def extract(url,content,startEndMarkers,comment):
  assert len(startEndMarkers)==2, "Should have exactly one '...' between the braces when extracting items"
  start,end = startEndMarkers
  i=0 ; items = []
  while True:
    i = content.find(start,i)
    if i==-1: break
    j = content.find(end,i+len(start))
    if j==-1: break
    items.append(('Auto-extracted text:','',content[i+len(start):j].decode('utf-8'))) # NB the 'title' field must not be empty (unless we relocate that logic to parseRSS instead of handleRSS)
    i = j+len(end)
  # if not items: print "No items in",repr(content)
  handleRSS(url,items,comment,"extracted")

def myFind(text,content):
  if text.startswith("*"): return re.search(text[1:],content)
  elif text in content: return True
  t2 = normalisePunc(text)
  if not t2==text: return t2 in normalisePunc(content)
def normalisePunc(t): return re.sub(r"(\s)\s+",r"\1",t.replace(u"\u2019".encode('utf-8'),"'")) # for apostrophes, + collapse (but don't ignore) whitespace (TODO: other?)
  
if __name__=="__main__": main()
