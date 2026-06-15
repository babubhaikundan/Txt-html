"""
txthtml.py — TXT → HTML Converter
Features: Drawer menu, dark mode, continue watching, progress tracking,
          per-lecture watch toggle, search highlight, keyboard shortcuts,
          HLS + MP4 playback, accordion (no clip bug), Part buttons only when needed.
"""

import re, html, json, hashlib


# ═══════════════════════════════════════════════════════════════════════════
#  DATA EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════

def extract_names_and_urls(file_content: str) -> list:
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
    return re.sub(r"\s*#\d+\s*$", "", title).strip()


def parse_line(name: str):
    if name == "JSON_DATA":
        return "JSON_DATA", None, None
    m = re.match(r"^\((.*?)\)\s*(.+)", name)
    if m:
        subj = m.group(1).strip()
        rest = m.group(2).strip().lstrip("||").strip()
        return subj, extract_topic(rest), rest
    m = re.match(r"^(.*?\s+(?:by|By)\s+(?:Sir|Mam))\s*\|\|\s*(.+)", name)
    if m:
        subj  = m.group(1).strip()
        title = m.group(2).strip()
        return subj, extract_topic(title), title
    if "||" in name:
        subj, _, title = name.partition("||")
        return subj.strip(), extract_topic(title.strip()), title.strip()
    return "General", None, name


def _make_lid(subject: str, topic: str, title: str) -> str:
    raw = f"{subject}||{topic or ''}||{title}"
    return "l" + hashlib.md5(raw.encode()).hexdigest()[:12]


def structure_data_in_order(urls: list) -> list:
    """
    Each line → its own lecture.
    Exception: a PDF with the same name as the preceding video gets merged into it.
    This prevents same-name videos from becoming Part-1/Part-2 incorrectly.
    """
    structured  = []
    subject_map = {}
    last_video  = {}   # (subject, topic, title) → last video lecture dict

    for idx, (name, url) in enumerate(urls):
        subject, topic, title = parse_line(name)

        # ── JSON path ──────────────────────────────────────────────────────
        if subject == "JSON_DATA" and name == "JSON_DATA":
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
            continue

        # ── Normal path — each line = its own lecture ──────────────────────
        is_pdf = ".pdf" in url.lower()
        key    = (subject, topic or "", title or name)
        lid    = _make_lid(subject, topic or "", f"{title or name}__{idx}")

        # PDF with same name as last video → attach, skip new row
        if is_pdf and key in last_video:
            last_video[key]["pdfs"].append(url)
            continue

        lecture = {
            "title":  title or name,
            "lid":    lid,
            "videos": [] if is_pdf else [url],
            "pdfs":   [url] if is_pdf else [],
        }
        if not is_pdf:
            last_video[key] = lecture

        if subject not in subject_map:
            obj = {"name": subject, "topics": {}}
            subject_map[subject] = obj
            structured.append(obj)

        cur = subject_map[subject]
        if topic:
            if topic not in cur["topics"]:
                cur["topics"][topic] = {"name": topic, "lectures": []}
            cur["topics"][topic]["lectures"].append(lecture)
        else:
            cur.setdefault("direct_lectures", []).append(lecture)

    return structured


def count_total_lectures(structured: list) -> int:
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
    title  = lec["title"]
    lid    = lec["lid"]
    videos = lec["videos"]
    pdfs   = lec["pdfs"]
    et     = html.escape(title)
    eta    = html.escape(title, quote=True)
    multi  = len(videos) > 1

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
        f'onclick="toggleWatched(\'{lid}\')" title="Mark watched">&#9675;</button>'
    )

    return (
        f'<div class="lecture-entry" data-lid="{lid}">'
        f'<div class="lecture-meta">'
        f'{watch_btn}'
        f'<p class="lecture-title" data-title="{eta}">{et}</p>'
        f'</div>'
        f'<div class="lecture-links">{video_links}{pdf_links}</div>'
        f'</div>'
    )


def _build_content_html(structured: list) -> str:
    if not structured:
        return "<p class='empty-msg'>No content found.</p>"
    parts = []
    for sub in structured:
        sname  = sub["name"]
        direct = sub.get("direct_lectures", [])
        topics = sub.get("topics", {})
        total  = len(direct) + sum(len(t["lectures"]) for t in topics.values())
        inner  = "".join(_lecture_html(l) for l in direct)
        for tname, tdata in topics.items():
            lec_html = "".join(_lecture_html(l) for l in tdata["lectures"])
            tc = len(tdata["lectures"])
            inner += (
                f'<div class="topic-accordion">'
                f'<button class="topic-header">'
                f'<i class="fa-solid fa-folder"></i>'
                f'<span class="topic-name">{html.escape(tname)}</span>'
                f'<span class="topic-count">{tc}</span>'
                f'<span class="topic-progress"></span>'
                f'</button>'
                f'<div class="topic-content">{lec_html}</div>'
                f'</div>'
            )
        parts.append(
            f'<div class="accordion-item">'
            f'<button class="accordion-header">'
            f'<span class="sub-name">{html.escape(sname)}</span>'
            f'<span class="sub-count">{total}</span>'
            f'<span class="sub-progress"></span>'
            f'<span class="acc-arrow">&#43;</span>'
            f'</button>'
            f'<div class="accordion-content">{inner}</div>'
            f'</div>'
        )
    return "\n".join(parts)


