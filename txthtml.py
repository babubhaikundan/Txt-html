import os
import re
import subprocess
from vars import CREDIT

def parse_line(name):
    """Smarter parsing to identify subject and title while maintaining order."""
    # Pattern 1: (Subject by Teacher) Anything else
    match = re.search(r'^\((.*?)\)', name)
    if match:
        subject = match.group(1).strip()
        title = name.replace(match.group(0), '').strip().lstrip('|| ').strip()
        return subject, title

    # Pattern 2: Subject by Teacher || Title
    match = re.search(r'^(.*? (?:by|By) (?:Sir|Mam))\s*\|\|\s*(.*)', name)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # Pattern 3 (Fallback): Anything before || is subject
    if '||' in name:
        parts = name.split('||', 1)
        return parts[0].strip(), parts[1].strip()
        
    # Final fallback
    return "General", name

def structure_data_in_order(urls):
    """
    Processes URLs sequentially to maintain their original order and groups them by subject.
    Links PDFs and videos of the same lecture together.
    """
    structured_list = []
    subject_map = {}
    
    # First, group PDFs and Videos by their exact name
    temp_map = {}
    for name, url in urls:
        if name not in temp_map:
            temp_map[name] = {"videos": [], "pdfs": []}
        
        if ".pdf" in url.lower():
            temp_map[name]["pdfs"].append(url)
        else: # Assume everything else is a video link
            temp_map[name]["videos"].append(url)
            
    # Now, process in order to create the final structure
    processed_names = set()
    for name, _ in urls:
        if name in processed_names:
            continue
        
        subject, title = parse_line(name)
        lecture_data = temp_map[name]

        if subject not in subject_map:
            new_subject = {"name": subject, "lectures": []}
            subject_map[subject] = new_subject
            structured_list.append(new_subject)
            
        subject_map[subject]["lectures"].append({
            "title": title,
            "videos": lecture_data["videos"],
            "pdfs": lecture_data["pdfs"]
        })
        processed_names.add(name)
        
    return structured_list

