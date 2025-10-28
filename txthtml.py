import os
import re

def extract_names_and_urls(file_content):
    """
    Extracts (name, url) pairs from the raw text content. Required by main.py.
    """
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

def parse_line(name):
    """
    Smart parsing with 5 rules to identify subject, topic, and title
    Returns: (subject, topic, title)
    """
    # Rule 1: Bracket wala Subject (Highest Priority)
    match = re.search(r'^\((.*?)\)\s*(.+)', name)
    if match:
        subject = match.group(1).strip()
        remaining = match.group(2).strip().lstrip('||').strip()
        # Check if there's a topic in remaining
        topic = extract_topic(remaining)
        return subject, topic, remaining
    
    # Rule 2: "by Sir/Mam" aur "||" wala Format
    match = re.search(r'^(.*?\s+(?:by|By)\s+(?:Sir|Mam))\s*\|\|\s*(.+)', name)
    if match:
        subject = match.group(1).strip()
        title = match.group(2).strip()
        topic = extract_topic(title)
        return subject, topic, title
    
    # Rule 3: Sirf "||" wala Format
    if '||' in name:
        parts = name.split('||', 1)
        subject = parts[0].strip()
        title = parts[1].strip()
        topic = extract_topic(title)
        return subject, topic, title
    
    # Rule 5: Default (Jab kuch match na ho)
    return "General", None, name