# ═══════════════════════════════════════════════════════════════════════════
#  CSS
# ═══════════════════════════════════════════════════════════════════════════

_CSS = """
/* ── CSS Variables ── */
:root {
  --bg:#f0f4f8; --card:#ffffff; --header-bg:#0f172a;
  --text:#1e293b; --muted:#64748b; --border:#e2e8f0;
  --accent:#2563eb; --accent2:#0ea5e9; --green:#22c55e;
  --plyr-color-main:#0ea5e9;
  --shadow:0 1px 3px rgba(0,0,0,.08),0 4px 12px rgba(0,0,0,.06);
  --shadow-md:0 4px 16px rgba(0,0,0,.12);
  --radius:12px; --radius-sm:8px;
}
html.dark {
  --bg:#0d1117; --card:#161b22; --header-bg:#010409;
  --text:#e6edf3; --muted:#8b949e; --border:#30363d;
  --accent:#58a6ff; --accent2:#38bdf8; --green:#4ade80;
  --shadow:0 1px 3px rgba(0,0,0,.3),0 4px 12px rgba(0,0,0,.25);
  --shadow-md:0 4px 16px rgba(0,0,0,.4);
}

/* ── Reset & Base ── */
*{margin:0;padding:0;box-sizing:border-box;}
html{scroll-behavior:smooth;}
body{
  background:var(--bg);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Inter,sans-serif;
  font-size:15px;line-height:1.5;
  transition:background .25s,color .25s;
}

/* ── Header ── */
.header{
  background:var(--header-bg);color:#fff;
  padding:12px 16px 12px 16px;
  padding-right:68px;
  display:flex;align-items:center;gap:10px;
  position:sticky;top:0;z-index:2000;
  box-shadow:0 2px 8px rgba(0,0,0,.25);
}
.header-title{
  font-size:16px;font-weight:700;flex:1;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
  letter-spacing:-.01em;
}
.header-controls{display:flex;gap:6px;align-items:center;flex-shrink:0;}
.ctrl-btn{
  background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.18);
  color:#fff;border-radius:8px;padding:6px 10px;cursor:pointer;
  font-size:13px;line-height:1;transition:background .2s,transform .15s;
  white-space:nowrap;
}
.ctrl-btn:hover{background:rgba(255,255,255,.22);transform:scale(1.05);}

/* ── Progress Bar (thin, just below header) ── */
.progress-bar-track{
  height:3px;background:var(--border);
  position:sticky;top:46px;z-index:1999;
}
.progress-bar-fill{
  height:100%;width:0%;
  background:linear-gradient(90deg,var(--accent2),var(--accent));
  transition:width .5s ease;
}

/* ── Main Container ── */
.main-container{padding:14px;max-width:900px;margin:0 auto;}

/* ── Player ── */
.player-wrapper{
  background:#000;margin-bottom:12px;border-radius:var(--radius);
  overflow:visible!important;
  box-shadow:0 8px 32px rgba(0,0,0,.28);
  position:sticky;top:49px;z-index:1000;
}
.player-wrapper video{pointer-events:none!important;}
.plyr{pointer-events:auto!important;overflow:visible!important;border-radius:var(--radius);}
.plyr__controls{pointer-events:auto!important;}
.plyr__menu{z-index:10000!important;position:relative!important;}
.plyr__menu__container{max-height:350px!important;overflow-y:auto!important;z-index:10001!important;}
.plyr--volume{display:none!important;}

/* Now playing */
.now-playing{
  background:linear-gradient(135deg,#1e293b,#0f172a);
  border:1px solid rgba(14,165,233,.25);
  border-radius:var(--radius-sm);padding:9px 14px;margin-bottom:10px;
  display:none;align-items:center;gap:9px;font-size:13px;color:#e2e8f0;
}
.now-playing-dot{width:8px;height:8px;border-radius:50%;background:var(--accent2);
  flex-shrink:0;animation:blink 1.2s ease-in-out infinite;}
@keyframes blink{0%,100%{opacity:1;}50%{opacity:.3;}}
.now-playing-title{flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-weight:500;}

/* ── Resume Banner ── */
.resume-banner{
  background:linear-gradient(135deg,#1e293b,#0f172a);
  border:1px solid rgba(14,165,233,.2);
  border-radius:var(--radius-sm);padding:11px 14px;margin-bottom:10px;
  display:none;align-items:center;gap:10px;flex-wrap:wrap;font-size:13px;color:#e2e8f0;
}
.resume-banner span{flex:1;min-width:140px;}
.resume-btn{
  background:var(--accent2);border:none;color:#fff;
  border-radius:6px;padding:6px 12px;cursor:pointer;font-size:12px;font-weight:600;
  transition:background .2s;
}
.resume-btn:hover{background:var(--accent);}
.resume-dismiss{
  background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.15);
  color:#94a3b8;border-radius:6px;padding:6px 10px;cursor:pointer;font-size:12px;
}

/* ── Search ── */
.search-wrap{position:relative;margin-bottom:12px;}
.search-wrap .fa-magnifying-glass{
  position:absolute;left:14px;top:50%;transform:translateY(-50%);
  color:var(--muted);font-size:14px;pointer-events:none;
}
.search-input{
  width:100%;padding:11px 14px 11px 40px;
  border:1.5px solid var(--border);border-radius:var(--radius);
  font-size:14px;background:var(--card);color:var(--text);
  outline:none;transition:border-color .2s,box-shadow .2s;
}
.search-input:focus{border-color:var(--accent2);box-shadow:0 0 0 3px rgba(14,165,233,.12);}

/* ── Toolbar ── */
.toolbar{display:flex;gap:8px;align-items:center;margin-bottom:14px;flex-wrap:wrap;}
.badge{
  font-size:12px;font-weight:500;border-radius:20px;padding:4px 12px;
  border:1.5px solid var(--border);background:var(--card);color:var(--muted);
}
.badge-progress{border-color:var(--accent2);color:var(--accent2);}
.badge-result{border-color:var(--accent);color:var(--accent);}

/* ── Subject Accordion ── */
.accordion-item{
  margin-bottom:10px;border-radius:var(--radius);
  background:var(--card);box-shadow:var(--shadow);
  border:1px solid var(--border);overflow:hidden;
}
.accordion-header{
  width:100%;background:var(--card);color:var(--text);border:none;
  text-align:left;padding:15px 18px;cursor:pointer;
  display:flex;align-items:center;gap:10px;
  transition:background .2s;
}
.accordion-header:hover{background:var(--bg);}
.accordion-header.active{background:var(--bg);}
.sub-name{font-size:15px;font-weight:700;flex:1;letter-spacing:-.01em;}
.sub-count{
  background:#dbeafe;color:#1d4ed8;font-size:11px;font-weight:700;
  border-radius:20px;padding:3px 9px;flex-shrink:0;
}
html.dark .sub-count{background:#1e3a5f;color:#60a5fa;}
.sub-progress{font-size:12px;color:var(--muted);flex-shrink:0;}
.acc-arrow{
  color:var(--muted);font-size:20px;font-weight:300;
  transition:transform .35s cubic-bezier(.4,0,.2,1);flex-shrink:0;
  margin-left:4px;
}
.accordion-header.active .acc-arrow{transform:rotate(45deg);}
.accordion-content{
  padding:0 14px;max-height:0;overflow:hidden;
  transition:max-height .35s cubic-bezier(.4,0,.2,1);
}
.accordion-content.open{padding-bottom:8px;}

/* ── Topic Accordion ── */
.topic-accordion{margin:8px 0;border-radius:var(--radius-sm);overflow:hidden;}
.topic-header{
  width:100%;background:var(--bg);color:var(--text);border:none;
  text-align:left;padding:10px 13px;cursor:pointer;border-radius:var(--radius-sm);
  display:flex;align-items:center;gap:8px;font-size:14px;
  transition:background .2s,color .2s;
}
.topic-header .fa-folder{color:var(--accent2);font-size:13px;transition:color .2s;}
.topic-header:hover{background:var(--border);}
.topic-header.active{background:var(--accent2);color:#fff;}
.topic-header.active .fa-folder{color:rgba(255,255,255,.8);}
html.dark .topic-header.active{background:#0369a1;}
.topic-name{flex:1;font-weight:600;}
.topic-count{
  font-size:11px;font-weight:700;border-radius:20px;padding:2px 8px;
  background:rgba(0,0,0,.1);flex-shrink:0;
}
.topic-header.active .topic-count{background:rgba(255,255,255,.2);}
.topic-progress{font-size:11px;flex-shrink:0;opacity:.8;}
.topic-content{max-height:0;overflow:hidden;transition:max-height .35s cubic-bezier(.4,0,.2,1);padding:0 4px;}

/* ── Lecture Row ── */
.lecture-entry{
  padding:11px 0;border-bottom:1px solid var(--border);
  border-left:3px solid transparent;padding-left:6px;
  transition:border-color .2s,background .2s;
}
.lecture-entry:last-child{border-bottom:none;}
.lecture-entry.watched{border-left-color:var(--green);}
.lecture-entry.now-active{border-left-color:var(--accent2);background:rgba(14,165,233,.04);}
.lecture-meta{display:flex;align-items:flex-start;gap:9px;margin-bottom:9px;}
.watch-btn{
  background:none;border:2px solid var(--border);color:var(--muted);
  border-radius:50%;width:24px;height:24px;cursor:pointer;
  font-size:12px;display:flex;align-items:center;justify-content:center;
  flex-shrink:0;margin-top:1px;transition:all .2s;padding:0;
}
.watch-btn:hover{border-color:var(--green);color:var(--green);}
.lecture-entry.watched .watch-btn{
  background:var(--green);border-color:var(--green);color:#fff;
}
.lecture-title{
  font-size:14px;font-weight:600;color:var(--text);flex:1;line-height:1.45;
}
.lecture-entry.watched .lecture-title{color:var(--muted);text-decoration:line-through;text-decoration-color:var(--green);}
.lecture-links{display:flex;flex-wrap:wrap;gap:7px;}
mark{background:#fef3c7;color:#92400e;border-radius:3px;padding:0 2px;}
html.dark mark{background:#451a03;color:#fbbf24;}

/* ── Buttons ── */
.list-item{
  display:inline-flex;align-items:center;gap:6px;padding:7px 14px;
  border-radius:20px;text-decoration:none;font-size:13px;font-weight:500;
  cursor:pointer;border:1.5px solid transparent;
  transition:all .2s cubic-bezier(.4,0,.2,1);
}
.video-item{background:#eff6ff;color:#1d4ed8;border-color:#bfdbfe;}
.video-item:hover,.video-item.playing{
  background:var(--accent);color:#fff;border-color:var(--accent);
  transform:translateY(-1px);box-shadow:0 4px 12px rgba(37,99,235,.3);
}
html.dark .video-item{background:#172554;color:#93c5fd;border-color:#1e40af;}
html.dark .video-item:hover,html.dark .video-item.playing{
  background:var(--accent);color:#fff;border-color:var(--accent);
}
.pdf-item{background:#fff7ed;color:#c2410c;border-color:#fed7aa;}
.pdf-item:hover{background:#ea580c;color:#fff;border-color:#ea580c;transform:translateY(-1px);}
html.dark .pdf-item{background:#431407;color:#fb923c;border-color:#7c2d12;}

/* ── Empty state ── */
.empty-msg{text-align:center;padding:48px;color:var(--muted);font-size:15px;}

/* ── Footer ── */
.footer-wrap{
  text-align:center;margin:24px 0 20px;
  padding:18px 0;border-top:1px solid var(--border);
}
.footer-credit-btn{
  display:inline-flex;align-items:center;gap:8px;
  background:#0f172a;padding:9px 20px;border-radius:24px;
  text-decoration:none;box-shadow:0 4px 14px rgba(0,0,0,.2);
  transition:transform .2s,box-shadow .2s;
}
.footer-credit-btn:hover{transform:translateY(-2px);box-shadow:0 8px 20px rgba(0,0,0,.3);}
.shortcut-hint{margin-top:12px;font-size:11px;color:var(--muted);line-height:1.8;}

/* ── Drawer overrides (make toggle sit in header) ── */
.kk-drawer-toggle{
  position:fixed!important;
  top:8px!important;right:12px!important;
  z-index:9999!important;
  width:40px!important;height:40px!important;
  gap:5px!important;border-radius:10px!important;
  background:rgba(255,255,255,.12)!important;
  border:1px solid rgba(255,255,255,.2)!important;
}
.kk-drawer-toggle span{width:18px!important;height:2.5px!important;}
.kk-drawer-toggle.active{background:var(--accent2)!important;border-color:var(--accent2)!important;}
.kk-drawer-toggle.active span{background:#fff!important;}
.kk-drawer-toggle.active span:nth-child(1){transform:translateY(7.5px) rotate(45deg)!important;}
.kk-drawer-toggle.active span:nth-child(3){transform:translateY(-7.5px) rotate(-45deg)!important;}
.kk-drawer-toggle:hover{
  box-shadow:0 0 16px rgba(14,165,233,.4)!important;
  border-color:var(--accent2)!important;transform:none!important;
}

/* ── Responsive ── */
@media(max-width:600px){
  .header-title{font-size:14px;}
  .accordion-header{padding:13px 14px;}
  .sub-name{font-size:14px;}
  .player-wrapper{top:46px;}
  .progress-bar-track{top:43px;}
  .main-container{padding:10px;}
}
"""

