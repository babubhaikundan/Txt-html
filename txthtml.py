import os
import re
import html

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
    # UPDATED: We now assign a topic even in the default case if possible.
    topic = extract_topic(name)
    return "General", topic, name

def extract_topic(title):
    """
    Extract topic name from title by removing numbering patterns like #1, #2, etc.
    Returns base topic name without numbers.
    """
    # Remove patterns like #1, #2, #8, etc. at the end
    topic = re.sub(r'\s*#\d+\s*$', '', title).strip()
    # PREVIOUSLY: return topic if topic != title else None
    # UPDATED LOGIC: Always return the base name as the topic.
    # This ensures "Lecture 1" and "Lecture" both go into the "Lecture" topic group.
    return topic

def structure_data_in_order(urls):
    """
    Processes URLs with smart grouping by Subject → Topic → Lectures
    """
    structured_list = []
    subject_map = {}
    temp_map = {}
    
    # First pass: Collect all videos and PDFs for each unique name
    for name, url in urls:
        if name not in temp_map:
            temp_map[name] = {"videos": [], "pdfs": []}
        if ".pdf" in url.lower():
            temp_map[name]["pdfs"].append(url)
        else:
            temp_map[name]["videos"].append(url)
    
    # Second pass: Parse and organize by Subject → Topic → Lecture
    processed_names = set()
    for name, _ in urls:
        if name in processed_names:
            continue
        
        subject, topic, title = parse_line(name)
        
        # Create subject if doesn't exist
        if subject not in subject_map:
            new_subject = {
                "name": subject,
                "topics": {}  # Topics will be organized here
            }
            subject_map[subject] = new_subject
            structured_list.append(new_subject)
        
        current_subject = subject_map[subject]
        
        # If there's a topic, group under it
        # With the new logic, 'topic' should always exist.
        if topic:
            if topic not in current_subject["topics"]:
                current_subject["topics"][topic] = {
                    "name": topic,
                    "lectures": []
                }
            
            current_subject["topics"][topic]["lectures"].append({
                "title": title,
                "videos": temp_map[name]["videos"],
                "pdfs": temp_map[name]["pdfs"]
            })
        else:
            # This 'else' block is now less likely to be used but kept for safety.
            if "direct_lectures" not in current_subject:
                current_subject["direct_lectures"] = []
            
            current_subject["direct_lectures"].append({
                "title": title,
                "videos": temp_map[name]["videos"],
                "pdfs": temp_map[name]["pdfs"]
            })
        
        processed_names.add(name)
    
    return structured_list

