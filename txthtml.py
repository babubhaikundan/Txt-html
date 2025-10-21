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

def categorize_urls(urls):
    """
    Smarter categorization that understands complex formats and links PDFs to videos.
    """
    lecture_map = {}  # Temporary map to group videos and PDFs by their full title

    # Step 1: Group URLs by their full name (the text before the colon)
    for name, url in urls:
        if name not in lecture_map:
            lecture_map[name] = {"videos": [], "pdfs": [], "others": []}
        
        if ".pdf" in url.lower():
            lecture_map[name]["pdfs"].append(url)
        elif any(vid_marker in url for vid_marker in [".m3u8", ".mp4", "youtube.com/embed", "akamaized.net"]):
            lecture_map[name]["videos"].append(url)
        else:
            lecture_map[name]["others"].append(url)

    # Step 2: Structure the grouped data into Subjects and Lectures
    categorized_data = {
        "subjects": {},  # Format: { "Subject": { "Lecture Title": {"videos": [], "pdfs": []} } }
        "unmatched_pdfs": [],
        "unmatched_others": []
    }

    for name, data in lecture_map.items():
        subject = "General"
        title = name
        
        # Regex to smartly find Subject and Title from various formats
        # Format 1: (Subject by Teacher) Lecture || Title
        match = re.search(r'^\((.*?)\)\s*(.*)', name)
        if match:
            subject = match.group(1).strip()
            title = match.group(2).strip().lstrip('|| ').strip()
        else:
            # Format 2: Subject by Teacher || Title
            # Format 3: Subject By Teacher || Topic #2
            parts = re.split(r'\s*\|\|\s*|\s+by\s+|\s+By\s+', name, 1)
            if len(parts) > 1 and ("Sir" in parts[0] or "Mam" in parts[0]):
                subject = parts[0].strip()
                title = parts[1].strip()
        
        # Ensure dictionaries exist
        if subject not in categorized_data["subjects"]:
            categorized_data["subjects"][subject] = {}
            
        # Store the grouped data under the extracted title
        categorized_data["subjects"][subject][title] = data
        
    return categorized_data


