/*
  Time and Item Counter (c) 2004-2019 Silas S. Brown.
  
  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.

  2004: SNOBOL version
  2010: Javascript version
  2019: Node.js option in JS version

  Command-line usage: echo "1234-507" | node timetrack.js
  
  (also has functions for timetrack.html, q.v. for full details)

  */

function save() { var v=document.forms[0].txt.value; if(window.localStorage!=undefined) localStorage.setItem('ttrk',v); else { document.cookie="ttrk="+escape(v)+"; path=/; expires=Sun, 27-Sep-2037 00:00:00 GMT"; if(document.cookie && getC()!=v && !this.alerted_already) { alert("Too much text to save as cookie (try add-up, or enable HTML-5 Storage)"); this.alerted_already=true } } }
function load() { if(window.localStorage!=undefined) document.forms[0].txt.value=localStorage.getItem('ttrk'); else document.forms[0].txt.value=getC() }
function getC() { var dc=document.cookie; var i=dc.indexOf("ttrk="); if(i==-1) return ""; i+=5; var e=dc.indexOf(";",i); if(e==-1) e=dc.length; return unescape(dc.substring(i,e)) }
// TODO: undo/redo?  (for browsers that don't have it natively) as save is now automatic

function doPredefinedText(txt) { document.forms[0].txt.value = txt+" "+document.forms[0].txt.value; save() }
// TODO: option to auto doAddup() at end of doPredefinedText that isn't called from doNow?  but might be best NOT to do this if it adds to existing figures, making it less obvious how many times the button was pressed

function doNow() {
    var t = document.forms[0].nowButton.value;
    if (t.match(/-$/)) doPredefinedText(t);
    else if (t.match(/^-/)) { // need to find where to put it on
        var tt = document.forms[0].txt.value+" ";
        var hyphen = tt.search(/-\s/);
        if (hyphen==-1) return alert("Could not find where to put the "+t);
        document.forms[0].txt.value=(tt.slice(0,hyphen)+t+tt.slice(hyphen+1,tt.length-1)); save()
    } else alert("Illegal value of nowButton");
    updateNowButton();
}

function parseTime(hmStr) {
    if (hmStr.length <= 2) return [false,Number(hmStr)];
    else return [Number(hmStr.slice(0,-2)),Number(hmStr.slice(-2))];
}

function pad(n, width) { n+=''; if (n.length >= width) return n; return new Array(width-n.length+1).join('0') + n; }
                        
function parseTimeRelative(hmStr1,hmStr2) { // parse hmStr2 relative to hmStr1
    if (hmStr2.length > 2) return parseTime(hmStr2);
    var hm = parseTime(hmStr1);
    if (hmStr2.length==1) hmStr2=pad(hm[1],2).charAt(0)+hmStr2;
    var m2 = Number(hmStr2);
    if (m2<hm[1]) return "E: minute "+m2+" is less than minute "+hm[1];
    return [hm[0],m2];
}

function curTime(oldTime) {
   var date = new Date;
   var h=date.getHours(),m=date.getMinutes();
   if (h>12) h -= 12;
   else if (h==0) h = 12;
   if (oldTime) hhmm = parseTime(oldTime);
   else hhmm = [-1,-1];
   if (hhmm[0]==h && hhmm[1]==m) { // can't have 0min, minimum 1min
        m += 1;
        if (m==60) { h++; m=0; if(h==13) h=1; }
    }
    if (h==hhmm[0]) return pad(m,2);
    else return ''+h+pad(m,2);
}

function getNowTxt() {
    var ww = document.forms[0].txt.value.split(/\s+/);
    for (var i=0; i < ww.length; i++)
        if (ww[i].match(/-$/)) // incomplete time
            return "-"+curTime(ww[i].slice(0,-1));
    return curTime()+"-";
}

function updateNowButton() {
    document.forms[0].nowButton.value=getNowTxt();
    window.setTimeout(updateNowButton,1000*(60-new Date().getSeconds()));
}

function doOtherButtons() {
    if(!document.getElementById) return;
    var span = document.getElementById("predef");
    while(span.firstChild) span.removeChild(span.firstChild);
    function addButton(thing) {
        var b=document.createElement('INPUT');
        b.type='button'; b.value='+1'+thing;
        b.onclick=function(){doPredefinedText('1'+thing);return false};
        span.appendChild(b)
    }
    var had=new Array();
    had.push('min'); had.push('mins'); had.push('h');
    var ww = document.forms[0].txt.value.split(/\s+/);
    for (var i=0; i < ww.length; i++) {
        w = ww[i];
        var ii=w.length-1;
        while (ii>=0 && w.slice(ii,ii+1).match(/[A-Za-z]/)) ii--;
        if(ii+1==w.length) continue;
        var thing=w.slice(ii+1,w.length);
        if(had.indexOf(thing)==-1) had.push(thing);
    }
    had = had.slice(3); had.sort();
    for(i in had) addButton(had[i])
}