def extract_topic(title):
    """
    Extract topic name from title by removing numbering patterns like #1, #2, etc.
    Returns base topic name without numbers
    """
    # Remove patterns like #1, #2, #8, etc. at the end
    topic = re.sub(r'\s*#\d+\s*

def structure_data_in_order(urls):
    """
    Processes URLs sequentially to maintain their original order and groups them by subject.
    """
    structured_list, subject_map, temp_map = [], {}, {}
    for name, url in urls:
        if name not in temp_map: temp_map[name] = {"videos": [], "pdfs": []}
        if ".pdf" in url.lower(): temp_map[name]["pdfs"].append(url)
        else: temp_map[name]["videos"].append(url)
            
    processed_names = set()
    for name, _ in urls:
        if name in processed_names: continue
        subject, title = parse_line(name)
        if subject not in subject_map:
            new_subject = {"name": subject, "lectures": []}
            subject_map[subject] = new_subject
            structured_list.append(new_subject)
        subject_map[subject]["lectures"].append({"title": title, **temp_map[name]})
        processed_names.add(name)
    return structured_list

def generate_html(file_name, structured_list):
    """
    FINAL WORKING SOLUTION - Research-based fixes for BOTH issues
    """
    content_html = ""
    if not structured_list:
        content_html = "<p class='text-center text-white'>No content found.</p>"
    else:
        item_id_counter = 0
        for subject_data in structured_list:
            subject_name, lectures = subject_data["name"], subject_data["lectures"]
            lecture_html = ""
            for lecture in lectures:
                title, videos, pdfs = lecture["title"], lecture["videos"], lecture["pdfs"]
                video_links = "".join(f'<a href="#" class="list-item video-item" onclick="playVideo(event, \'{url}\', this)"><i class="fa-solid fa-circle-play"></i> Play</a>' for url in videos)
                pdf_links = "".join(f'<a href="{url}" target="_blank" class="list-item pdf-item"><i class="fa-solid fa-file-pdf"></i> PDF</a>' for url in pdfs)
                lecture_html += f"""
                <div class="lecture-entry">
                    <p class="lecture-title">{title}</p><div class="lecture-links">{video_links}{pdf_links}</div>
                </div>"""
            item_id = f"item{item_id_counter}"
            content_html += f"""
            <div class="accordion-item">
                <button class="accordion-header">{subject_name}</button><div class="accordion-content">{lecture_html}</div>
            </div>"""
            item_id_counter += 1

    new_footer = """
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
        <a href="https://babubhaikundan.blogspot.com" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: #222; padding: 8px 16px; border-radius: 20px; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" alt="Telegram" style="width: 20px; height: 20px;">
            <span style="color: #00ffc8; font-weight: bold; font-size: 15px;">Developer💀:-</span>
            <span style="display: flex; align-items: center; gap: 5px; color: #FFD700; font-size: 15px; font-weight: bold;">
                𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧 <img src="https://s.tfrbot.com/h/gL5VTi" alt="Kundan" style="width: 22px; height: 22px; border-radius: 50%;">
            </span>
        </a>
    </div>"""

    return f"""
<!DOCTYPE html><html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{file_name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <style>
        :root {{--plyr-color-main: #00b3ff; --bg-color: #f4f7f9; --card-bg: #ffffff; --header-bg: #1c1c1c;}}
        * {{margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;}}
        body {{background: var(--bg-color);}} .header {{background: var(--header-bg); color: white; padding: 20px; text-align: center; font-size: 24px; font-weight: bold;}}
        .main-container {{padding: 15px; max-width: 1200px; margin: 0 auto;}}
        .player-wrapper {{background: #000; margin-bottom: 20px; border-radius: 12px; overflow: visible !important; box-shadow: 0 10px 25px rgba(0,0,0,0.2); position: sticky; top: 10px; z-index: 1000;}}
        .player-wrapper video {{pointer-events: none !important;}}
        .plyr {{pointer-events: auto !important; overflow: visible !important;}}
        .plyr__controls {{pointer-events: auto !important;}}
        .plyr__menu {{z-index: 10000 !important; position: relative !important;}}
        .plyr__menu__container {{max-height: 350px !important; overflow-y: auto !important; z-index: 10001 !important;}}
        .search-bar input {{width: 100%; padding: 14px; border: 2px solid #ddd; border-radius: 10px; font-size: 16px; margin-bottom: 20px;}}
        .accordion-item {{margin-bottom: 10px; border-radius: 10px; overflow: hidden; background: var(--card-bg); box-shadow: 0 3px 8px rgba(0,0,0,0.08);}}
        .accordion-header {{width: 100%; background: var(--card-bg); border: none; text-align: left; padding: 18px 20px; font-size: 18px; font-weight: 600; cursor: pointer; position: relative;}}
        .accordion-header:after {{content: '+'; font-size: 24px; position: absolute; right: 20px; color: #888; transition: transform 0.3s ease;}}
        .accordion-header.active:after {{transform: rotate(45deg);}}
        .accordion-content {{padding: 0 20px; max-height: 0; overflow: hidden; transition: max-height 0.4s ease-out;}}
        .lecture-entry {{padding: 15px 0; border-bottom: 1px solid #f0f0f0;}} .lecture-entry:last-child {{border-bottom: none;}}
        .lecture-title {{font-weight: 600; margin-bottom: 12px; color: #333;}} .lecture-links {{display: flex; flex-wrap: wrap; gap: 10px;}}
        .list-item {{display: inline-flex; align-items: center; gap: 8px; padding: 8px 15px; border-radius: 20px; text-decoration: none; font-weight: 500; transition: all 0.2s ease; cursor: pointer;}}
        .video-item {{background-color: #e9f5ff; color: #0056b3; border: 1px solid #b3d7ff;}}
        .video-item.playing, .video-item:hover {{background-color: #007bff; color: white; border-color: #007bff; transform: translateY(-2px);}}
        .pdf-item {{background-color: #fff0e9; color: #d84315; border: 1px solid #ffd0b3;}}
        .pdf-item:hover {{background-color: #ff5722; color: white; border-color: #ff5722;}}
        .plyr--volume {{display: none !important;}}
    </style>
</head>
<body>
    <div class="header">{file_name}</div>
    <div class="main-container">
        <div class="player-wrapper"><video id="player" playsinline controls crossorigin preload="metadata"></video></div>
        <div class="search-bar"><input type="text" id="searchInput" placeholder="Search..." onkeyup="filterContent()"></div>
        <div id="content-container">{content_html}</div>
    </div>
    {new_footer}
    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script>
        let player = null;
        let hls = null;
        let isPlayerReady = false;
        let playerWrapper, video;
        let lastTapTime = 0;
        let pendingVideoUrl = null;
        
        document.addEventListener('DOMContentLoaded', () => {{
            video = document.getElementById('player');
            playerWrapper = document.querySelector('.player-wrapper');
            setupDoubleTapSeek();
        }});
        
        function setupDoubleTapSeek() {{
            playerWrapper.addEventListener('dblclick', (e) => {{
                if (e.target.closest('.plyr__controls')) return;
                
                e.preventDefault();
                e.stopImmediatePropagation();
                
                if (player && isPlayerReady) {{
                    const rect = playerWrapper.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    
                    if (x < rect.width / 2) {{
                        player.rewind(10);
                        console.log('⏪ -10s');
                    }} else {{
                        player.forward(10);
                        console.log('⏩ +10s');
                    }}
                }}
            }});
            
            playerWrapper.addEventListener('touchend', (e) => {{
                if (e.target.closest('.plyr__controls')) return;
                
                const now = Date.now();
                const diff = now - lastTapTime;
                
                if (diff > 0 && diff < 300 && lastTapTime > 0) {{
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    
                    if (player && isPlayerReady) {{
                        const rect = playerWrapper.getBoundingClientRect();
                        const x = e.changedTouches[0].clientX - rect.left;
                        
                        if (x < rect.width / 2) {{
                            player.rewind(10);
                        }} else {{
                            player.forward(10);
                        }}
                    }}
                    lastTapTime = 0;
                }} else {{
                    lastTapTime = now;
                    setTimeout(() => lastTapTime = 0, 300);
                }}
            }});
        }}
        
        let currentlyPlaying = null;
        
        function playVideo(event, url, element) {{
            event.preventDefault();
            
            if (currentlyPlaying) currentlyPlaying.classList.remove('playing');
            element.classList.add('playing');
            currentlyPlaying = element;
            
            isPlayerReady = false;
            pendingVideoUrl = url;
            
            console.log('🎬 Starting new video:', url);
            
            // CRITICAL: Proper cleanup based on research
            if (hls) {{
                console.log('Cleaning up HLS');
                
                // Listen for MEDIA_DETACHED event before loading new video
                hls.once(Hls.Events.MEDIA_DETACHED, function() {{
                    console.log('✅ Media detached, loading new video');
                    hls = null;
                    
                    // Now load the new video
                    if (pendingVideoUrl) {{
                        loadNewVideo(pendingVideoUrl);
                        pendingVideoUrl = null;
                    }}
                }});
                
                // Remove all event listeners
                hls.off(Hls.Events.MANIFEST_PARSED);
                hls.off(Hls.Events.ERROR);
                
                // Destroy HLS (will trigger MEDIA_DETACHED)
                hls.destroy();
            }} else {{
                // No HLS to clean up, load directly
                if (player) {{
                    console.log('Destroying Plyr');
                    player.off('ready');
                    player.off('enterfullscreen');
                    player.off('exitfullscreen');
                    player.destroy();
                    player = null;
                }}
                
                // Clear video element
                video.removeAttribute('src');
                video.load();
                
                setTimeout(() => {{
                    loadNewVideo(url);
                    pendingVideoUrl = null;
                }}, 50);
            }}
        }}
        
        function loadNewVideo(url) {{
            console.log('📹 Loading video:', url);
            
            if (url.includes('.m3u8')) {{
                // HLS VIDEO
                if (Hls.isSupported()) {{
                    console.log('🎬 Loading HLS');
                    
                    hls = new Hls({{
                        enableWorker: true,
                        maxBufferLength: 30
                    }});
                    
                    hls.loadSource(url);
                    hls.attachMedia(video);
                    
                    hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                        const availableQualities = hls.levels.map(l => l.height);
                        availableQualities.unshift(0);
                        
                        console.log('✅ Qualities:', availableQualities);
                        
                        // Create Plyr
                        player = new Plyr(video, {{
                            controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'settings', 'pip', 'fullscreen'],
                            settings: ['quality', 'speed'],
                            speed: {{ selected: 1, options: [0.5, 0.75, 1, 1.5, 2] }},
                            quality: {{
                                default: 0,
                                options: availableQualities,
                                forced: true,
                                onChange: (quality) => updateQuality(quality)
                            }},
                            i18n: {{ qualityLabel: {{ 0: 'Auto' }} }},
                            fullscreen: {{ enabled: true, fallback: true, iosNative: true }},
                            clickToPlay: true
                        }});
                        
                        // Wait for Plyr ready
                        player.on('ready', () => {{
                            isPlayerReady = true;
                            console.log('✅ Plyr ready');
                            
                            player.play().then(() => {{
                                console.log('✅ Playing');
                            }}).catch(err => {{
                                console.log('Autoplay blocked:', err.message);
                            }});
                        }});
                        
                        // Fullscreen orientation
                        player.on('enterfullscreen', () => {{
                            try {{
                                if (screen.orientation?.lock) screen.orientation.lock('landscape');
                            }} catch(e) {{}}
                        }});
                        
                        player.on('exitfullscreen', () => {{
                            try {{
                                if (screen.orientation?.unlock) screen.orientation.unlock();
                            }} catch(e) {{}}
                        }});
                    }});
                    
                    hls.on(Hls.Events.ERROR, function(event, data) {{
                        if (data.fatal) {{
                            console.error('❌ HLS Error:', data.type);
                            switch(data.type) {{
                                case Hls.ErrorTypes.NETWORK_ERROR:
                                    hls.startLoad();
                                    break;
                                case Hls.ErrorTypes.MEDIA_ERROR:
                                    hls.recoverMediaError();
                                    break;
                                default:
                                    console.error('Fatal error');
                                    break;
                            }}
                        }}
                    }});
                    
                }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                    // Safari
                    video.src = url;
                    player = new Plyr(video, {{
                        controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'settings', 'pip', 'fullscreen'],
                        settings: ['speed'],
                        speed: {{ selected: 1, options: [0.5, 0.75, 1, 1.5, 2] }}
                    }});
                    
                    player.on('ready', () => {{
                        isPlayerReady = true;
                        player.play();
                    }});
                }}
            }} else {{
                // MP4
                video.src = url;
                player = new Plyr(video, {{
                    controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'settings', 'pip', 'fullscreen'],
                    settings: ['speed'],
                    speed: {{ selected: 1, options: [0.5, 0.75, 1, 1.5, 2] }}
                }});
                
                player.on('ready', () => {{
                    isPlayerReady = true;
                    player.play();
                }});
            }}
        }}
        
        function updateQuality(newQuality) {{
            if (!hls) return;
            
            if (newQuality === 0) {{
                hls.currentLevel = -1;
            }} else {{
                hls.levels.forEach((level, index) => {{
                    if (level.height === newQuality) {{
                        hls.currentLevel = index;
                    }}
                }});
            }}
        }}
        
        // Accordion
        document.querySelectorAll('.accordion-header').forEach(btn => {{
            btn.addEventListener('click', () => {{
                btn.classList.toggle('active');
                const content = btn.nextElementSibling;
                content.style.maxHeight = content.style.maxHeight ? null : content.scrollHeight + 'px';
            }});
        }});
        
        // Search
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
</html>"""
, '', title).strip()
    # If topic is different from title, return it, else None
    return topic if topic != title else None