# ═══════════════════════════════════════════════════════════════════════════
#  DRAWER HTML + CSS  (from plug-and-play drawer-menu component)
# ═══════════════════════════════════════════════════════════════════════════

_DRAWER_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap');
.kk-drawer-overlay{position:fixed;top:0;left:0;width:100%;height:100%;
  background:rgba(0,0,0,.75);z-index:8000;opacity:0;visibility:hidden;
  transition:all .4s cubic-bezier(.4,0,.2,1);
  backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);}
.kk-drawer-overlay.open{opacity:1;visibility:visible;}
.kk-drawer-nav{position:fixed;top:0;right:0;width:290px;max-width:80%;height:100%;
  background:linear-gradient(180deg,rgba(10,20,35,.99),rgba(5,10,15,.99));
  z-index:8500;transform:translateX(100%);
  transition:transform .5s cubic-bezier(.77,0,.175,1);
  display:flex;flex-direction:column;
  box-shadow:-12px 0 48px rgba(0,0,0,.6);
  border-left:1px solid rgba(255,255,255,.07);overflow-y:auto;}
.kk-drawer-nav.open{transform:translateX(0);}
.kk-drawer-header{padding:26px 26px 18px;border-bottom:1px solid rgba(255,255,255,.08);flex-shrink:0;}
.kk-drawer-logo{font-family:'Outfit',sans-serif;font-size:1.3rem;font-weight:800;
  display:flex;align-items:center;gap:10px;color:#f5f5ff;}
.kk-drawer-logo i{color:#00f2ff;}
.kk-drawer-nav ul{list-style:none;padding:18px 22px;flex:1;margin:0;}
.kk-drawer-nav li{margin:3px 0;opacity:0;transform:translateX(40px);
  transition:opacity .4s cubic-bezier(.4,0,.2,1),transform .4s cubic-bezier(.4,0,.2,1);}
.kk-drawer-nav.open li{opacity:1;transform:translateX(0);}
.kk-drawer-nav.open li:nth-child(1){transition-delay:.07s;}
.kk-drawer-nav.open li:nth-child(2){transition-delay:.12s;}
.kk-drawer-nav.open li:nth-child(3){transition-delay:.17s;}
.kk-drawer-nav.open li:nth-child(4){transition-delay:.22s;}
.kk-drawer-nav.open li:nth-child(5){transition-delay:.27s;}
.kk-drawer-nav.open li:nth-child(6){transition-delay:.32s;}
.kk-drawer-nav.open li:nth-child(7){transition-delay:.37s;}
.kk-drawer-nav a{font-family:'Outfit',sans-serif;font-size:1.05rem;font-weight:700;
  color:#f0f0ff;text-decoration:none;display:flex;align-items:center;gap:13px;
  padding:10px 8px;border-radius:10px;transition:all .3s ease;}
.kk-drawer-nav a:hover{color:#00ffc8;background:rgba(0,255,200,.06);padding-left:15px;}
.kk-drawer-nav a i{font-size:.9rem;width:32px;height:32px;display:flex;
  align-items:center;justify-content:center;background:rgba(20,10,40,.7);
  border-radius:9px;flex-shrink:0;transition:all .3s ease;}
.kk-drawer-nav a:hover i{background:#00ffc8;color:#0a0118;}
.kk-drawer-social{padding:18px 22px 26px;border-top:1px solid rgba(255,255,255,.08);flex-shrink:0;}
.kk-drawer-social-title{font-size:.68rem;color:#888;text-transform:uppercase;
  letter-spacing:3px;margin-bottom:12px;font-weight:600;font-family:'Outfit',sans-serif;}
.kk-drawer-social-links{display:flex;gap:10px;flex-wrap:wrap;}
.kk-drawer-social-links a{width:44px;height:44px;background:rgba(20,10,40,.7)!important;
  border:1px solid rgba(255,255,255,.1);border-radius:13px;
  display:flex;align-items:center;justify-content:center;
  color:#fff;font-size:1.1rem;padding:0!important;gap:0!important;
  transition:all .35s ease;}
.kk-drawer-social-links a:hover{border-color:#00f2ff!important;color:#00f2ff!important;
  background:rgba(20,10,40,.7)!important;padding-left:0!important;
  transform:translateY(-5px) rotate(5deg)!important;
  box-shadow:0 10px 25px rgba(0,242,255,.2);}
.kk-drawer-social-links a:hover i{background:transparent!important;color:#00f2ff!important;}
@media(max-width:480px){
  .kk-drawer-nav{width:82vw!important;max-width:300px!important;}
}
"""

_DRAWER_HTML = """
<div class="kk-drawer-overlay" id="kk-drawer-overlay"></div>
<button class="kk-drawer-toggle" id="kk-drawer-toggle" aria-label="Menu" aria-expanded="false">
  <span></span><span></span><span></span>
</button>
<nav class="kk-drawer-nav" id="kk-drawer-nav" aria-label="Main Navigation">
  <div class="kk-drawer-header">
    <div class="kk-drawer-logo"><i class="fa-solid fa-cube"></i> Menu</div>
  </div>
  <ul role="menu">
    <li><a href="https://babubhaikundan.pages.dev" target="_blank" rel="noopener" role="menuitem">
        <i class="fa-solid fa-globe"></i> Official Website</a></li>
    <li><a href="https://babubhaikundan.pages.dev/App-Store/" role="menuitem">
        <i class="fa-solid fa-rocket"></i> App Store</a></li>
    <li><a href="https://babubhaikundan.pages.dev/Tools/" role="menuitem">
        <i class="fa-solid fa-wand-magic-sparkles"></i> Tools</a></li>
    <li><a href="https://babubhaikundan.pages.dev/Resume/" target="_blank" rel="noopener" role="menuitem">
        <i class="fa-solid fa-file-invoice"></i> Resume Maker</a></li>
    <li><a href="https://babubhaikundan.pages.dev/Test-Series/" role="menuitem">
        <i class="fa-solid fa-layer-group"></i> Test Series</a></li>
    <li><a href="https://babubhaikundan.pages.dev/Ai/" role="menuitem">
        <i class="fa-solid fa-robot"></i> Ai ChatBot</a></li>
    <li><a href="https://babubhaikundan.pages.dev/About/" role="menuitem">
        <i class="fa-solid fa-user-astronaut"></i> About Me</a></li>
  </ul>
  <div class="kk-drawer-social">
    <div class="kk-drawer-social-title">Connect With Me</div>
    <div class="kk-drawer-social-links">
      <a href="https://instagram.com/babubhaikundan" target="_blank" aria-label="Instagram"><i class="fa-brands fa-instagram"></i></a>
      <a href="https://github.com/babubhaikundan" target="_blank" aria-label="GitHub"><i class="fa-brands fa-github"></i></a>
      <a href="https://twitter.com/babubhaikundan" target="_blank" aria-label="Twitter"><i class="fa-brands fa-x-twitter"></i></a>
      <a href="https://t.me/babubhaikundan" target="_blank" aria-label="Telegram"><i class="fa-brands fa-telegram"></i></a>
    </div>
  </div>
</nav>
"""

_DRAWER_JS = """
(function(){
  'use strict';
  var tb=document.getElementById('kk-drawer-toggle');
  var nav=document.getElementById('kk-drawer-nav');
  var ov=document.getElementById('kk-drawer-overlay');
  if(!tb||!nav||!ov)return;
  function openD(){nav.classList.add('open');ov.classList.add('open');tb.classList.add('active');tb.setAttribute('aria-expanded','true');document.body.style.overflow='hidden';}
  function closeD(){nav.classList.remove('open');ov.classList.remove('open');tb.classList.remove('active');tb.setAttribute('aria-expanded','false');document.body.style.overflow='';}
  tb.addEventListener('click',function(){nav.classList.contains('open')?closeD():openD();});
  ov.addEventListener('click',closeD);
  nav.querySelectorAll('a').forEach(function(a){a.addEventListener('click',function(){if(nav.classList.contains('open'))closeD();});});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&nav.classList.contains('open')){closeD();tb.focus();}});
})();
"""


# ═══════════════════════════════════════════════════════════════════════════
#  JAVASCRIPT  (raw string — no f-string escaping needed)
# ═══════════════════════════════════════════════════════════════════════════

_JS_BODY = r"""
/* ── State ── */
var player=null,hls=null,isPlayerReady=false;
var currentLid=null,currentPlayUrl=null,currentPlayTitle='';
var currentlyPlaying=null,pendingVideoUrl=null;
var lastTapTime=0,autoMarked=new Set(),watchedSet=new Set();
var videoEl,playerWrapper;

/* ── Watched tracking ── */
function loadWatched(){
  try{watchedSet=new Set(JSON.parse(localStorage.getItem(FILE_KEY+'_w')||'[]'));}catch(e){}
  updateWatchedUI();
}
function toggleWatched(lid){
  if(watchedSet.has(lid)){watchedSet.delete(lid);}else{watchedSet.add(lid);}
  try{localStorage.setItem(FILE_KEY+'_w',JSON.stringify([...watchedSet]));}catch(e){}
  updateWatchedUI();
}
function markWatched(lid){
  if(!lid||watchedSet.has(lid))return;
  watchedSet.add(lid);
  try{localStorage.setItem(FILE_KEY+'_w',JSON.stringify([...watchedSet]));}catch(e){}
  updateWatchedUI();
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
  /* Per-subject progress */
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
  /* Overall progress badge */
  var pb=document.getElementById('progress-badge');
  if(pb&&total>0){
    var pct=Math.round(watched/total*100);
    pb.textContent='Progress: '+watched+'/'+total+' ('+pct+'%)';
  }
  /* Thin progress bar */
  var fill=document.getElementById('progress-fill');
  if(fill&&total>0)fill.style.width=(watched/total*100)+'%';
}

/* ── Continue watching ── */
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

/* ── Dark mode ── */
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
      var b=document.getElementById('darkBtn');if(b)b.textContent='\u2600\uFE0F';
    }
  }catch(e){}
}

