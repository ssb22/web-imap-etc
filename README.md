WebCheck
========

From https://ssb22.user.srcf.net/setup/webcheck.html (also mirrored at https://ssb22.gitlab.io/setup/webcheck.html just in case, or you can use `pip install webcheck-strings` or `pipx run webcheck-strings` if you prefer)

WebCheck is a Python program (compatible with both Python 2 and Python 3) to check Web pages for changes to specific phrases (strings) of text. I currently use it to:

* check that external links from my website still lead to the information that was there when I added them (I might need to update my links otherwise), and check whether or not I need to warn Lynx users about misguided blocking,
* check the websites of companies, organisations or governments for changes to a specific rule to which I'd be interested in changes (for example because it applies to myself or someone I know, or because I've commented on it somewhere and my comment might need updating),
* follow a couple of sites' "what's new" RSS feeds in my email,
* check for new versions of software programs, data files, EPUB publications etc,
* check if servers hosting my own projects are still serving them,
* alert me if a private page has somehow been set to public when it shouldn't,
* check if sentences I've added to "wiki" sites have been changed or deleted (perhaps for good reason, but anyway I want to know),
* check if code fixes to websites have been accidentally reverted,
* check if answers or comments I've added to crowd-sourced sites and/or 'blogs have been edited or deleted,
* check transport websites to see when discounted bookings for a certain date range become available,
* check if certain rare items I might be interested in appear on an auction site,
* check to see if Chinese translations have appeared for resources I think my Chinese friends might be interested in,
* check for any new seminars planned at a couple of locations,
* check for messages to myself on a couple of websites where I need to log in to check for messages,
* check for new events planned at a local stadium so I know when the roads are likely to be crowded,
* check the names of new tenants at a local startup incubator in case I know someone whom I think might be interested in one,
* check if Android applications I recommend are still on the Play Store, and if their minimum requirements have changed,
* and various other checks as needed.

Some web monitoring programs and “watchlist” facilities etc will tell you when *any* change is made to a page, but that’s of limited use when you are interested in only a few specific phrases, especially when these are surrounded by many other items which change far more frequently than the one that actually interests you. So WebCheck lets you check for changes to a particular item on a page.

Note that this is not a “foolproof” method. If a page lists “old news”, or otherwise incorporates an old version of the item you’re monitoring, WebCheck might fail to spot the new situation. You have to use your judgement about when this program can reasonably be used.

WebCheck runs from the command line, usually from a cron job or similar, and writes any changes it found to standard output, which can then be emailed or whatever. If using ImapFix (below), try its `--maybenote` option.

## webcheck.list

The list of sites to check is in a text file called `webcheck.list`.  Each line (apart from blank lines and comments) specifies a URL to fetch and some text to check, optionally followed by a comment (which starts with a space and a `#`). For example:

    http://nice-program.example.com The latest version is 1.0

or

    http://nice-program.example.com The latest version is 1.0 # otherwise we'd better upgrade

If the text starts with a `*` then the rest of it is treated as a regular expression, otherwise it is treated as a simple search.

You can check for the absence of certain text by prepending a `!` to it:

    http://wiki-page.example.org !spam

By default, the searches are made against the text on the page, not against its source code. If you want to check the source code, prepend a `>` to the `text` or `!text`.

If you need to make more than one test on the same page, simply add multiple lines with the same URL. A shortcut for this is to specify also: on the second and subsequent lines, in place of the repeated URL. Webcheck does of course perform multiple tests in the same fetch operation—the fetch itself will not be duplicated for each test.

It is possible to add arbitrary HTTP headers (such as `Accept-Language: en`) on lines of their own; these apply to all subsequently-listed URLs (except when using a Javascript processor, see below) until removed by setting them blank (e.g. `Accept-Language:`). One use of arbitrary headers is to send “cookies” to indicate you’ve accepted the GDPR or whatever: in most graphical browsers’ Developer Options you can go to a Javascript console and type `document.cookie` to find out what to put in the `Cookie:` header to restore your current ‘session’ with the server.

It is also possible to add :include directives if you wish to place some of your configuration into other files, e.g. `:include wiki-pages.list` (and if any file such as `webcheck.list` is a directory then the files inside it are read).

It is also possible to add simple “or else” logic, for example:

    http://example.org/page1 my text
    else: http://example.org/page2 my text

(this can also be used to retry the same URL if a server works intermittently); unexpected results or errors are reported only from the last `else:` in such a sequence.

## RSS feeds and item lists

You can follow new items on RSS/Atom feeds: give the feed URL and *no* search text.

If the site lists new items but does not support RSS, you can also *extract* items, by setting the search text to `{START...END}` where `START` and `END` are starting and ending strings that surround each item. (By default this is done on the parsed version of the page; to do it on the HTML source, add a `>` before the `{` at the start of the search text.)

## Basic checks