function doAddup() {
    var a=addup(document.forms[0].txt.value);
    if(a.slice(0,3)=="E: ") return alert(a.slice(3));
    else document.forms[0].txt.value=a;
    save();
    doOtherButtons(); // TODO: call this more frequently?
}

function addup(s) {
    function Project() {
        this.letters = new Object();
        this.startedAt = false; this.stopped = true;
        this.totMins = 0;
        this.report = function(label) {
            var tRep="", tr_other = new Array();
            if(!label || this.totMins) tRep += label+Math.floor(this.totMins/60)+"h "+label+(this.totMins%60)+"min";
            for (var l in this.letters) tr_other.push(""+label+this.letters[l]+l);
            tr_other.sort();
            if ((tr_other.length || !this.stopped) && tRep) tRep += " ";
            tRep += tr_other.join(" ");
            if (!this.stopped) tRep += (" "+label+this.startedAt+"-");
            return tRep;
        };
    }
    var anonP = new Project(), otherP = new Object();
    var ww = s.replace(/-/g," -").split(/\s+/);
    var proj=anonP, lastProj=anonP;
    for (var ii=0; ii < ww.length; ii++) {
        var w = ww[ii]; if (!w) continue;
        lastProj = proj;
        if (w.match(/^[A-Za-z]+/)) {
            var iii = w.search(/[^A-Za-z]/);
            if(iii==-1) return "E: Don't know what "+w+" means (if it's a project name, join it to a figure with no intervening space)";
            var pName = w.slice(0,iii);
            if (otherP[pName]==undefined)
                otherP[pName] = new Project();
            proj = otherP[pName]; w = w.slice(iii);
            lastProj = proj;
        } else proj=anonP; // and keep lastProj, for cases like (pname)305 -47 (remembering we added the space)
        if (w.match(/^[0-9]+h$/)) proj.totMins += 60*Number(w.slice(0,-1));
        else if (w.match(/^[0-9]+min$/)) proj.totMins += Number(w.slice(0,-3));
        else if (w.match(/^[0-9]+mins$/)) proj.totMins += Number(w.slice(0,-4));
        else if (w.slice(-1).match(/[A-Za-z]/)) {
            var i=w.length-1;
            while (i>=0 && w.slice(i,i+1).match(/[A-Za-z]/)) i--;
            i++; // first letter
            if (w.slice(0,i).match(/^[0-9]+$/)) {
                var thing=w.slice(i,w.length);
                if (proj.letters[thing]==undefined) proj.letters[thing]=0;
                proj.letters[thing] += Number(w.slice(0,i));
            } else return "E: Don't know what "+w+" means";
        } else if (w.match(/^-[0-9]/)) {
            proj = lastProj; // TODO: even if we DIDN'T add the space?
            if (!proj.startedAt) return "E: Don't know when "+w+" started";
            oldHM = parseTime(proj.startedAt);
            hm = parseTimeRelative(proj.startedAt,w.slice(1));
            if(typeof hm=='string') return hm;
            var oldH=oldHM[0],oldM=oldHM[1],h=hm[0],m=hm[1];
            proj.startedAt=''+h+pad(m,2); proj.stopped=true;
            while (h<oldH || (h==oldH && m<oldM)) h += 12;
            proj.totMins += ((h-oldH)*60 + m-oldM);
        } else if (w.match(/^[0-9][0-9][0-9]+$/)) {
            if (!proj.stopped) return "E: Trying to start time twice, "+proj.startedAt+" and "+w;
            proj.startedAt=w; proj.stopped=false;
        } else if (w=="-" && !proj.stopped) {}
        else return "E: Don't know what "+w+" means";
    }
    var tRep = anonP.report(""), oPout = new Array();
    for (p in otherP) oPout.push("\n"+otherP[p].report(p));
    oPout.sort(); return tRep + oPout.join("");
}

if (typeof require != "undefined" && typeof module != "undefined" && require.main === module) {
    // We are on Node.JS command line
    fs=require('fs');
    var out=addup(fs.readFileSync('/dev/stdin').toString())+"\n";
    process.stdout.write(out);
    if(out.slice(0,3)=="E: ") process.exit(1);
} else {
    if(navigator.userAgent.indexOf("Opera Mini")>-1 && document.getElementById) document.getElementById("jump").removeAttribute("onclick"); // save a round-trip to the transcoder
    window.onerror=function(msg,url,line){alert(""+line+": "+msg); return true};
}