/* ── Expand / Collapse all ── */
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

/* ── Search ── */
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
  var cb=document.getElementById('search-result-count');
  if(cb)cb.textContent=term?visible+' results':'';
  cb=document.getElementById('search-result-count');
  if(cb)cb.style.display=term?'':'none';
}

/* ── Now playing ── */
function setNowPlaying(title){
  var np=document.getElementById('now-playing');
  var npt=document.getElementById('now-playing-title');
  if(!np||!npt)return;
  if(title){npt.textContent=title;np.style.display='flex';}
  else{np.style.display='none';}
}

/* ── Player ── */
function playVideo(event,element){
  event.preventDefault();
  var url=element.dataset.url,lid=element.dataset.lid||null,title=element.dataset.title||'';
  if(!url)return;
  /* Highlight new, remove old */
  if(currentlyPlaying)currentlyPlaying.classList.remove('playing');
  element.classList.add('playing');currentlyPlaying=element;
  /* Remove active class from all lecture entries, add to current */
  document.querySelectorAll('.lecture-entry.now-active').forEach(function(e){e.classList.remove('now-active');});
  var parentEntry=element.closest('.lecture-entry');
  if(parentEntry)parentEntry.classList.add('now-active');
  currentLid=lid;currentPlayUrl=url;currentPlayTitle=title;
  isPlayerReady=false;pendingVideoUrl=url;
  setNowPlaying(title);
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
  var plyrOpts={
    controls:['play-large','play','progress','current-time','mute','settings','pip','fullscreen'],
    settings:['speed'],
    speed:{selected:1,options:[0.5,0.75,1,1.25,1.5,1.75,2]},
    fullscreen:{enabled:true,fallback:true,iosNative:true},
    clickToPlay:true
  };
  if(url.indexOf('.m3u8')!==-1){
    if(typeof Hls!=='undefined'&&Hls.isSupported()){
      hls=new Hls({enableWorker:true,maxBufferLength:30});
      hls.loadSource(url);hls.attachMedia(videoEl);
      hls.on(Hls.Events.MANIFEST_PARSED,function(){
        var lvls=hls.levels.map(function(l){return l.height;});lvls.unshift(0);
        plyrOpts.settings=['quality','speed'];
        plyrOpts.quality={default:0,options:lvls,forced:true,onChange:updateQuality};
        plyrOpts.i18n={qualityLabel:{0:'Auto'}};
        player=new Plyr(videoEl,plyrOpts);
        _attachEvents(startTime);
      });
      hls.on(Hls.Events.ERROR,function(e,data){
        if(data.fatal){
          if(data.type===Hls.ErrorTypes.NETWORK_ERROR)hls.startLoad();
          else if(data.type===Hls.ErrorTypes.MEDIA_ERROR)hls.recoverMediaError();
        }
      });
    }else if(videoEl.canPlayType('application/vnd.apple.mpegurl')){
      videoEl.src=url;player=new Plyr(videoEl,plyrOpts);_attachEvents(startTime);
    }
  }else{
    videoEl.src=url;player=new Plyr(videoEl,plyrOpts);_attachEvents(startTime);
  }
}