def structure_data_in_order(urls):
    """
    Processes URLs sequentially to maintain their original order and groups them by subject.
    """
    structured_list, subject_map, temp_map = [], {}, {}
    for name, url in urls:
        if name not in temp_map: temp_map[name] = {"videos": [], "pdfs": []}
        if ".pdf" in url.lower(): temp_map[name]["pdfs"].append(url)
        else: temp_map[name]["videos"].append(url)
            
    processed_names = set()
    for name, _ in urls:
        if name in processed_names: continue
        subject, title = parse_line(name)
        if subject not in subject_map:
            new_subject = {"name": subject, "lectures": []}
            subject_map[subject] = new_subject
            structured_list.append(new_subject)
        subject_map[subject]["lectures"].append({"title": title, **temp_map[name]})
        processed_names.add(name)
    return structured_list

def generate_html(file_name, structured_list):
    """
    FINAL WORKING SOLUTION - Research-based fixes for BOTH issues
    """
    content_html = ""
    if not structured_list:
        content_html = "<p class='text-center text-white'>No content found.</p>"
    else:
        item_id_counter = 0
        for subject_data in structured_list:
            subject_name, lectures = subject_data["name"], subject_data["lectures"]
            lecture_html = ""
            for lecture in lectures:
                title, videos, pdfs = lecture["title"], lecture["videos"], lecture["pdfs"]
                video_links = "".join(f'<a href="#" class="list-item video-item" onclick="playVideo(event, \'{url}\', this)"><i class="fa-solid fa-circle-play"></i> Play</a>' for url in videos)
                pdf_links = "".join(f'<a href="{url}" target="_blank" class="list-item pdf-item"><i class="fa-solid fa-file-pdf"></i> PDF</a>' for url in pdfs)
                lecture_html += f"""
                <div class="lecture-entry">
                    <p class="lecture-title">{title}</p><div class="lecture-links">{video_links}{pdf_links}</div>
                </div>"""
            item_id = f"item{item_id_counter}"
            content_html += f"""
            <div class="accordion-item">
                <button class="accordion-header">{subject_name}</button><div class="accordion-content">{lecture_html}</div>
            </div>"""
            item_id_counter += 1

    new_footer = """
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
        <a href="https://babubhaikundan.blogspot.com" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: #222; padding: 8px 16px; border-radius: 20px; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" alt="Telegram" style="width: 20px; height: 20px;">
            <span style="color: #00ffc8; font-weight: bold; font-size: 15px;">Developer💀:-</span>
            <span style="display: flex; align-items: center; gap: 5px; color: #FFD700; font-size: 15px; font-weight: bold;">
                𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧 <img src="https://s.tfrbot.com/h/gL5VTi" alt="Kundan" style="width: 22px; height: 22px; border-radius: 50%;">
            </span>
        </a>
    </div>"""

    return f"""
<!DOCTYPE html><html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{file_name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <style>
        :root {{--plyr-color-main: #00b3ff; --bg-color: #f4f7f9; --card-bg: #ffffff; --header-bg: #1c1c1c;}}
        * {{margin: 0; padding: 0; box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;}}
        body {{background: var(--bg-color);}} .header {{background: var(--header-bg); color: white; padding: 20px; text-align: center; font-size: 24px; font-weight: bold;}}
        .main-container {{padding: 15px; max-width: 1200px; margin: 0 auto;}}
        .player-wrapper {{background: #000; margin-bottom: 20px; border-radius: 12px; overflow: visible !important; box-shadow: 0 10px 25px rgba(0,0,0,0.2); position: sticky; top: 10px; z-index: 1000;}}
        .player-wrapper video {{pointer-events: none !important;}}
        .plyr {{pointer-events: auto !important; overflow: visible !important;}}
        .plyr__controls {{pointer-events: auto !important;}}
        .plyr__menu {{z-index: 10000 !important; position: relative !important;}}
        .plyr__menu__container {{max-height: 350px !important; overflow-y: auto !important; z-index: 10001 !important;}}
        .search-bar input {{width: 100%; padding: 14px; border: 2px solid #ddd; border-radius: 10px; font-size: 16px; margin-bottom: 20px;}}
        .accordion-item {{margin-bottom: 10px; border-radius: 10px; overflow: hidden; background: var(--card-bg); box-shadow: 0 3px 8px rgba(0,0,0,0.08);}}
        .accordion-header {{width: 100%; background: var(--card-bg); border: none; text-align: left; padding: 18px 20px; font-size: 18px; font-weight: 600; cursor: pointer; position: relative;}}
        .accordion-header:after {{content: '+'; font-size: 24px; position: absolute; right: 20px; color: #888; transition: transform 0.3s ease;}}
        .accordion-header.active:after {{transform: rotate(45deg);}}
        .accordion-content {{padding: 0 20px; max-height: 0; overflow: hidden; transition: max-height 0.4s ease-out;}}
        .lecture-entry {{padding: 15px 0; border-bottom: 1px solid #f0f0f0;}} .lecture-entry:last-child {{border-bottom: none;}}
        .lecture-title {{font-weight: 600; margin-bottom: 12px; color: #333;}} .lecture-links {{display: flex; flex-wrap: wrap; gap: 10px;}}
        .list-item {{display: inline-flex; align-items: center; gap: 8px; padding: 8px 15px; border-radius: 20px; text-decoration: none; font-weight: 500; transition: all 0.2s ease; cursor: pointer;}}
        .video-item {{background-color: #e9f5ff; color: #0056b3; border: 1px solid #b3d7ff;}}
        .video-item.playing, .video-item:hover {{background-color: #007bff; color: white; border-color: #007bff; transform: translateY(-2px);}}
        .pdf-item {{background-color: #fff0e9; color: #d84315; border: 1px solid #ffd0b3;}}
        .pdf-item:hover {{background-color: #ff5722; color: white; border-color: #ff5722;}}
        .plyr--volume {{display: none !important;}}
    </style>
</head>
<body>
    <div class="header">{file_name}</div>
    <div class="main-container">
        <div class="player-wrapper"><video id="player" playsinline controls crossorigin preload="metadata"></video></div>
        <div class="search-bar"><input type="text" id="searchInput" placeholder="Search..." onkeyup="filterContent()"></div>
        <div id="content-container">{content_html}</div>
    </div>
    {new_footer}
    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script>
        let player = null;
        let hls = null;
        let isPlayerReady = false;
        let playerWrapper, video;
        let lastTapTime = 0;
        let pendingVideoUrl = null;
        
        document.addEventListener('DOMContentLoaded', () => {{
            video = document.getElementById('player');
            playerWrapper = document.querySelector('.player-wrapper');
            setupDoubleTapSeek();
        }});
        
        function setupDoubleTapSeek() {{
            playerWrapper.addEventListener('dblclick', (e) => {{
                if (e.target.closest('.plyr__controls')) return;
                
                e.preventDefault();
                e.stopImmediatePropagation();
                
                if (player && isPlayerReady) {{
                    const rect = playerWrapper.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    
                    if (x < rect.width / 2) {{
                        player.rewind(10);
                        console.log('⏪ -10s');
                    }} else {{
                        player.forward(10);
                        console.log('⏩ +10s');
                    }}
                }}
            }});
            
            playerWrapper.addEventListener('touchend', (e) => {{
                if (e.target.closest('.plyr__controls')) return;
                
                const now = Date.now();
                const diff = now - lastTapTime;
                
                if (diff > 0 && diff < 300 && lastTapTime > 0) {{
                    e.preventDefault();
                    e.stopImmediatePropagation();
                    
                    if (player && isPlayerReady) {{
                        const rect = playerWrapper.getBoundingClientRect();
                        const x = e.changedTouches[0].clientX - rect.left;
                        
                        if (x < rect.width / 2) {{
                            player.rewind(10);
                        }} else {{
                            player.forward(10);
                        }}
                    }}
                    lastTapTime = 0;
                }} else {{
                    lastTapTime = now;
                    setTimeout(() => lastTapTime = 0, 300);
                }}
            }});
        }}
        
        let currentlyPlaying = null;
        
        function playVideo(event, url, element) {{
            event.preventDefault();
            
            if (currentlyPlaying) currentlyPlaying.classList.remove('playing');
            element.classList.add('playing');
            currentlyPlaying = element;
            
            isPlayerReady = false;
            pendingVideoUrl = url;
            
            console.log('🎬 Starting new video:', url);
            
            // CRITICAL: Proper cleanup based on research
            if (hls) {{
                console.log('Cleaning up HLS');
                
                // Listen for MEDIA_DETACHED event before loading new video
                hls.once(Hls.Events.MEDIA_DETACHED, function() {{
                    console.log('✅ Media detached, loading new video');
                    hls = null;
                    
                    // Now load the new video
                    if (pendingVideoUrl) {{
                        loadNewVideo(pendingVideoUrl);
                        pendingVideoUrl = null;
                    }}
                }});
                
                // Remove all event listeners
                hls.off(Hls.Events.MANIFEST_PARSED);
                hls.off(Hls.Events.ERROR);
                
                // Destroy HLS (will trigger MEDIA_DETACHED)
                hls.destroy();
            }} else {{
                // No HLS to clean up, load directly
                if (player) {{
                    console.log('Destroying Plyr');
                    player.off('ready');
                    player.off('enterfullscreen');
                    player.off('exitfullscreen');
                    player.destroy();
                    player = null;
                }}
                
                // Clear video element
                video.removeAttribute('src');
                video.load();
                
                setTimeout(() => {{
                    loadNewVideo(url);
                    pendingVideoUrl = null;
                }}, 50);
            }}
        }}
        
        function loadNewVideo(url) {{
            console.log('📹 Loading video:', url);
            
            if (url.includes('.m3u8')) {{
                // HLS VIDEO
                if (Hls.isSupported()) {{
                    console.log('🎬 Loading HLS');
                    
                    hls = new Hls({{
                        enableWorker: true,
                        maxBufferLength: 30
                    }});
                    
                    hls.loadSource(url);
                    hls.attachMedia(video);
                    
                    hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                        const availableQualities = hls.levels.map(l => l.height);
                        availableQualities.unshift(0);
                        
                        console.log('✅ Qualities:', availableQualities);
                        
                        // Create Plyr
                        player = new Plyr(video, {{
                            controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'settings', 'pip', 'fullscreen'],
                            settings: ['quality', 'speed'],
                            speed: {{ selected: 1, options: [0.5, 0.75, 1, 1.5, 2] }},
                            quality: {{
                                default: 0,
                                options: availableQualities,
                                forced: true,
                                onChange: (quality) => updateQuality(quality)
                            }},
                            i18n: {{ qualityLabel: {{ 0: 'Auto' }} }},
                            fullscreen: {{ enabled: true, fallback: true, iosNative: true }},
                            clickToPlay: true
                        }});
                        
                        // Wait for Plyr ready
                        player.on('ready', () => {{
                            isPlayerReady = true;
                            console.log('✅ Plyr ready');
                            
                            player.play().then(() => {{
                                console.log('✅ Playing');
                            }}).catch(err => {{
                                console.log('Autoplay blocked:', err.message);
                            }});
                        }});
                        
                        // Fullscreen orientation
                        player.on('enterfullscreen', () => {{
                            try {{
                                if (screen.orientation?.lock) screen.orientation.lock('landscape');
                            }} catch(e) {{}}
                        }});
                        
                        player.on('exitfullscreen', () => {{
                            try {{
                                if (screen.orientation?.unlock) screen.orientation.unlock();
                            }} catch(e) {{}}
                        }});
                    }});
                    
                    hls.on(Hls.Events.ERROR, function(event, data) {{
                        if (data.fatal) {{
                            console.error('❌ HLS Error:', data.type);
                            switch(data.type) {{
                                case Hls.ErrorTypes.NETWORK_ERROR:
                                    hls.startLoad();
                                    break;
                                case Hls.ErrorTypes.MEDIA_ERROR:
                                    hls.recoverMediaError();
                                    break;
                                default:
                                    console.error('Fatal error');
                                    break;
                            }}
                        }}
                    }});
                    
                }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                    // Safari
                    video.src = url;
                    player = new Plyr(video, {{
                        controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'settings', 'pip', 'fullscreen'],
                        settings: ['speed'],
                        speed: {{ selected: 1, options: [0.5, 0.75, 1, 1.5, 2] }}
                    }});
                    
                    player.on('ready', () => {{
                        isPlayerReady = true;
                        player.play();
                    }});
                }}
            }} else {{
                // MP4
                video.src = url;
                player = new Plyr(video, {{
                    controls: ['play-large', 'play', 'progress', 'current-time', 'mute', 'settings', 'pip', 'fullscreen'],
                    settings: ['speed'],
                    speed: {{ selected: 1, options: [0.5, 0.75, 1, 1.5, 2] }}
                }});
                
                player.on('ready', () => {{
                    isPlayerReady = true;
                    player.play();
                }});
            }}
        }}
        
        function updateQuality(newQuality) {{
            if (!hls) return;
            
            if (newQuality === 0) {{
                hls.currentLevel = -1;
            }} else {{
                hls.levels.forEach((level, index) => {{
                    if (level.height === newQuality) {{
                        hls.currentLevel = index;
                    }}
                }});
            }}
        }}
        
        // Accordion
        document.querySelectorAll('.accordion-header').forEach(btn => {{
            btn.addEventListener('click', () => {{
                btn.classList.toggle('active');
                const content = btn.nextElementSibling;
                content.style.maxHeight = content.style.maxHeight ? null : content.scrollHeight + 'px';
            }});
        }});
        
        // Search
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
</html>"""
