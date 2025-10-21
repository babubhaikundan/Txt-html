import os
import re
import subprocess
from vars import CREDIT

def extract_names_and_urls(file_content):
    """Extracts lines into (name, url) tuples."""
    lines = file_content.strip().split("\n")
    data = []
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            name = parts[0].strip()
            url = parts[1].strip()
            if name and url:
                data.append((name, url))
    return data

def get_subject_and_title(name):
    """A smarter function to parse subject and title from various formats."""
    # Pattern 1: (Subject by Teacher) Lecture-01 || Title
    match = re.search(r'^\((.*?)\)\s*(.*)', name)
    if match:
        return match.group(1).strip(), match.group(2).strip().lstrip('|| ').strip()
    
    # Pattern 2: Subject by Teacher || Title
    match = re.search(r'^(.*? (?:by|By) (?:Sir|Mam))\s*\|\|\s*(.*)', name)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # Pattern 3 (Fallback): Anything before || is the subject
    if '||' in name:
        parts = name.split('||', 1)
        return parts[0].strip(), parts[1].strip()

    # Final fallback if no patterns match
    return "General Course", name


def categorize_urls(urls):
    """Categorizes URLs by smartly parsing subjects and linking PDFs to videos."""
    lecture_map = {}

    # Step 1: Group all URLs (videos, pdfs) by their full name
    for name, url in urls:
        if name not in lecture_map:
            lecture_map[name] = {"videos": [], "pdfs": [], "others": []}
        
        if ".pdf" in url.lower():
            lecture_map[name]["pdfs"].append(url)
        elif any(vid in url for vid in [".m3u8", ".mp4", "youtube.com/embed", "akamaized.net"]):
            lecture_map[name]["videos"].append(url)
        else:
            lecture_map[name]["others"].append(url)

    # Step 2: Structure the data by Subject -> Lecture
    categorized_data = {"subjects": {}}
    for name, data in lecture_map.items():
        subject, title = get_subject_and_title(name)
        
        if subject not in categorized_data["subjects"]:
            categorized_data["subjects"][subject] = {}
            
        categorized_data["subjects"][subject][title] = data
        
    return categorized_data


