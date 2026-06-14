"""
txthtml.py — TXT → HTML converter core
Features in generated HTML:
  • Dark mode toggle (persists via localStorage)
  • Continue watching (resume banner with timestamp)
  • Progress tracking (auto-mark at 80%, manual toggle, per-subject %)
  • Part-numbered buttons when a lecture has multiple video URLs
  • Lecture count badges on subject & topic headers
  • Expand All / Collapse All buttons
  • Search with live highlight + auto-expand matching subjects
  • Keyboard shortcuts: Space F ← → ↑ ↓ M
  • HLS + MP4 playback via Plyr + hls.js
  • Double-tap / double-click seek ±10 s
"""

import re
import html
import json
import hashlib


# ═══════════════════════════════════════════════════════════════════════════
#  DATA EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════

def extract_names_and_urls(file_content: str) -> list:
    """Return list of (name, url) pairs. Also handles JSON batch format."""
    file_content = file_content.strip()
    if file_content.startswith("{") and file_content.endswith("}"):
        try:
            return [("JSON_DATA", json.loads(file_content))]
        except json.JSONDecodeError:
            pass
    pairs = []
    for line in file_content.splitlines():
        line = line.strip()
        if ":" in line:
            name, _, url = line.partition(":")
            name, url = name.strip(), url.strip()
            if name and url:
                pairs.append((name, url))
    return pairs


def extract_topic(title: str) -> str:
    """Strip trailing '#N' numbering to get a base topic name."""
    return re.sub(r"\s*#\d+\s*$", "", title).strip()


def parse_line(name: str):
    """Return (subject, topic, title) for a raw lecture name string."""
    if name == "JSON_DATA":
        return "JSON_DATA", None, None

    # (Subject) rest
    m = re.match(r"^\((.*?)\)\s*(.+)", name)
    if m:
        subj = m.group(1).strip()
        rest = m.group(2).strip().lstrip("||").strip()
        return subj, extract_topic(rest), rest

    # Subject by Sir/Mam || Title
    m = re.match(r"^(.*?\s+(?:by|By)\s+(?:Sir|Mam))\s*\|\|\s*(.+)", name)
    if m:
        subj  = m.group(1).strip()
        title = m.group(2).strip()
        return subj, extract_topic(title), title

    # Subject || Title
    if "||" in name:
        subj, _, title = name.partition("||")
        subj  = subj.strip()
        title = title.strip()
        return subj, extract_topic(title), title

    return "General", None, name


def _make_lid(subject: str, topic: str, title: str) -> str:
    """Stable 12-char hex ID for a lecture (used as localStorage key)."""
    raw = f"{subject}||{topic or ''}||{title}"
    return "l" + hashlib.md5(raw.encode()).hexdigest()[:12]


# ═══════════════════════════════════════════════════════════════════════════
#  STRUCTURE BUILDER
# ═══════════════════════════════════════════════════════════════════════════

def structure_data_in_order(urls: list) -> list:
    """Group (name, url) pairs into Subject → Topic → Lecture hierarchy."""
    structured = []
    subject_map = {}
    temp_map    = {}

    for name, url in urls:
        if name == "JSON_DATA":
            continue
        if name not in temp_map:
            temp_map[name] = {"videos": [], "pdfs": []}
        if ".pdf" in url.lower():
            temp_map[name]["pdfs"].append(url)
        else:
            temp_map[name]["videos"].append(url)

    processed = set()
    for name, url in urls:
        if name in processed:
            continue

        subject, topic, title = parse_line(name)

        # ── JSON path ──────────────────────────────────────────────────────
        if subject == "JSON_DATA":
            json_data = url
            for ch in json_data.get("data", {}).get("chapters", []):
                subj   = ch.get("subject_id", "General")
                ctitle = ch.get("title", "")
                clink  = ch.get("link", "")
                ctopic = extract_topic(ctitle)
                lid    = _make_lid(subj, ctopic, ctitle)

                if subj not in subject_map:
                    obj = {"name": subj, "topics": {}}
                    subject_map[subj] = obj
                    structured.append(obj)

                cur = subject_map[subj]
                if ctopic not in cur["topics"]:
                    cur["topics"][ctopic] = {"name": ctopic, "lectures": []}
                cur["topics"][ctopic]["lectures"].append(
                    {"title": ctitle, "lid": lid, "videos": [clink], "pdfs": []}
                )
            processed.add(name)
            continue

        # ── Normal path ────────────────────────────────────────────────────
        lid = _make_lid(subject, topic or "", title or name)

        if subject not in subject_map:
            obj = {"name": subject, "topics": {}}
            subject_map[subject] = obj
            structured.append(obj)

        cur = subject_map[subject]
        lecture = {
            "title":  title,
            "lid":    lid,
            "videos": temp_map[name]["videos"],
            "pdfs":   temp_map[name]["pdfs"],
        }

        if topic:
            if topic not in cur["topics"]:
                cur["topics"][topic] = {"name": topic, "lectures": []}
            cur["topics"][topic]["lectures"].append(lecture)
        else:
            cur.setdefault("direct_lectures", []).append(lecture)

        processed.add(name)

    return structured