function updateQuality(q){
  if(!hls)return;
  hls.currentLevel=q===0?-1:hls.levels.findIndex(function(l){return l.height===q;});
}

/* ── Double-tap seek ── */
function setupDoubleTapSeek(){
  playerWrapper.addEventListener('dblclick',function(e){
    if(e.target.closest('.plyr__controls'))return;
    e.preventDefault();e.stopImmediatePropagation();
    if(!player||!isPlayerReady)return;
    var x=e.clientX-playerWrapper.getBoundingClientRect().left;
    x<playerWrapper.offsetWidth/2?player.rewind(10):player.forward(10);
  });
  playerWrapper.addEventListener('touchend',function(e){
    if(e.target.closest('.plyr__controls'))return;
    var now=Date.now(),diff=now-lastTapTime;
    if(diff>0&&diff<300&&lastTapTime>0){
      e.preventDefault();e.stopImmediatePropagation();
      if(player&&isPlayerReady){
        var x=e.changedTouches[0].clientX-playerWrapper.getBoundingClientRect().left;
        x<playerWrapper.offsetWidth/2?player.rewind(10):player.forward(10);
      }
      lastTapTime=0;
    }else{lastTapTime=now;setTimeout(function(){lastTapTime=0;},300);}
  });
}

/* ── Keyboard shortcuts ── */
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