def generate_html(file_name, categorized_data):
    """Generates the final HTML with all the new features."""
    file_name_without_extension = os.path.splitext(file_name)[0]

    video_html = ""
    subjects = categorized_data.get("subjects", {})
    if not subjects:
        video_html = "<p>No content found to display.</p>"
    else:
        for subject, lectures in subjects.items():
            lecture_html = ""
            for title, data in lectures.items():
                video_links = "".join(
                    f'<a href="#" class="list-item video-item" onclick="playVideo(\'{url}\', this)"><i class="fa-solid fa-circle-play"></i> Play Video</a>'
                    for url in data["videos"]
                )
                pdf_links = "".join(
                    f'<a href="{url}" class="list-item pdf-item" target="_blank"><i class="fa-solid fa-file-pdf"></i> View PDF</a>'
                    for url in data["pdfs"]
                )
                
                lecture_html += f"""
                <div class="lecture-entry">
                    <p class="lecture-title">{title}</p>
                    <div class="lecture-links">
                        {video_links}{pdf_links}
                    </div>
                </div>
                """
            
            video_html += f"""
            <div class="accordion-item">
                <button class="accordion-header">{subject}</button>
                <div class="accordion-content">
                    {lecture_html}
                </div>
            </div>
            """
    
    new_footer = f"""
    <div style="display: flex; justify-content: center; margin: 20px 0; padding: 20px 0; border-top: 1px solid #ddd;">
        <a href="https://babubhaikundan.blogspot.com" target="_blank" style="display: flex; align-items: center; gap: 6px; background: #1a1a1a; padding: 6px 12px; border-radius: 12px; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.3);">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" alt="Telegram" style="width: 18px; height: 18px;">
            <span style="color: #00ffc8; font-weight: bold; font-size: 15px;">Developer💀:-</span>
            <span style="display: flex; align-items: center; gap: 5px; color: #FFD700;; font-size: 15px; font-weight: bold;">
                𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧
                <img src="https://s.tfrbot.com/h/gL5VTi" alt="𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧" style="width: 20px; height: 20px; border-radius: 50%; object-fit: cover;">
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
        :root {{ --primary-color: #007bff; --bg-color: #f0f2f5; --card-bg: #ffffff; --header-bg: #1c1c1c; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, sans-serif; }}
        body {{ background: var(--bg-color); }}
        .header {{ background: var(--header-bg); color: white; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; }}
        .main-container {{ padding: 15px; max-width: 1200px; margin: 0 auto; }}
        .player-wrapper {{ background: #000; margin-bottom: 15px; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 16px rgba(0,0,0,0.2); position: sticky; top: 10px; z-index: 1000; }}
        .search-bar input {{ width: 100%; padding: 12px; border: 2px solid #ccc; border-radius: 8px; font-size: 16px; margin-bottom: 15px; }}
        .accordion-item {{ margin-bottom: 10px; border-radius: 8px; overflow: hidden; background: var(--card-bg); box-shadow: 0 2px 4px rgba(0,0,0,0.05);}}
        .accordion-header {{ width: 100%; background: var(--card-bg); border: none; border-bottom: 1px solid #eee; text-align: left; padding: 15px; font-size: 18px; font-weight: 600; cursor: pointer; transition: background-color 0.3s; position: relative; }}
        .accordion-header:after {{ content: '+'; font-size: 24px; position: absolute; right: 20px; color: #888; transition: transform 0.3s; }}
        .accordion-header.active:after {{ transform: rotate(45deg); }}
        .accordion-content {{ padding: 0 15px; max-height: 0; overflow: hidden; transition: max-height 0.4s ease-out; }}
        .lecture-entry {{ padding: 15px 0; border-bottom: 1px solid #f0f0f0; }}
        .lecture-entry:last-child {{ border-bottom: none; }}
        .lecture-title {{ font-weight: 600; margin-bottom: 10px; color: #333; }}
        .lecture-links {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .list-item {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 20px; text-decoration: none; font-weight: 500; transition: all 0.2s ease; }}
        .video-item {{ background-color: #e7f1ff; color: #0056b3; }}
        .video-item.playing, .video-item:hover {{ background-color: #007bff; color: white; }}
        .pdf-item {{ background-color: #fbe9e7; color: #d84315; }}
        .pdf-item:hover {{ background-color: #ff5722; color: white; }}
    </style>
</head>
<body>
    <div class="header">{file_name_without_extension}</div>
    <div class="main-container">
        <div class="player-wrapper">
            <video id="kundan-player" class="video-js vjs-theme-city" controls preload="auto" poster="https://i.imgur.com/7pA3gdA.png"></video>
        </div>
        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="Search for lectures..." onkeyup="filterContent()">
        </div>
        <div id="content-container">{video_html}</div>
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
                children: [ 'playToggle', 'currentTimeDisplay', 'timeDivider', 'durationDisplay', 'progressControl', 'liveDisplay', 'remainingTimeDisplay', 'customControlSpacer', 'playbackRateMenuButton', 'fullscreenToggle' ]
            }},
            plugins: {{
                hlsQualitySelector: {{ displayCurrentQuality: true }},
                seekButtons: {{ forward: 10, back: 10 }}
            }}
        }});
        let currentlyPlaying = null;
        function playVideo(url, element) {{
            if (url.toLowerCase().includes('.m3u8')) {{
                player.src({{ src: url, type: 'application/x-mpegURL' }});
                player.play();
                if(currentlyPlaying) currentlyPlaying.classList.remove('playing');
                element.classList.add('playing');
                currentlyPlaying = element;
            }} else {{ window.open(url, '_blank'); }}
        }}
        // The rest of the script for search and accordion remains the same
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
        document.querySelectorAll('.accordion-header').forEach(btn => {{
            btn.addEventListener('click', () => {{
                const content = btn.nextElementSibling;
                btn.classList.toggle('active');
                content.style.maxHeight = content.style.maxHeight ? null : content.scrollHeight + 'px';
            }});
        }});
    </script>
</body>
</html>
"""

# Download function remains unchanged
def download_video(url, output_path):
    command = f"ffmpeg -i {url} -c copy {output_path}"
    subprocess.run(command, shell=True, check=True)