def generate_html(file_name, structured_list):
    """Generates the final, feature-rich HTML."""
    file_name_without_extension = os.path.splitext(file_name)[0]
    
    content_html = ""
    if not structured_list:
        content_html = "<p>No content found to display.</p>"
    else:
        for subject_data in structured_list:
            subject_name = subject_data["name"]
            lectures = subject_data["lectures"]
            
            lecture_html = ""
            for lecture in lectures:
                title = lecture["title"]
                video_links = "".join(f'<a href="#" class="list-item video-item" onclick="playVideo(event, \'{url}\', this)"><i class="fa-solid fa-circle-play"></i> Play Video</a>' for url in lecture["videos"])
                pdf_links = "".join(f'<a href="{url}" class="list-item pdf-item" target="_blank"><i class="fa-solid fa-file-pdf"></i> View PDF</a>' for url in lecture["pdfs"])
                
                lecture_html += f"""
                <div class="lecture-entry">
                    <p class="lecture-title">{title}</p>
                    <div class="lecture-links">{video_links}{pdf_links}</div>
                </div>
                """
            
            content_html += f"""
            <div class="accordion-item">
                <button class="accordion-header">{subject_name}</button>
                <div class="accordion-content">{lecture_html}</div>
            </div>
            """

    new_footer = f"""
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
        <a href="https://babubhaikundan.blogspot.com" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: #222; padding: 8px 16px; border-radius: 20px; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" alt="Telegram" style="width: 20px; height: 20px;">
            <span style="color: #00ffc8; font-weight: bold; font-size: 15px;">Developer💀:-</span>
            <span style="display: flex; align-items: center; gap: 5px; color: #FFD700; font-size: 15px; font-weight: bold;">
                𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧
                <img src="https://s.tfrbot.com/h/gL5VTi" alt="Kundan" style="width: 22px; height: 22px; border-radius: 50%;">
            </span>
        </a>
    </div>
    """

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_name_without_extension}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
    <link href="https://unpkg.com/@videojs/themes@1/dist/city/index.css" rel="stylesheet">
    <link href="https://cdn.jsdelivr.net/npm/videojs-seek-buttons/dist/videojs-seek-buttons.css" rel="stylesheet">
    <style>
        :root {{ --primary-color: #007bff; --bg-color: #f4f7f9; --card-bg: #ffffff; --header-bg: #1c1c1c; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background: var(--bg-color); }}
        .header {{ background: var(--header-bg); color: white; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; }}
        .main-container {{ padding: 15px; max-width: 1200px; margin: 0 auto; }}
        .player-wrapper {{ background: #000; margin-bottom: 20px; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.2); position: sticky; top: 10px; z-index: 1000; }}
        .search-bar input {{ width: 100%; padding: 14px; border: 2px solid #ddd; border-radius: 10px; font-size: 16px; margin-bottom: 20px; }}
        .accordion-item {{ margin-bottom: 10px; border-radius: 10px; overflow: hidden; background: var(--card-bg); box-shadow: 0 3px 8px rgba(0,0,0,0.08);}}
        .accordion-header {{ width: 100%; background: var(--card-bg); border: none; text-align: left; padding: 18px 20px; font-size: 18px; font-weight: 600; cursor: pointer; position: relative; }}
        .accordion-header:after {{ content: '+'; font-size: 24px; position: absolute; right: 20px; color: #888; transition: transform 0.3s ease; }}
        .accordion-header.active:after {{ transform: rotate(45deg); }}
        .accordion-content {{ padding: 0 20px; max-height: 0; overflow: hidden; transition: max-height 0.4s ease-out; }}
        .lecture-entry {{ padding: 15px 0; border-bottom: 1px solid #f0f0f0; }}
        .lecture-entry:last-child {{ border-bottom: none; }}
        .lecture-title {{ font-weight: 600; margin-bottom: 12px; color: #333; }}
        .lecture-links {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .list-item {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 15px; border-radius: 20px; text-decoration: none; font-weight: 500; transition: all 0.2s ease; }}
        .video-item {{ background-color: #e9f5ff; color: #0056b3; border: 1px solid #b3d7ff; }}
        .video-item.playing, .video-item:hover {{ background-color: #007bff; color: white; border-color: #007bff; transform: translateY(-2px); }}
        .pdf-item {{ background-color: #fff0e9; color: #d84315; border: 1px solid #ffd0b3; }}
        .pdf-item:hover {{ background-color: #ff5722; color: white; border-color: #ff5722; }}
    </style>
</head>
<body>
    <div class="header">{file_name_without_extension}</div>
    <div class="main-container">
        <div class="player-wrapper">
            <video id="kundan-player" class="video-js vjs-theme-city" controls preload="auto" poster="https://i.imgur.com/7pA3gdA.png"></video>
        </div>
        <div class="search-bar"><input type="text" id="searchInput" placeholder="Search for lectures..." onkeyup="filterContent()"></div>
        <div id="content-container">{content_html}</div>
    </div>
    {new_footer}

    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/videojs-contrib-quality-levels@4.0.0/dist/videojs-contrib-quality-levels.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/videojs-hls-quality-selector@1.1.4/dist/videojs-hls-quality-selector.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/videojs-seek-buttons/dist/videojs-seek-buttons.min.js"></script>
    <script>
        const player = videojs('kundan-player', {{
            fluid: true,
            controlBar: {{
                children: [ 'playToggle', 'seekButton', { 'name': 'seekButton', 'options': { 'forward': false } }, 'volumePanel', 'currentTimeDisplay', 'timeDivider', 'durationDisplay', 'progressControl', 'liveDisplay', 'remainingTimeDisplay', 'playbackRateMenuButton', 'fullscreenToggle' ]
            }},
            plugins: {{
                hlsQualitySelector: {{ displayCurrentQuality: true }},
                seekButtons: {{ forward: 10, back: 10 }}
            }}
        }});

        // Custom Double-tap to seek
        let lastTap = 0;
        player.on('touchstart', (event) => {{
            const now = new Date().getTime();
            const timeSince = now - lastTap;
            if (timeSince < 300 && timeSince > 0) {{
                const rect = player.el().getBoundingClientRect();
                const tapX = event.touches[0].clientX - rect.left;
                if (tapX < rect.width / 2) {{
                    player.currentTime(player.currentTime() - 10); // Seek back
                }} else {{
                    player.currentTime(player.currentTime() + 10); // Seek forward
                }}
            }}
            lastTap = now;
        }});

        let currentlyPlaying = null;
        function playVideo(event, url, element) {{
            event.preventDefault(); // <-- THIS FIXES THE PAGE JUMPING
            if (url.toLowerCase().includes('.m3u8')) {{
                player.src({{ src: url, type: 'application/x-mpegURL' }});
                player.play();
                if(currentlyPlaying) currentlyPlaying.classList.remove('playing');
                element.classList.add('playing');
                currentlyPlaying = element;
            }} else {{ window.open(url, '_blank'); }}
        }}

        // Accordion and Search script (no changes needed)
        document.querySelectorAll('.accordion-header').forEach(btn => btn.addEventListener('click', () => {{
            btn.classList.toggle('active');
            const content = btn.nextElementSibling;
            content.style.maxHeight = content.style.maxHeight ? null : content.scrollHeight + 'px';
        }}));

        function filterContent() {{
            const term = document.getElementById('searchInput').value.toLowerCase();
            document.querySelectorAll('.accordion-item').forEach(sub => {{
                let hasMatch = false;
                sub.querySelectorAll('.lecture-entry').forEach(lec => {{
                    const match = lec.querySelector('.lecture-title').textContent.toLowerCase().includes(term);
                    lec.style.display = match ? '' : 'none';
                    if(match) hasMatch = true;
                }});
                sub.style.display = hasMatch ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>
"""