def generate_html(file_name, structured_list):
    """
    Generates HTML with nested structure: Subject → Topic → Lectures
    With PROPER quote escaping for onclick attributes
    """
    content_html = ""
    if not structured_list:
        content_html = "<p class='text-center text-white'>No content found.</p>"
    else:
        for subject_data in structured_list:
            subject_name = subject_data["name"]
            
            # Build subject content
            subject_content = ""
            
            # First add direct lectures (without topic grouping)
            if "direct_lectures" in subject_data and subject_data["direct_lectures"]:
                for lecture in subject_data["direct_lectures"]:
                    title, videos, pdfs = lecture["title"], lecture["videos"], lecture["pdfs"]
                    
                    # PROPER quote escaping using html.escape
                    video_links = "".join(
                        f'<a href="#" class="list-item video-item" onclick="playVideo(event, {html.escape(repr(url), quote=True)}, this)"><i class="fa-solid fa-circle-play"></i> Play</a>'
                        for url in videos
                    )
                    pdf_links = "".join(
                        f'<a href="{html.escape(url, quote=True)}" target="_blank" class="list-item pdf-item"><i class="fa-solid fa-file-pdf"></i> PDF</a>'
                        for url in pdfs
                    )
                    
                    subject_content += f"""
                    <div class="lecture-entry">
                        <p class="lecture-title">{html.escape(title)}</p><div class="lecture-links">{video_links}{pdf_links}</div>
                    </div>"""
            
            # Then add topic-wise lectures
            if "topics" in subject_data and subject_data["topics"]:
                # Sort topics alphabetically for consistent order
                sorted_topics = sorted(subject_data["topics"].items())
                for topic_name, topic_data in sorted_topics:
                    
                    # Build lecture list for this topic
                    lecture_html = ""
                    # Optional: Sort lectures within a topic if needed (e.g., by title)
                    sorted_lectures = sorted(topic_data["lectures"], key=lambda x: x['title'])
                    for lecture in sorted_lectures:
                        title, videos, pdfs = lecture["title"], lecture["videos"], lecture["pdfs"]
                        
                        # PROPER quote escaping
                        video_links = "".join(
                            f'<a href="#" class="list-item video-item" onclick="playVideo(event, {html.escape(repr(url), quote=True)}, this)"><i class="fa-solid fa-circle-play"></i> Play</a>'
                            for url in videos
                        )
                        pdf_links = "".join(
                            f'<a href="{html.escape(url, quote=True)}" target="_blank" class="list-item pdf-item"><i class="fa-solid fa-file-pdf"></i> PDF</a>'
                            for url in pdfs
                        )
                        
                        lecture_html += f"""
                        <div class="lecture-entry">
                            <p class="lecture-title">{html.escape(title)}</p><div class="lecture-links">{video_links}{pdf_links}</div>
                        </div>"""
                    
                    # Add topic as nested accordion
                    subject_content += f"""
                    <div class="topic-accordion">
                        <button class="topic-header">📁 {html.escape(topic_name)}</button>
                        <div class="topic-content">{lecture_html}</div>
                    </div>"""
            
            # Add subject accordion
            content_html += f"""
            <div class="accordion-item">
                <button class="accordion-header">{html.escape(subject_name)}</button>
                <div class="accordion-content">{subject_content}</div>
            </div>"""
    
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
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{html.escape(file_name)}</title>
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
        .topic-accordion {{margin: 10px 0; border-left: 3px solid #00b3ff; padding-left: 10px;}}
        .topic-header {{width: 100%; background: #f8f9fa; border: none; text-align: left; padding: 12px 15px; font-size: 16px; font-weight: 600; cursor: pointer; border-radius: 6px; color: #333; transition: all 0.2s ease;}}
        .topic-header:hover {{background: #e9ecef;}}
        .topic-header.active {{background: #00b3ff; color: white;}}
        .topic-content {{padding: 10px 0; max-height: 0; overflow: hidden; transition: max-height 0.4s ease-out;}}
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
    <div class="header">{html.escape(file_name)}</div>
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
        
        // Accordion (Subject level)
        document.querySelectorAll('.accordion-header').forEach(btn => {{
            btn.addEventListener('click', () => {{
                btn.classList.toggle('active');
                const content = btn.nextElementSibling;
                content.style.maxHeight = content.style.maxHeight ? null : content.scrollHeight + 'px';
            }});
        }});
        
        // Topic Accordion (Nested level)
        document.querySelectorAll('.topic-header').forEach(btn => {{
            btn.addEventListener('click', () => {{
                btn.classList.toggle('active');
                const content = btn.nextElementSibling;
                if (content.style.maxHeight) {{
                    content.style.maxHeight = null;
                }} else {{
                    content.style.maxHeight = content.scrollHeight + 'px';
                    // Also expand parent if collapsed
                    const parentContent = btn.closest('.accordion-content');
                    if (parentContent && !parentContent.style.maxHeight) {{
                        parentContent.style.maxHeight = parentContent.scrollHeight + 'px';
                    }}
                }}
            }});
        }});
        
        // Search
        function filterContent() {{
            const term = document.getElementById('searchInput').value.toLowerCase();
            document.querySelectorAll('.accordion-item').forEach(sub => {{
                let hasMatch = false;
                // Search in direct lectures
                sub.querySelectorAll('.lecture-entry').forEach(lec => {{
                    const match = lec.querySelector('.lecture-title').textContent.toLowerCase().includes(term);
                    lec.style.display = match ? '' : 'none';
                    if(match) hasMatch = true;
                }});
                
                // Search in topics
                sub.querySelectorAll('.topic-accordion').forEach(topic => {{
                    let topicHasMatch = false;
                    topic.querySelectorAll('.lecture-entry').forEach(lec => {{
                         const match = lec.querySelector('.lecture-title').textContent.toLowerCase().includes(term);
                         lec.style.display = match ? '' : 'none';
                         if(match) topicHasMatch = true;
                    }});
                    topic.style.display = topicHasMatch ? '' : 'none';
                    if(topicHasMatch) hasMatch = true;
                }});
                
                sub.style.display = hasMatch ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>"""