def count_total_lectures(structured: list) -> int:
    """Count total lectures across the whole structure."""
    n = 0
    for sub in structured:
        n += len(sub.get("direct_lectures", []))
        for t in sub.get("topics", {}).values():
            n += len(t.get("lectures", []))
    return n


# ═══════════════════════════════════════════════════════════════════════════
#  HTML CONTENT BUILDER
# ═══════════════════════════════════════════════════════════════════════════

def _lecture_html(lec: dict) -> str:
    """Build HTML for one lecture row."""
    title  = lec["title"]
    lid    = lec["lid"]
    videos = lec["videos"]
    pdfs   = lec["pdfs"]

    et  = html.escape(title)
    eta = html.escape(title, quote=True)
    multi = len(videos) > 1

    video_links = ""
    for i, vurl in enumerate(videos, 1):
        label = f"Part {i} &#9654;" if multi else "&#9654; Play"
        eu    = html.escape(vurl, quote=True)
        video_links += (
            f'<a href="#" class="list-item video-item" '
            f'data-url="{eu}" data-lid="{lid}" data-title="{eta}" '
            f'onclick="playVideo(event,this)">{label}</a>'
        )

    pdf_links = ""
    for purl in pdfs:
        eu = html.escape(purl, quote=True)
        pdf_links += (
            f'<a href="{eu}" target="_blank" class="list-item pdf-item">'
            f'<i class="fa-solid fa-file-pdf"></i> PDF</a>'
        )

    watch_btn = (
        f'<button class="watch-btn" data-lid="{lid}" '
        f'onclick="toggleWatched(\'{lid}\')" title="Mark as watched">&#9675;</button>'
    )

    return (
        f'<div class="lecture-entry" data-lid="{lid}">'
        f'<div class="lecture-meta">'
        f'<p class="lecture-title" data-title="{eta}">{et}</p>'
        f'{watch_btn}'
        f'</div>'
        f'<div class="lecture-links">{video_links}{pdf_links}</div>'
        f'</div>'
    )


def _build_content_html(structured: list) -> str:
    if not structured:
        return "<p style='text-align:center;color:var(--muted);padding:40px'>No content found.</p>"

    parts = []
    for sub in structured:
        sname   = sub["name"]
        direct  = sub.get("direct_lectures", [])
        topics  = sub.get("topics", {})
        total   = len(direct) + sum(len(t["lectures"]) for t in topics.values())

        inner = "".join(_lecture_html(l) for l in direct)

        for tname, tdata in topics.items():
            lec_html = "".join(_lecture_html(l) for l in tdata["lectures"])
            tc       = len(tdata["lectures"])
            inner += (
                f'<div class="topic-accordion">'
                f'<button class="topic-header">'
                f'&#128193; {html.escape(tname)}'
                f'<span class="topic-count">{tc}</span>'
                f'<span class="topic-progress"></span>'
                f'</button>'
                f'<div class="topic-content">{lec_html}</div>'
                f'</div>'
            )

        parts.append(
            f'<div class="accordion-item">'
            f'<button class="accordion-header">'
            f'{html.escape(sname)}'
            f'<span class="sub-count">{total}</span>'
            f'<span class="sub-progress"></span>'
            f'</button>'
            f'<div class="accordion-content">{inner}</div>'
            f'</div>'
        )

    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
#  CSS  (plain string — no f-string needed)
# ═══════════════════════════════════════════════════════════════════════════