def generate_html(file_name, categorized_data):
    """Generates the final HTML with the new linked structure."""
    file_name_without_extension = os.path.splitext(file_name)[0]

    # --- Generate Video links with nested accordions and linked PDFs ---
    video_html = ""
    subjects = categorized_data.get("subjects", {})
    if not subjects:
        video_html = "<p>No content found to display.</p>"
    else:
        for subject, lectures in subjects.items():
            lecture_html = ""
            for title, data in lectures.items():
                
                # Create video links
                video_links = "".join(
                    f'<a href="#" class="list-item video-item" onclick="playVideo(\'{url}\', this)"><i class="fa-solid fa-circle-play"></i> {os.path.basename(title)}</a>'
                    for url in data["videos"]
                )
                
                # Create PDF links for THIS lecture
                pdf_links = "".join(
                    f'<a href="{url}" class="list-item pdf-item" target="_blank"><i class="fa-solid fa-file-pdf"></i> View PDF</a>'
                    for url in data["pdfs"]
                )
                
                # Combine them for one lecture entry
                lecture_html += f"""
                <div class="lecture-entry">
                    <p class="lecture-title">{title}</p>
                    <div class="lecture-links">
                        {video_links}
                        {pdf_links}
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

    # --- Footer remains the same ---
    new_footer = f"""
    <div style="display: flex; justify-content: center; margin-top: 20px; padding-bottom: 20px;">...</div> 
    """ # Note: Footer code is truncated for brevity, it's the same as before.

    # --- Main HTML Template ---
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
    <style>
        :root {{ --primary-color: #007bff; --bg-color: #f0f2f5; --card-bg: #ffffff; --header-bg: #1c1c1c; }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, sans-serif; }}
        body {{ background: var(--bg-color); }}
        .header {{ background: var(--header-bg); color: white; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; }}
        .main-container {{ padding: 15px; max-width: 1200px; margin: 0 auto; }}
        .player-wrapper {{ background: #000; margin-bottom: 15px; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 16px rgba(0,0,0,0.2); position: sticky; top: 10px; z-index: 1000; }}
        .search-bar input {{ width: 100%; padding: 12px; border: 2px solid #ccc; border-radius: 8px; font-size: 16px; margin-bottom: 15px; }}
        
        .accordion-item {{ margin-bottom: 10px; border: 1px solid #e0e0e0; border-radius: 8px; overflow: hidden; background: var(--card-bg); }}
        .accordion-header {{ width: 100%; background: #f9f9f9; border: none; text-align: left; padding: 15px; font-size: 18px; font-weight: 600; cursor: pointer; transition: background-color 0.3s; position: relative; }}
        .accordion-header:after {{ content: '+'; font-size: 24px; position: absolute; right: 20px; color: #888; }}
        .accordion-header.active:after {{ content: '-'; }}
        .accordion-header:hover {{ background-color: #e9e9e9; }}
        .accordion-content {{ padding: 0 15px; max-height: 0; overflow: hidden; transition: max-height 0.4s ease-out; }}
        
        .lecture-entry {{ padding: 15px 0; border-bottom: 1px solid #eee; }}
        .lecture-entry:last-child {{ border-bottom: none; }}
        .lecture-title {{ font-weight: 600; margin-bottom: 10px; color: #333; }}
        .lecture-links {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .list-item {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 6px; text-decoration: none; font-weight: 500; transition: all 0.2s ease; border: 1px solid transparent; }}
        .video-item {{ background-color: #e7f1ff; color: #0056b3; }}
        .video-item:hover, .video-item.playing {{ background-color: #007bff; color: white; transform: translateY(-2px); }}
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
        <div id="content-container">
            {video_html}
        </div>
    </div>
    {new_footer.replace("...", "<div style='display: flex; justify-content: center; margin-top: 20px; padding-bottom: 20px;'><a href='https://babubhaikundan.blogspot.com' target='_blank' style='display: flex; align-items: center; gap: 6px; background: #1a1a1a; padding: 6px 12px; border-radius: 12px; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.3);'><img src='https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg' alt='Telegram' style='width: 18px; height: 18px;'><span style='color: #00ffc8; font-weight: bold; font-size: 15px;'>Developer💀:-</span><span style='display: flex; align-items: center; gap: 5px; color: #FFD700;; font-size: 15px; font-weight: bold;'>𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧<img src='https://s.tfrbot.com/h/gL5VTi' alt='𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧' style='width: 20px; height: 20px; border-radius: 50%; object-fit: cover;'></span></a></div>")}

    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/videojs-contrib-quality-levels@4.0.0/dist/videojs-contrib-quality-levels.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/videojs-hls-quality-selector@1.1.4/dist/videojs-hls-quality-selector.min.js"></script>
    <script>
        const player = videojs('kundan-player', {{ fluid: true, plugins: {{ hlsQualitySelector: {{ displayCurrentQuality: true }} }} }});
        let currentlyPlaying = null;
        function playVideo(url, element) {{
            if (url.toLowerCase().includes('.m3u8')) {{
                player.src({{ src: url, type: 'application/x-mpegURL' }});
                player.play();
                if(currentlyPlaying) currentlyPlaying.classList.remove('playing');
                element.classList.add('playing');
                currentlyPlaying = element;
                document.querySelector('.player-wrapper').scrollIntoView({{ behavior: 'smooth' }});
            }} else {{ window.open(url, '_blank'); }}
        }}
        function filterContent() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            document.querySelectorAll('.accordion-item').forEach(subjectItem => {{
                let subjectHasVisibleLecture = false;
                subjectItem.querySelectorAll('.lecture-entry').forEach(lecture => {{
                    const title = lecture.querySelector('.lecture-title').textContent.toLowerCase();
                    const match = title.includes(searchTerm);
                    lecture.style.display = match ? '' : 'none';
                    if(match) subjectHasVisibleLecture = true;
                }});
                subjectItem.style.display = subjectHasVisibleLecture ? '' : 'none';
            }});
        }}
        document.querySelectorAll('.accordion-header').forEach(button => {{
            button.addEventListener('click', () => {{
                const content = button.nextElementSibling;
                button.classList.toggle('active');
                if (content.style.maxHeight) {{
                    content.style.maxHeight = null;
                }} else {{
                    content.style.maxHeight = content.scrollHeight + "px";
                }}
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