/* ── Accordions ── */
function initAccordions(){
  /* Subject level — one open at a time, parent uses 99999px so topics never clip */
  document.querySelectorAll('.accordion-header').forEach(function(btn){
    btn.addEventListener('click',function(){
      var was=btn.classList.contains('active');
      document.querySelectorAll('.accordion-header').forEach(function(b){
        if(b!==btn){b.classList.remove('active');b.nextElementSibling.style.maxHeight=null;}
      });
      if(!was){
        btn.classList.add('active');
        btn.nextElementSibling.style.maxHeight='99999px';
      }else{
        btn.classList.remove('active');
        btn.nextElementSibling.style.maxHeight=null;
      }
    });
  });
  /* Topic level */
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
      }else{
        btn.classList.remove('active');
        btn.nextElementSibling.style.maxHeight=null;
      }
    });
  });
}

/* ── Init ── */
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
    safe_key = re.sub(r"[^a-zA-Z0-9_-]", "_", file_key)[:48]
    return "const FILE_KEY=" + json.dumps(safe_key) + ";\n" + _JS_BODY + "\n" + _DRAWER_JS


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════

def generate_html(file_name: str, structured_list: list) -> str:
    content_html = _build_content_html(structured_list)
    total        = count_total_lectures(structured_list)
    js           = _build_js(file_name)
    ename        = html.escape(file_name)

    return (
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">\n'
        f'<title>{ename}</title>\n'
        '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css">\n'
        '<link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css">\n'
        f'<style>{_CSS}</style>\n'
        f'<style>{_DRAWER_CSS}</style>\n'
        '</head>\n'
        '<body>\n'

        # Drawer (overlay + toggle + nav panel)
        + _DRAWER_HTML +

        # Header
        '<div class="header">\n'
        f'  <span class="header-title">{ename}</span>\n'
        '  <div class="header-controls">\n'
        '    <button onclick="expandAll()" class="ctrl-btn" title="Expand all">\u229e</button>\n'
        '    <button onclick="collapseAll()" class="ctrl-btn" title="Collapse all">\u229f</button>\n'
        '    <button onclick="toggleDark()" class="ctrl-btn" id="darkBtn" title="Dark mode">\U0001f319</button>\n'
        '  </div>\n'
        '</div>\n'

        # Thin progress bar (sticky below header)
        '<div class="progress-bar-track">'
        '<div class="progress-bar-fill" id="progress-fill"></div>'
        '</div>\n'

        # Main content
        '<div class="main-container">\n'

        # Player
        '  <div class="player-wrapper">\n'
        '    <video id="player" playsinline controls crossorigin preload="metadata"></video>\n'
        '  </div>\n'

        # Now playing
        '  <div id="now-playing" class="now-playing">\n'
        '    <span class="now-playing-dot"></span>\n'
        '    <span class="now-playing-title" id="now-playing-title"></span>\n'
        '  </div>\n'

        # Resume banner
        '  <div id="resume-banner" class="resume-banner">\n'
        '    <span id="resume-text"></span>\n'
        '    <button class="resume-btn" onclick="resumeVideo()">\u25b6 Resume</button>\n'
        '    <button class="resume-dismiss" onclick="dismissResume()">\u2715</button>\n'
        '  </div>\n'

        # Search
        '  <div class="search-wrap">\n'
        '    <i class="fa-solid fa-magnifying-glass"></i>\n'
        '    <input class="search-input" type="text" id="searchInput"'
        '     placeholder="Search lectures..." oninput="filterContent(this.value)">\n'
        '  </div>\n'

        # Toolbar
        '  <div class="toolbar">\n'
        f'    <span class="badge">{total} lectures</span>\n'
        '    <span class="badge badge-result" id="search-result-count" style="display:none"></span>\n'
        '    <span class="badge badge-progress" id="progress-badge"></span>\n'
        '  </div>\n'

        # Content
        f'  <div id="content-container">{content_html}</div>\n'
        '</div>\n'

        # Footer
        '<div class="footer-wrap">\n'
        '  <a class="footer-credit-btn" href="https://babubhaikundan.pages.dev" target="_blank">\n'
        '    <span style="color:#00ffc8;font-weight:800;font-size:14px">Developer \U0001f480</span>\n'
        '    <span style="color:#ffd700;font-size:14px;font-weight:800">\U0001d542\U0001d566\U0001d55f\U0001d555\U0001d552\U0001d55f \U0001d550\U0001d552\U0001d555\U0001d552\U0001d567</span>\n'
        '  </a>\n'
        '  <p class="shortcut-hint">\n'
        '    \u2328 <b>Space</b>=play/pause &nbsp;\u2502&nbsp; <b>F</b>=fullscreen '
        '&nbsp;\u2502&nbsp; <b>&larr;/&rarr;</b>=&plusmn;10s '
        '&nbsp;\u2502&nbsp; <b>&uarr;/&darr;</b>=volume &nbsp;\u2502&nbsp; <b>M</b>=mute\n'
        '  </p>\n'
        '</div>\n'

        '<script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>\n'
        '<script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>\n'
        f'<script>{js}</script>\n'
        '</body>\n'
        '</html>'
    )