_CSS = """
:root{--bg:#f4f7f9;--card:#fff;--header-bg:#1c1c1c;--text:#222;--muted:#666;
  --border:#e0e0e0;--accent:#007bff;--accent2:#00b3ff;--plyr-color-main:#00b3ff;}
html.dark{--bg:#111;--card:#1e1e1e;--header-bg:#0a0a0a;--text:#eee;--muted:#aaa;
  --border:#333;--accent:#4da6ff;--accent2:#00c8ff;}
*{margin:0;padding:0;box-sizing:border-box;
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;}
body{background:var(--bg);color:var(--text);transition:background .3s,color .3s;}

/* Header */
.header{background:var(--header-bg);color:#fff;padding:14px 18px;display:flex;
  align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;
  position:sticky;top:0;z-index:2000;}
.header-title{font-size:18px;font-weight:700;}
.header-controls{display:flex;gap:6px;}
.ctrl-btn{background:rgba(255,255,255,.15);border:1px solid rgba(255,255,255,.3);
  color:#fff;border-radius:6px;padding:6px 11px;cursor:pointer;font-size:13px;
  transition:background .2s;}
.ctrl-btn:hover{background:rgba(255,255,255,.3);}

/* Main */
.main-container{padding:14px;max-width:1100px;margin:0 auto;}

/* Player */
.player-wrapper{background:#000;margin-bottom:14px;border-radius:12px;
  overflow:visible!important;box-shadow:0 8px 24px rgba(0,0,0,.25);
  position:sticky;top:54px;z-index:1000;}
.player-wrapper video{pointer-events:none!important;}
.plyr{pointer-events:auto!important;overflow:visible!important;}
.plyr__controls{pointer-events:auto!important;}
.plyr__menu{z-index:10000!important;position:relative!important;}
.plyr__menu__container{max-height:350px!important;overflow-y:auto!important;z-index:10001!important;}
.plyr--volume{display:none!important;}

/* Resume banner */
.resume-banner{background:linear-gradient(135deg,#1a1a2e,#16213e);color:#fff;
  border-radius:10px;padding:11px 14px;margin-bottom:12px;display:flex;
  align-items:center;gap:10px;flex-wrap:wrap;font-size:13px;}
.resume-banner span{flex:1;min-width:140px;}
.resume-banner button{background:rgba(255,255,255,.2);border:1px solid rgba(255,255,255,.4);
  color:#fff;border-radius:6px;padding:5px 11px;cursor:pointer;font-size:12px;}
.resume-banner button:hover{background:rgba(255,255,255,.35);}

/* Search */
.search-bar input{width:100%;padding:12px 16px;border:2px solid var(--border);
  border-radius:10px;font-size:15px;background:var(--card);color:var(--text);
  margin-bottom:10px;outline:none;transition:border-color .2s;}
.search-bar input:focus{border-color:var(--accent2);}

/* Toolbar */
.toolbar{display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap;}
.count-badge,.progress-badge{font-size:12px;color:var(--muted);background:var(--card);
  border:1px solid var(--border);border-radius:20px;padding:3px 11px;}
.progress-badge{color:var(--accent);border-color:var(--accent);}

/* Subject accordion */
.accordion-item{margin-bottom:9px;border-radius:10px;overflow:hidden;
  background:var(--card);box-shadow:0 2px 6px rgba(0,0,0,.07);}
.accordion-header{width:100%;background:var(--card);color:var(--text);border:none;
  text-align:left;padding:15px 18px;font-size:16px;font-weight:700;cursor:pointer;
  display:flex;align-items:center;gap:8px;transition:background .2s;}
.accordion-header:hover{background:var(--bg);}
.accordion-header::after{content:'+';font-size:20px;margin-left:auto;color:var(--muted);
  transition:transform .3s;}
.accordion-header.active::after{transform:rotate(45deg);}
.accordion-content{padding:0 14px;max-height:0;overflow:hidden;
  transition:max-height .4s ease-out;}

/* Subject badges */
.sub-count{background:#e8f4ff;color:#0056b3;font-size:11px;font-weight:600;
  border-radius:20px;padding:2px 8px;white-space:nowrap;}
html.dark .sub-count{background:#1a3550;color:#7ac8ff;}
.sub-progress{font-size:11px;color:var(--muted);}

/* Topic accordion */
.topic-accordion{margin:7px 0;border-left:3px solid var(--accent2);padding-left:10px;}
.topic-header{width:100%;background:var(--bg);color:var(--text);border:none;
  text-align:left;padding:10px 13px;font-size:14px;font-weight:600;cursor:pointer;
  border-radius:6px;display:flex;align-items:center;gap:7px;transition:all .2s;}
.topic-header:hover{background:var(--border);}
.topic-header.active{background:var(--accent2);color:#fff;}
html.dark .topic-header.active{background:#005f8a;}
.topic-content{max-height:0;overflow:hidden;transition:max-height .4s ease-out;padding:0 3px;}
.topic-count{background:rgba(0,0,0,.1);font-size:10px;font-weight:700;
  border-radius:20px;padding:2px 7px;}
.topic-header.active .topic-count{background:rgba(255,255,255,.25);}
.topic-progress{font-size:11px;opacity:.8;margin-left:auto;}

/* Lecture row */
.lecture-entry{padding:12px 0;border-bottom:1px solid var(--border);}
.lecture-entry:last-child{border-bottom:none;}
.lecture-entry.watched .lecture-title::before{content:'✓ ';color:#22a06b;font-weight:700;}
.lecture-meta{display:flex;align-items:flex-start;gap:8px;margin-bottom:9px;}
.lecture-title{font-weight:600;color:var(--text);flex:1;line-height:1.45;font-size:14px;}
.lecture-links{display:flex;flex-wrap:wrap;gap:7px;}

/* Search highlight */
mark{background:#fff3cd;color:#333;border-radius:3px;padding:0 2px;}
html.dark mark{background:#5a4a00;color:#ffe;}

/* Buttons */
.list-item{display:inline-flex;align-items:center;gap:6px;padding:7px 14px;
  border-radius:20px;text-decoration:none;font-size:13px;font-weight:500;
  cursor:pointer;border:none;transition:all .2s;}
.video-item{background:#e9f5ff;color:#0056b3;border:1px solid #b3d7ff;}
.video-item.playing,.video-item:hover{background:var(--accent);color:#fff;
  border-color:var(--accent);transform:translateY(-1px);}
.pdf-item{background:#fff0e9;color:#d84315;border:1px solid #ffd0b3;}
.pdf-item:hover{background:#ff5722;color:#fff;border-color:#ff5722;}
html.dark .video-item{background:#0d2a45;color:#7ac8ff;border-color:#1a4a6e;}
html.dark .pdf-item{background:#3d1000;color:#ffaa88;border-color:#5a2000;}

/* Watch button */
.watch-btn{background:none;border:1.5px solid var(--border);color:var(--muted);
  border-radius:50%;width:26px;height:26px;cursor:pointer;font-size:14px;
  display:flex;align-items:center;justify-content:center;flex-shrink:0;
  transition:all .2s;padding:0;line-height:1;}
.watch-btn:hover{border-color:#22a06b;color:#22a06b;}
.lecture-entry.watched .watch-btn{background:#22a06b;border-color:#22a06b;color:#fff;}

/* Footer */
.footer-credit{text-align:center;margin-top:28px;padding:18px 0;border-top:1px solid var(--border);}
.footer-credit a{display:inline-flex;align-items:center;gap:8px;background:#222;
  padding:8px 18px;border-radius:20px;text-decoration:none;
  box-shadow:0 4px 10px rgba(0,0,0,.2);}
.shortcut-hint{margin-top:10px;font-size:11px;color:var(--muted);}

@media(max-width:600px){
  .header-title{font-size:15px;}
  .accordion-header{font-size:14px;padding:13px;}
  .player-wrapper{top:50px;}
}
"""


