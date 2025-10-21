import os
import re
import subprocess
from vars import CREDIT

# Function to extract names and URLs from the text file
def extract_names_and_urls(file_content):
    lines = file_content.strip().split("\n")
    data = []
    for line in lines:
        if ":" in line:
            parts = line.split(":", 1)
            name = parts[0].strip()
            url = parts[1].strip()
            data.append((name, url))
    return data

# Function to categorize URLs into topics
def categorize_urls(urls):
    categorized_data = {
        "videos": {},
        "pdfs": [],
        "others": []
    }

    for name, url in urls:
        # URL categorization logic
        is_video = any(ext in url for ext in [".m3u8", ".mp4", "akamaized.net", "d1d34p8vz63oiq.cloudfront.net", "youtube.com/embed"])
        is_pdf = ".pdf" in url

        if is_video:
            # Topic extraction logic (e.g., from "Topic - Video Title")
            topic = "General Videos"  # Default topic
            if " - " in name:
                topic_part, title_part = name.split(" - ", 1)
                topic = topic_part.strip()
                name = title_part.strip()
            
            if topic not in categorized_data["videos"]:
                categorized_data["videos"][topic] = []

            # URL processing
            new_url = url
            if "akamaized.net/" in url or "1942403233.rsc.cdn77.org/" in url:
                new_url = f"https://www.khanglobalstudies.com/player?src={url}"
            elif "d1d34p8vz63oiq.cloudfront.net/" in url:
                # Note: 'your_working_token' needs to be replaced with an actual token if this is to work
                your_working_token = "YOUR_TOKEN_HERE" 
                new_url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={url}?token={your_working_token}"
            elif "youtube.com/embed" in url:
                yt_id = url.split('/')[-1].split('?')[0]
                new_url = f"https://www.youtube.com/watch?v={yt_id}"

            categorized_data["videos"][topic].append((name, new_url))
        elif is_pdf:
            categorized_data["pdfs"].append((name, url))
        else:
            categorized_data["others"].append((name, url))

    return categorized_data