Besides checking `http://`, `https://` and `gemini://` URLs, you can check for:

  * DNS changes (useful if you’re maintaining a hosts file somewhere due to unreliable DNS or an awkward proxy situation): URLs starting `dns://` will return a list of all current IPs, each enclosed in parentheses. So for example to be alerted if `93.184.215.14` ceases to be one of the IP addresses of `example.com`, use `dns://example.com (23.192.228.84)`
  * Server reachability: if a server has been unreachable for a long time and you want to be alerted if it ever becomes reachable again, you can place `up://` before the URL (e.g. `up://http://www.example.com`) which will return `yes` or `no` and not report an error if the server is not reachable.
  * Misguided blocking of the Lynx browser. Prepend `blocks-lynx://` to a URL to have Webcheck try to fetch it with a Lynx user agent and return `yes` if it gets an error or timeout only with that agent, or `no` otherwise, so you can, at least in a `noscript` tag, warn your visitors that the server to which you link has accidentally started discriminating against blind and other users of the text-only Lynx browser due to misguided security settings—some “example” security configurations of web servers incorrectly assume Lynx implies automation and block it, and staff have been known to copy such examples without review or without realising what blocking Lynx implies.
  * Items in the HTTP HEAD response: prepend `head://` to a URL. This might be useful for checking `Last-Modified` to see if a large download has changed, like `wget -N` but without needing to keep a copy of the file on the machine where your WebCheck runs. 
  * Output of arbitrary shell commands: prepend `c://` to the command, and end it with `;` surrounded by spaces

## Using a Javascript processor

If the text you wish to check is written by complex Javascript and there’s no simple way to get it out of the site’s source code, and/or if you need to “log in” or perform other interaction to make it available, then you could try installing one of:

 *  Headless Firefox with GeckoDriver,
 *  Headless Chrome with ChromeDriver,
 *  PhantomJS, or
 *  Edbrowse

and have WebCheck drive one of these.