# ═══════════════════════════════════════════════════════════════════════════
#  JAVASCRIPT  (raw string — no f-string escaping needed)
# ═══════════════════════════════════════════════════════════════════════════

# NOTE: FILE_KEY is injected as the very first line via _build_js()
_JS_BODY = r"""
/* ── State ──────────────────────────────────────────────────────────────── */
var player=null,hls=null,isPlayerReady=false;
var currentLid=null,currentPlayUrl=null,currentPlayTitle='';
var currentlyPlaying=null,pendingVideoUrl=null;
var lastTapTime=0,autoMarked=new Set(),watchedSet=new Set();
var videoEl,playerWrapper;

/* ── Watched tracking ───────────────────────────────────────────────────── */
function loadWatched(){
  try{watchedSet=new Set(JSON.parse(localStorage.getItem(FILE_KEY+'_w')||'[]'));}catch(e){}
  updateWatchedUI();
}
function toggleWatched(lid){
  if(watchedSet.has(lid)){watchedSet.delete(lid);}else{watchedSet.add(lid);}
  saveWatched();updateWatchedUI();
}
function markWatched(lid){
  if(!lid||watchedSet.has(lid))return;
  watchedSet.add(lid);saveWatched();updateWatchedUI();
}
function saveWatched(){
  try{localStorage.setItem(FILE_KEY+'_w',JSON.stringify([...watchedSet]));}catch(e){}
}
function updateWatchedUI(){
  var total=0,watched=0;
  document.querySelectorAll('.lecture-entry[data-lid]').forEach(function(entry){
    var lid=entry.dataset.lid,w=watchedSet.has(lid);
    entry.classList.toggle('watched',w);
    var wb=entry.querySelector('.watch-btn');
    if(wb)wb.innerHTML=w?'&#10003;':'&#9675;';
    total++;if(w)watched++;
  });
  document.querySelectorAll('.accordion-item').forEach(function(sub){
    var lecs=sub.querySelectorAll('.lecture-entry[data-lid]');
    var wc=[...lecs].filter(function(l){return watchedSet.has(l.dataset.lid);}).length;
    var sp=sub.querySelector('.sub-progress');
    if(sp)sp.textContent=lecs.length?wc+'/'+lecs.length:'';
    sub.querySelectorAll('.topic-accordion').forEach(function(t){
      var tl=t.querySelectorAll('.lecture-entry[data-lid]');
      var tw=[...tl].filter(function(l){return watchedSet.has(l.dataset.lid);}).length;
      var tp=t.querySelector('.topic-progress');
      if(tp)tp.textContent=tl.length?tw+'/'+tl.length:'';
    });
  });
  var pb=document.getElementById('progress-badge');
  if(pb&&total>0){
    var pct=Math.round(watched/total*100);
    pb.textContent='Progress: '+watched+'/'+total+' ('+pct+'%)';
  }
}

/* ── Continue watching ──────────────────────────────────────────────────── */
function saveLastPlayed(url,title,time){
  try{localStorage.setItem(FILE_KEY+'_last',JSON.stringify({url:url,title:title,time:Math.floor(time)}));}catch(e){}
}
function checkResume(){
  try{
    var s=JSON.parse(localStorage.getItem(FILE_KEY+'_last')||'null');
    if(s&&s.url&&s.time>5){
      var m=Math.floor(s.time/60),sec=String(s.time%60).padStart(2,'0');
      document.getElementById('resume-text').textContent='Continue: "'+(s.title||'')+'" at '+m+':'+sec;
      document.getElementById('resume-banner').style.display='flex';
      window._resumeUrl=s.url;window._resumeTime=s.time;
    }
  }catch(e){}
}
function resumeVideo(){
  document.getElementById('resume-banner').style.display='none';
  if(window._resumeUrl)loadNewVideo(window._resumeUrl,window._resumeTime||0);
}
function dismissResume(){
  document.getElementById('resume-banner').style.display='none';
  try{localStorage.removeItem(FILE_KEY+'_last');}catch(e){}
}

/* ── Dark mode ──────────────────────────────────────────────────────────── */
function toggleDark(){
  var d=document.documentElement.classList.toggle('dark');
  try{localStorage.setItem('bbk_dark',d?'1':'0');}catch(e){}
  var btn=document.getElementById('darkBtn');
  if(btn)btn.textContent=d?'\u2600\uFE0F':'\uD83C\uDF19';
}
function initDarkMode(){
  try{
    if(localStorage.getItem('bbk_dark')==='1'){
      document.documentElement.classList.add('dark');
      var b=document.getElementById('darkBtn');
      if(b)b.textContent='\u2600\uFE0F';
    }
  }catch(e){}
}

/* ── Expand / Collapse all ──────────────────────────────────────────────── */
function expandAll(){
  document.querySelectorAll('.accordion-header').forEach(function(b){
    b.classList.add('active');b.nextElementSibling.style.maxHeight='99999px';
  });
  document.querySelectorAll('.topic-header').forEach(function(b){
    b.classList.add('active');b.nextElementSibling.style.maxHeight='99999px';
  });
}
function collapseAll(){
  document.querySelectorAll('.accordion-header.active,.topic-header.active').forEach(function(b){
    b.classList.remove('active');b.nextElementSibling.style.maxHeight=null;
  });
}

/* ── Search ─────────────────────────────────────────────────────────────── */
function filterContent(rawTerm){
  var term=rawTerm.trim().toLowerCase();
  var visible=0;
  document.querySelectorAll('.accordion-item').forEach(function(subEl){
    var subMatch=false;
    subEl.querySelectorAll('.lecture-entry').forEach(function(lec){
      var titleEl=lec.querySelector('.lecture-title');
      var orig=titleEl.dataset.title||titleEl.textContent;
      var match=!term||orig.toLowerCase().indexOf(term)!==-1;
      lec.style.display=match?'':'none';
      if(match){
        subMatch=true;visible++;
        if(term){
          var esc=term.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
          titleEl.innerHTML=orig.replace(new RegExp('('+esc+')','gi'),'<mark>$1</mark>');
        }else{titleEl.textContent=orig;}
      }
    });
    subEl.style.display=subMatch?'':'none';
    if(term&&subMatch){
      var hdr=subEl.querySelector('.accordion-header');
      hdr.classList.add('active');
      subEl.querySelector('.accordion-content').style.maxHeight='99999px';
      subEl.querySelectorAll('.topic-accordion').forEach(function(t){
        var hv=[...t.querySelectorAll('.lecture-entry')].some(function(l){return l.style.display!=='none';});
        if(hv){
          t.querySelector('.topic-header').classList.add('active');
          t.querySelector('.topic-content').style.maxHeight='99999px';
        }
      });
    }
  });
  var cb=document.getElementById('total-count');
  if(cb)cb.textContent=term?visible+' results':'';
}

/* ── Player ─────────────────────────────────────────────────────────────── */
function playVideo(event,element){
  event.preventDefault();
  var url=element.dataset.url,lid=element.dataset.lid||null,title=element.dataset.title||'';
  if(!url)return;
  if(currentlyPlaying)currentlyPlaying.classList.remove('playing');
  element.classList.add('playing');currentlyPlaying=element;
  currentLid=lid;currentPlayUrl=url;currentPlayTitle=title;
  isPlayerReady=false;pendingVideoUrl=url;
  if(hls){
    hls.once(Hls.Events.MEDIA_DETACHED,function(){
      hls=null;
      if(pendingVideoUrl){loadNewVideo(pendingVideoUrl,0);pendingVideoUrl=null;}
    });
    hls.off(Hls.Events.MANIFEST_PARSED);hls.off(Hls.Events.ERROR);hls.destroy();
  }else{
    if(player){
      player.off('ready');player.off('timeupdate');
      player.off('enterfullscreen');player.off('exitfullscreen');
      player.destroy();player=null;
    }
    videoEl.removeAttribute('src');videoEl.load();
    setTimeout(function(){loadNewVideo(url,0);pendingVideoUrl=null;},50);
  }
}

function _attachEvents(startTime){
  player.on('ready',function(){
    isPlayerReady=true;
    if(startTime>0){try{player.currentTime=startTime;}catch(e){}}
    player.play().catch(function(){});
  });
  player.on('timeupdate',function(){
    if(!isPlayerReady||!currentPlayUrl)return;
    var dur=player.duration,cur=player.currentTime;
    if(dur>0&&cur>3){
      saveLastPlayed(currentPlayUrl,currentPlayTitle,cur);
      if(currentLid&&(cur/dur)>0.8&&!autoMarked.has(currentLid)){
        autoMarked.add(currentLid);markWatched(currentLid);
      }
    }
  });
  player.on('enterfullscreen',function(){
    try{if(screen.orientation&&screen.orientation.lock)screen.orientation.lock('landscape');}catch(e){}
  });
  player.on('exitfullscreen',function(){
    try{if(screen.orientation&&screen.orientation.unlock)screen.orientation.unlock();}catch(e){}
  });
}

function loadNewVideo(url,startTime){
  startTime=startTime||0;
  if(url.indexOf('.m3u8')!==-1){
    if(typeof Hls!=='undefined'&&Hls.isSupported()){
      hls=new Hls({enableWorker:true,maxBufferLength:30});
      hls.loadSource(url);hls.attachMedia(videoEl);
      hls.on(Hls.Events.MANIFEST_PARSED,function(){
        var lvls=hls.levels.map(function(l){return l.height;});lvls.unshift(0);
        player=new Plyr(videoEl,{
          controls:['play-large','play','progress','current-time','mute','settings','pip','fullscreen'],
          settings:['quality','speed'],
          speed:{selected:1,options:[0.5,0.75,1,1.5,2]},
          quality:{default:0,options:lvls,forced:true,onChange:updateQuality},
          i18n:{qualityLabel:{0:'Auto'}},
          fullscreen:{enabled:true,fallback:true,iosNative:true},
          clickToPlay:true
        });
        _attachEvents(startTime);
      });
      hls.on(Hls.Events.ERROR,function(e,data){
        if(data.fatal){
          if(data.type===Hls.ErrorTypes.NETWORK_ERROR)hls.startLoad();
          else if(data.type===Hls.ErrorTypes.MEDIA_ERROR)hls.recoverMediaError();
        }
      });
    }else if(videoEl.canPlayType('application/vnd.apple.mpegurl')){
      videoEl.src=url;
      player=new Plyr(videoEl,{controls:['play-large','play','progress','current-time','mute','settings','pip','fullscreen'],settings:['speed'],speed:{selected:1,options:[0.5,0.75,1,1.5,2]}});
      _attachEvents(startTime);
    }
  }else{
    videoEl.src=url;
    player=new Plyr(videoEl,{controls:['play-large','play','progress','current-time','mute','settings','pip','fullscreen'],settings:['speed'],speed:{selected:1,options:[0.5,0.75,1,1.5,2]}});
    _attachEvents(startTime);
  }
}

function updateQuality(q){
  if(!hls)return;
  hls.currentLevel=q===0?-1:hls.levels.findIndex(function(l){return l.height===q;});
}

/* ── Double-tap seek ────────────────────────────────────────────────────── */
function setupDoubleTapSeek(){
  playerWrapper.addEventListener('dblclick',function(e){
    if(e.target.closest('.plyr__controls'))return;
    e.preventDefault();e.stopImmediatePropagation();
    if(!player||!isPlayerReady)return;
    var x=e.clientX-playerWrapper.getBoundingClientRect().left;
    if(x<playerWrapper.offsetWidth/2)player.rewind(10);else player.forward(10);
  });
  playerWrapper.addEventListener('touchend',function(e){
    if(e.target.closest('.plyr__controls'))return;
    var now=Date.now(),diff=now-lastTapTime;
    if(diff>0&&diff<300&&lastTapTime>0){
      e.preventDefault();e.stopImmediatePropagation();
      if(player&&isPlayerReady){
        var x=e.changedTouches[0].clientX-playerWrapper.getBoundingClientRect().left;
        if(x<playerWrapper.offsetWidth/2)player.rewind(10);else player.forward(10);
      }
      lastTapTime=0;
    }else{
      lastTapTime=now;
      setTimeout(function(){lastTapTime=0;},300);
    }
  });
}

/* ── Keyboard shortcuts ─────────────────────────────────────────────────── */
function initKeyboard(){
  document.addEventListener('keydown',function(e){
    if(e.target.tagName==='INPUT'||e.target.tagName==='TEXTAREA')return;
    if(!player||!isPlayerReady)return;
    switch(e.code){
      case'Space':e.preventDefault();player.togglePlay();break;
      case'KeyF':player.fullscreen.toggle();break;
      case'ArrowLeft':e.preventDefault();player.rewind(10);break;
      case'ArrowRight':e.preventDefault();player.forward(10);break;
      case'ArrowUp':e.preventDefault();player.increaseVolume(0.1);break;
      case'ArrowDown':e.preventDefault();player.decreaseVolume(0.1);break;
      case'KeyM':player.muted=!player.muted;break;
    }
  });
}

/* ── Accordions ─────────────────────────────────────────────────────────── */
function initAccordions(){
  document.querySelectorAll('.accordion-header').forEach(function(btn){
    btn.addEventListener('click',function(){
      var was=btn.classList.contains('active');
      document.querySelectorAll('.accordion-header').forEach(function(b){
        if(b!==btn){b.classList.remove('active');b.nextElementSibling.style.maxHeight=null;}
      });
      if(!was){
        btn.classList.add('active');
        btn.nextElementSibling.style.maxHeight=btn.nextElementSibling.scrollHeight+'px';
      }else{
        btn.classList.remove('active');
        btn.nextElementSibling.style.maxHeight=null;
      }
    });
  });
  document.querySelectorAll('.topic-header').forEach(function(btn){
    btn.addEventListener('click',function(){
      var was=btn.classList.contains('active');
      var pc=btn.closest('.accordion-content');
      pc.querySelectorAll('.topic-header').forEach(function(b){
        if(b!==btn){b.classList.remove('active');b.nextElementSibling.style.maxHeight=null;}
      });
      if(!was){
        btn.classList.add('active');
        btn.nextElementSibling.style.maxHeight=btn.nextElementSibling.scrollHeight+'px';
        setTimeout(function(){if(pc.style.maxHeight)pc.style.maxHeight=pc.scrollHeight+'px';},55);
      }else{
        btn.classList.remove('active');
        btn.nextElementSibling.style.maxHeight=null;
        setTimeout(function(){if(pc.style.maxHeight)pc.style.maxHeight=pc.scrollHeight+'px';},55);
      }
    });
  });
}

/* ── Init ───────────────────────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded',function(){
  videoEl=document.getElementById('player');
  playerWrapper=document.querySelector('.player-wrapper');
  initDarkMode();
  loadWatched();
  checkResume();
  initAccordions();
  initKeyboard();
  setupDoubleTapSeek();
});
"""