# Function to generate the new, improved HTML file
def generate_html(file_name, categorized_data):
    file_name_without_extension = os.path.splitext(file_name)[0]

    # --- Generate Video links grouped by topic in accordions ---
    video_html = ""
    video_topics = categorized_data.get("videos", {})
    if not video_topics:
        video_html = "<p>No video links found.</p>"
    else:
        for topic, videos in video_topics.items():
            video_links = "".join(f'<a href="#" class="list-item" onclick="playVideo(\'{url}\', this)">{name}</a>' for name, url in videos)
            video_html += f"""
            <div class="accordion-item">
                <button class="accordion-header">{topic} ({len(videos)})</button>
                <div class="accordion-content">
                    {video_links}
                </div>
            </div>
            """

    # --- Generate PDF and Other links ---
    pdf_links = "".join(f'<a href="{url}" class="list-item" target="_blank">{name}</a>' for name, url in categorized_data.get("pdfs", []))
    other_links = "".join(f'<a href="{url}" class="list-item" target="_blank">{name}</a>' for name, url in categorized_data.get("others", []))

    # --- Updated Branding/Footer ---
    new_footer = f"""
    <!-- Compact Footer with Kundan Image START -->
    <div style="display: flex; justify-content: center; margin-top: 20px; padding-bottom: 20px;">
        <a href="https://babubhaikundan.blogspot.com" target="_blank" style="display: flex; align-items: center; gap: 6px; background: #1a1a1a; padding: 6px 12px; border-radius: 12px; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.3); transition: all 0.3s ease; white-space: nowrap;">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" alt="Telegram" style="width: 18px; height: 18px;">
            <span style="color: #00ffc8; font-weight: bold; font-size: 15px;">Developer💀:-</span>
            <span style="display: flex; align-items: center; gap: 5px; color: #FFD700;; font-size: 15px; font-weight: bold;">
                𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧
                <img src="https://s.tfrbot.com/h/gL5VTi" alt="𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧" style="width: 20px; height: 20px; border-radius: 50%; object-fit: cover;">
            </span>
        </a>
    </div>
    <!-- Compact Footer with Kundan Image END -->
    """

    # --- Main HTML Template ---
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{file_name_without_extension}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.2/css/all.min.css">
    <link href="https://vjs.zencdn.net/8.10.0/video-js.css" rel="stylesheet" />
    <link href="https://unpkg.com/@videojs/themes@1/dist/city/index.css" rel="stylesheet">
    <style>
        :root {{
            --primary-color: #007bff;
            --secondary-color: #0056b3;
            --background-color: #f0f2f5;
            --text-color: #333;
            --header-bg: #1c1c1c;
            --header-text: #ffffff;
            --card-bg: #ffffff;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }}
        body {{ background: var(--background-color); color: var(--text-color); line-height: 1.6; }}
        
        .header {{ background: var(--header-bg); color: var(--header-text); padding: 20px; text-align: center; font-size: 24px; font-weight: bold; box-shadow: 0 4px 8px rgba(0,0,0,0.2); }}
        .header .subheading {{ font-size: 16px; margin-top: 8px; color: #ccc; font-weight: normal; }}
        .header .subheading a {{ color: #ffeb3b; text-decoration: none; }}
        
        .main-container {{ padding: 20px; max-width: 1200px; margin: 0 auto; }}
        .player-wrapper {{ background: #000; margin-bottom: 20px; border-radius: 12px; overflow: hidden; box-shadow: 0 8px 16px rgba(0,0,0,0.2); }}
        .video-js.vjs-theme-city {{ width: 100%; height: auto; }}
        
        .tabs {{ display: flex; justify-content: center; gap: 10px; margin-bottom: 20px; }}
        .tab-button {{ flex: 1; padding: 12px; background: var(--card-bg); border: none; box-shadow: 0 2px 4px rgba(0,0,0,0.1); cursor: pointer; transition: all 0.3s ease; border-radius: 8px; font-size: 16px; font-weight: bold; text-align: center; }}
        .tab-button.active, .tab-button:hover {{ background: var(--primary-color); color: white; transform: translateY(-3px); }}
        
        .search-bar {{ margin-bottom: 20px; }}
        .search-bar input {{ width: 100%; padding: 12px; border: 2px solid #ccc; border-radius: 8px; font-size: 16px; transition: border-color 0.3s ease; }}
        .search-bar input:focus {{ border-color: var(--primary-color); outline: none; }}

        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .list-container {{ background: var(--card-bg); padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .list-item {{ display: block; padding: 12px 15px; margin: 5px 0; border-radius: 6px; text-decoration: none; color: var(--primary-color); font-weight: 500; transition: all 0.3s ease; border-left: 3px solid transparent; }}
        .list-item:hover, .list-item.playing {{ background: #e9f5ff; color: var(--secondary-color); border-left-color: var(--primary-color); transform: translateX(5px); }}
        
        .accordion-item {{ margin-bottom: 10px; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }}
        .accordion-header {{ width: 100%; background: #f7f7f7; border: none; text-align: left; padding: 15px; font-size: 16px; font-weight: bold; cursor: pointer; transition: background-color 0.3s; }}
        .accordion-header:hover {{ background-color: #e9e9e9; }}
        .accordion-content {{ padding: 0 15px; max-height: 0; overflow: hidden; transition: max-height 0.3s ease-out, padding 0.3s ease-out; background: var(--card-bg); }}
    </style>
</head>
<body>
    <div class="header">
        {file_name_without_extension}
        <div class="subheading">Extracted By: <a href="https://t.me/{CREDIT}" target="_blank">{CREDIT}</a></div>
    </div>

    <div class="main-container">
        <div class="player-wrapper">
            <video id="kundan-player" class="video-js vjs-theme-city" controls preload="auto" poster="https://i.imgur.com/7pA3gdA.png">
                <p class="vjs-no-js">To view this video please enable JavaScript.</p>
            </video>
        </div>

        <div class="search-bar">
            <input type="text" id="searchInput" placeholder="Search for videos, PDFs..." onkeyup="filterContent()">
        </div>

        <div class="tabs">
            <button class="tab-button active" onclick="showTab('videos')">Videos</button>
            <button class="tab-button" onclick="showTab('pdfs')">PDFs</button>
            <button class="tab-button" onclick="showTab('others')">Others</button>
        </div>

        <div id="videos" class="tab-content active list-container">
            {video_html}
        </div>
        <div id="pdfs" class="tab-content list-container">
            {pdf_links if pdf_links else "<p>No PDF links found.</p>"}
        </div>
        <div id="others" class="tab-content list-container">
            {other_links if other_links else "<p>No other links found.</p>"}
        </div>
    </div>
    
    {new_footer}

    <script src="https://vjs.zencdn.net/8.10.0/video.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/videojs-contrib-quality-levels@4.0.0/dist/videojs-contrib-quality-levels.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/videojs-hls-quality-selector@1.1.4/dist/videojs-hls-quality-selector.min.js"></script>
    <script>
        const player = videojs('kundan-player', {{
            fluid: true,
            html5: {{
                hls: {{
                    overrideNative: true, // Important for quality switching
                }}
            }},
            plugins: {{
                hlsQualitySelector: {{
                    displayCurrentQuality: true,
                }}
            }}
        }});

        let currentlyPlaying = null;

        function playVideo(url, element) {{
            if (url.toLowerCase().includes('.m3u8')) {{
                player.src({{ src: url, type: 'application/x-mpegURL' }});
                player.play();
                if(currentlyPlaying) {{
                    currentlyPlaying.classList.remove('playing');
                }}
                element.classList.add('playing');
                currentlyPlaying = element;
                document.querySelector('.player-wrapper').scrollIntoView({{ behavior: 'smooth' }});
            }} else {{
                window.open(url, '_blank');
            }}
        }}

        function showTab(tabName) {{
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.tab-button').forEach(b => b.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            document.querySelector(`.tab-button[onclick="showTab('${{tabName}}')"]`).classList.add('active');
        }}

        function filterContent() {{
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            document.querySelectorAll('.list-item').forEach(item => {{
                const itemText = item.textContent.toLowerCase();
                item.style.display = itemText.includes(searchTerm) ? '' : 'none';
            }});
        }}
        
        document.querySelectorAll('.accordion-header').forEach(button => {{
            button.addEventListener('click', () => {{
                const content = button.nextElementSibling;
                button.classList.toggle('active');
                if (content.style.maxHeight) {{
                    content.style.maxHeight = null;
                    content.style.padding = "0 15px";
                }} else {{
                    content.style.maxHeight = content.scrollHeight + "px";
                    content.style.padding = "15px";
                }}
            }});
        }});
    </script>
</body>
</html>
    """
    return html_template

# Function to download video using FFmpeg (Unchanged)
def download_video(url, output_path):
    command = f"ffmpeg -i {url} -c copy {output_path}"
    subprocess.run(command, shell=True, check=True)