Edbrowse is more lightweight and should be enough in many cases, but the others have more complete DOM support (see discussion on [Edbrowse issue 4](https://github.com/CMB/edbrowse/issues/4)). In any case you’d be advised to set the check-frequency wisely (see Efficiency section below).

For Edbrowse, prepend `e://` to the URL, e.g.:

    e://http://javascripty-site.example.com my comment

Note that checks on the ‘source’ of a rendered DOM (such as checks for class names written by Javascript) are *not* available when using Edbrowse: you’ll have to run Headless Firefox, Headless Chrome or PhantomJS for those.

Advanced users of edbrowse can write scripts to perform simple interaction with a Javascript site before reading out the text, provided such interaction does not involve spaces, for example:

    e://http://javascripty.example.org\/{LOG/\g\/<>/\i=my-username\/<>/\i=myPassword\/<Log/\i*\/{INBOX/\g No messages

Here, `/{LOG/` searches for a link whose text begins with ‘LOG’, `g` follows the first link on the current line, `/<>/` searches for empty form fields, `i=` fills them in and `i*` submits; see the edbrowse manual for a full list. `\` is used to separate commands; an implicit `b` (browse) command is added before the start and “print all” at the end. Source is not shown.

For Headless Firefox, Headless Chrome or PhantomJS, you need to install the ‘webdriver’ (Selenium) interface. If you need to set it up in your home directory, try `pip install selenium --root $HOME/whatever`, set `PYTHONPATH` appropriately, and put the `phantomjs` or `chromedriver` or `geckodriver` binary in your `PATH` before running webcheck.

An instruction to fetch data via Headless Firefox, Headless Chrome or PhantomJS looks like this:

    { http://site.example.org/ [Click here to show the login form] #txtUsername=me@example.com [#okButton] [Show results] "Results" }

where the first word is the starting URL, and items in square brackets will click either a link with that exact text or an element with the `id` or `name` specified after a `#` (check for `id=` or `name=` in a browser’s Document Inspector or similar), or the first element with the `class` specified after a `.` dot (you can specify other elements of a class `someClass` via `.someClass#2` and `.someClass#3` etc). `#id=text` sends keystrokes `text` to an input field with ID (or name) `id` (`.class=text` is also possible), and you can include space by adding a quoted phrase after the `=`. Text in quotes on its own causes the browser to wait until the page source contains it (which is usually necessary when using Headless Firefox, Headless Chrome or PhantomJS, less so with edbrowse); if you'd rather wait a fixed time period, you can specify a number of seconds instead of a quoted string. Also available is `#id->text` to select from a drop-down (by visible text; blank means deselect all; add quotes after the `->` to select a multi-word phrase), and `#id*n` to set a checkbox to state `n` (0 or 1).

Some sites make you click each item on a results page to reveal an individual result. To automate this in Headless Firefox, Headless Chrome or PhantomJS, use `/start/5` where ‘start’ is the start of each item ID and 5 is the number of seconds to wait after clicking, or `/.itemClass/5` to perform similarly with a class of elements called `itemClass` (and `.itemClass/.closeClass/5` is also possible if a ‘close’ button of class `closeClass` needs to be pressed to dismiss each result, and you can limit the range of items by adding `:1-47` or `:48-0` etc after the number of seconds, plus if the instruction ends with `!` then any error clicking on an item will be treated as a failure to load the whole page). A snapshot of the page after each click will be added to that of the final page, and the checks (or item extractions) that you specify will occur on the combined result. It’s assumed that no ‘back’ button needs to be pressed between clicks.

## Efficiency

To be as efficient as is reasonable for this kind of program, WebCheck has the following features:

 * Different domains are handled in different threads (up to a maximum of `max_threads`)
 * Connections to the same domain are re-used when possible (with optional `delay`)
 * The program tries to save the “last modified” dates (and optionally the “ETag” values) of pages to a file called `.webcheck-last`, and asks servers not to bother sending pages that haven’t changed at all since the last check

However, connection re-use and last-modified handling is *not* performed when using edbrowse or webdriver (except within each session of course).

You can also change the frequency of specific checks with the `days` command, which must appear on a line of its own, for example:

    days 5

which specifies that the addresses below that line will be checked only if the day they were previously checked was at least 5 days ago (unless they are also listed in sections that require more frequent checks). For convenience, `daily`, `weekly` and `monthly` are short for `days 1`, `days 7` and `days 30` respectively. If for testing you need to temporarily turn off all frequencies, Last-Modified and ETag checks but not the already-seen RSS items, you can specify `--test-all` on the WebCheck command line.

ImapFix
=======

From https://ssb22.user.srcf.net/setup/imapfix.html (also mirrored at https://ssb22.gitlab.io/setup/imapfix.html just in case)

ImapFix is a filter/fixer for IMAP mailboxes.  It requires Python 2 and is *not* compatible with Python 3.

You can leave it running on a server somewhere and connect to your IMAP account from different machines/devices. Processed messages are moved from the inbox to a folder called `in` unless otherwise directed by your filters.

Selected features: (see program for a full list)

  * Can use SpamProbe
  * Converts non-ASCII headers and body to Unicode when possible, so you can connect with a device that can’t handle other encodings
  * Move very large message bodies into attachments, to work around display problems on some devices
  * Create “thumbnails” of large images so they can be previewed on low-bandwidth connections
  * Can use tnef and soffice to unpack winmail.dat and add HTML or PDF versions of office documents, so you can view these on devices that don’t otherwise support them
  * Move mail between IMAP and local Maildirs
  * Move old mail to compressed archives, saving attachments separately and merging duplicates; archives can be searched along with current mail
  * Periodically check additional IMAP accounts and process their mail as if it had been sent to the first
  * Rewrite delivery failure reports, adding the failed address to the Subject when possible
  * Rewrite the “importance” flag according to your own rules
  * Manage folders named after dates, for postponing messages and notes to a specific future date
  * Can add arbitrary Python code to the rules, and/or run extra code on messages that were SSL-authenticated as from yourself (for email-based remote control) 

MacLinux
========

From https://ssb22.user.srcf.net/setup/mac.html#maclinux
(also mirrored at https://ssb22.gitlab.io/setup/mac.html#maclinux just in case)

`maclinux.txt` is a script to make the Mac more GNU/Linux-like by:

 * Assigning all Mac applications to shell commands whenever possible
 * Providing functions for `wget`, `watch`, `umount`, `halt` etc when these commands are not available

The script can be added to, or sourced from, your `~/.bashrc` and/or `~/.bash_profile`. 

timetrack.js
============

This Javascript-based tool can be used to add up the time you spend on projects, and can also count arbitrary items along the way. The input is text-based (so it can be copied from a PDA or whatever) and can run either [in the browser](https://ssb22.user.srcf.net/timetrack.html) or on the command line via Node.js. You can enter:

* Hours and minutes e.g. `3h 5min` or decimal fractions of hours e.g. `1.5h` (start with e.g. `0.0h` to get *output* as decimal fractions)
* Starting and finishing times e.g. `954-1023` for start at 9:54 and stop at 10:23 (if stopping in the same hour, you need specify only the 2-digit minute after the `-`); a button to start/stop at the current time is provided
* Arbitrary items, by placing your chosen abbreviation of the item immediately after a number, e.g. `1m 2t 4bk`
* To track other projects, precede some numbers with one or more letters e.g. `x3h x45min y9t`: each prefix gives a separate total.

Legal
=====
All material © Silas S. Brown unless otherwise stated.  Licensed under Apache 2.
Apache is a registered trademark of The Apache Software Foundation.
Javascript is a trademark of Oracle Corporation in the US.
Python is a trademark of the Python Software Foundation.
Unicode is a registered trademark of Unicode, Inc. in the United States and other countries.
Any other trademarks I mentioned without realising are trademarks of their respective holders.