def _build_js(file_key: str) -> str:
    """Inject the FILE_KEY constant at the top of the JS body."""
    safe_key = re.sub(r"[^a-zA-Z0-9_-]", "_", file_key)[:48]
    return "const FILE_KEY=" + json.dumps(safe_key) + ";\n" + _JS_BODY


_FOOTER = """
<div class="footer-credit">
  <a href="https://babubhaikundan.pages.dev" target="_blank">
    <span style="color:#00ffc8;font-weight:bold;font-size:15px">Developer&#x1F480; :-</span>
    <span style="color:#FFD700;font-size:15px;font-weight:bold">&#x1D542;&#x1D566;&#x1D55F;&#x1D555;&#x1D552;&#x1D55F; &#x1D550;&#x1D552;&#x1D555;&#x1D552;&#x1D567;</span>
  </a>
  <p class="shortcut-hint">
    &#9000; Space=play/pause &nbsp;|&nbsp; F=fullscreen &nbsp;|&nbsp;
    &larr;/&rarr;=&plusmn;10s &nbsp;|&nbsp; &uarr;/&darr;=volume &nbsp;|&nbsp; M=mute
  </p>
</div>
"""


# ═══════════════════════════════════════════════════════════════════════════
#  PUBLIC ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def generate_html(file_name: str, structured_list: list) -> str:
    """Return a complete, self-contained HTML string."""
    content_html = _build_content_html(structured_list)
    total        = count_total_lectures(structured_list)
    js           = _build_js(file_name)
    ename        = html.escape(file_name)

    return (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1.0\">\n"
        f"<title>{ename}</title>\n"
        "<link rel=\"stylesheet\" href=\"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css\">\n"
        "<link rel=\"stylesheet\" href=\"https://cdn.plyr.io/3.7.8/plyr.css\">\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n"
        "<body>\n"
        "<div class=\"header\">\n"
        f"  <span class=\"header-title\">{ename}</span>\n"
        "  <div class=\"header-controls\">\n"
        "    <button onclick=\"expandAll()\" class=\"ctrl-btn\" title=\"Expand all\">\u229e</button>\n"
        "    <button onclick=\"collapseAll()\" class=\"ctrl-btn\" title=\"Collapse all\">\u229f</button>\n"
        "    <button onclick=\"toggleDark()\" class=\"ctrl-btn\" id=\"darkBtn\" title=\"Dark mode\">\U0001f319</button>\n"
        "  </div>\n"
        "</div>\n"
        "<div class=\"main-container\">\n"
        "  <div class=\"player-wrapper\">\n"
        "    <video id=\"player\" playsinline controls crossorigin preload=\"metadata\"></video>\n"
        "  </div>\n"
        "  <div id=\"resume-banner\" class=\"resume-banner\" style=\"display:none\">\n"
        "    <span id=\"resume-text\"></span>\n"
        "    <button onclick=\"resumeVideo()\">\u25b6 Resume</button>\n"
        "    <button onclick=\"dismissResume()\">\u2715 Dismiss</button>\n"
        "  </div>\n"
        "  <div class=\"search-bar\">\n"
        "    <input type=\"text\" id=\"searchInput\" placeholder=\"\U0001f50d Search lectures...\" oninput=\"filterContent(this.value)\">\n"
        "  </div>\n"
        "  <div class=\"toolbar\">\n"
        f"    <span class=\"count-badge\">{total} lectures</span>\n"
        "    <span id=\"total-count\" class=\"count-badge\"></span>\n"
        "    <span id=\"progress-badge\" class=\"progress-badge\"></span>\n"
        "  </div>\n"
        f"  <div id=\"content-container\">{content_html}</div>\n"
        "</div>\n"
        f"{_FOOTER}\n"
        "<script src=\"https://cdn.plyr.io/3.7.8/plyr.js\"></script>\n"
        "<script src=\"https://cdn.jsdelivr.net/npm/hls.js@latest\"></script>\n"
        f"<script>{js}</script>\n"
        "</body>\n"
        "</html>"
    )
