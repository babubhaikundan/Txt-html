import os
import re

def extract_names_and_urls(file_content):
    """
    Extracts (name, url) pairs from the raw text content. This function is required by main.py.
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
    Smarter parsing to identify subject and title from various formats.
    """
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

    # Pattern 3 (Fallback): Anything before || is the subject/topic
    if '||' in name:
        parts = name.split('||', 1)
        return parts[0].strip(), parts[1].strip()
        
    # Final fallback
    return "Miscellaneous", name

def structure_data_in_order(urls):
    """
    Processes URLs sequentially to maintain their original order and groups them by subject.
    Links PDFs and videos of the same lecture together.
    """
    structured_list = []
    subject_map = {}
    
    temp_map = {}
    for name, url in urls:
        if name not in temp_map:
            temp_map[name] = {"videos": [], "pdfs": []}
        if ".pdf" in url.lower():
            temp_map[name]["pdfs"].append(url)
        else:
            temp_map[name]["videos"].append(url)
            
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
    """
    Generates the final HTML with the good design and the powerful new player features.
    """
    content_html = ""
    if not structured_list:
        content_html = "<p class='text-center'>No content found to display.</p>"
    else:
        # Create a unique ID for each accordion item to prevent conflicts
        item_id_counter = 0
        for subject_data in structured_list:
            subject_name = subject_data["name"]
            lectures = subject_data["lectures"]
            
            lecture_html = ""
            for lecture in lectures:
                title = lecture["title"]
                video_links = "".join(f'<a href="#" class="list-item video-item" onclick="playVideo(event, \'{url}\', this)"><i class="fa-solid fa-circle-play"></i> Play Video</a>' for url in lecture["videos"])
                pdf_links = "".join(f'<a href="{url}" target="_blank" class="list-item pdf-item"><i class="fa-solid fa-file-pdf"></i> View PDF</a>' for url in lecture["pdfs"])
                
                lecture_html += f"""
                <div class="lecture-entry">
                    <p class="lecture-title">{title}</p>
                    <div class="lecture-links">{video_links}{pdf_links}</div>
                </div>
                """
            
            item_id = f"item{item_id_counter}"
            content_html += f"""
            <div class="accordion-item">
                <button class="accordion-header">{subject_name}</button>
                <div class="accordion-content">{lecture_html}</div>
            </div>
            """
            item_id_counter += 1

    new_footer = f"""
    <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd;">
        <a href="https://babubhaikundan.blogspot.com" target="_blank" style="display: inline-flex; align-items: center; gap: 8px; background: #222; padding: 8px 16px; border-radius: 20px; text-decoration: none; box-shadow: 0 4px 10px rgba(0,0,0,0.2);">
            <img src="https://upload.wikimedia.org/wikipedia/commons/8/82/Telegram_logo.svg" alt="Telegram" style="width: 20px; height: 20px;">
            <span style="color: #00ffc8; font-weight: bold; font-size: 15px;">Developer💀:-</span>
            <span style="display: flex; align-items: center; gap: 5px; color: #FFD700; font-size: 15px; font-weight: bold;">
                𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧 <img src="https://s.tfrbot.com/h/gL5VTi" alt="Kundan" style="width: 22px; height: 22px; border-radius: 50%;">
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
    <title>{file_name}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/animate.css/4.1.1/animate.min.css"/>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <script src="https://cdn.tailwindcss.com"></script>
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
        .lecture-entry {{ padding: 15px 0; border-bottom: 1px solid #f0f0f0; }} .lecture-entry:last-child {{ border-bottom: none; }}
        .lecture-title {{ font-weight: 600; margin-bottom: 12px; color: #333; }}
        .lecture-links {{ display: flex; flex-wrap: wrap; gap: 10px; }}
        .list-item {{ display: inline-flex; align-items: center; gap: 8px; padding: 8px 15px; border-radius: 20px; text-decoration: none; font-weight: 500; transition: all 0.2s ease; }}
        .video-item {{ background-color: #e9f5ff; color: #0056b3; border: 1px solid #b3d7ff; }}
        .video-item.playing, .video-item:hover {{ background-color: #007bff; color: white; border-color: #007bff; transform: translateY(-2px); }}
        .pdf-item {{ background-color: #fff0e9; color: #d84315; border: 1px solid #ffd0b3; }}
        .pdf-item:hover {{ background-color: #ff5722; color: white; border-color: #ff5722; }}
        
        /* Plyr.js Custom Styles */
        .plyr {{ border-radius: 8px; overflow: hidden; }}
        .plyr__video-wrapper {{ background: #000; }}
        .plyr__control--overlaid {{ background: rgba(0, 0, 0, 0.7); }}
        .plyr__progress__buffer {{ color: rgba(255, 255, 255, 0.25); }}
        .plyr--full-ui input[type=range] {{ color: #007bff; }}
        .plyr__menu__container {{ background: rgba(28, 28, 28, 0.9); backdrop-filter: blur(10px); }}
        
        /* Network Status Indicator */
        .network-indicator {{ position: absolute; top: 10px; right: 10px; background: rgba(0, 0, 0, 0.5); color: white; padding: 5px 10px; border-radius: 5px; font-size: 12px; z-index: 10; }}
        .network-indicator.good {{ background: rgba(0, 128, 0, 0.7); }}
        .network-indicator.medium {{ background: rgba(255, 165, 0, 0.7); }}
        .network-indicator.poor {{ background: rgba(255, 0, 0, 0.7); }}
        
        /* Loading Animation */
        .custom-loading {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 50px; height: 50px; border: 5px solid rgba(255, 255, 255, 0.3); border-radius: 50%; border-top-color: #007bff; animation: spin 1s ease-in-out infinite; z-index: 10; display: none; }}
        @keyframes spin {{ to {{ transform: translate(-50%, -50%) rotate(360deg); }} }}
        
        /* Video Type Indicator */
        .video-type-indicator {{ position: absolute; top: 10px; left: 10px; background: rgba(0, 0, 0, 0.5); color: white; padding: 5px 10px; border-radius: 5px; font-size: 12px; z-index: 10; }}
        .video-type-indicator.hls {{ background: rgba(255, 99, 71, 0.7); }}
        .video-type-indicator.mp4 {{ background: rgba(30, 144, 255, 0.7); }}
    </style>
</head>
<body>
    <div class="header">{file_name}</div>
    <div class="main-container">
        <div class="player-wrapper">
            <div class="network-indicator" id="networkIndicator">Checking connection...</div>
            <div class="video-type-indicator" id="videoTypeIndicator" style="display: none;">Video Type</div>
            <div class="custom-loading" id="customLoading"></div>
            <video id="player" class="player" playsinline controls></video>
        </div>
        <div class="search-bar"><input type="text" id="searchInput" placeholder="Search for lectures..." onkeyup="filterContent()"></div>
        <div id="content-container">{content_html}</div>
    </div>
    {new_footer}

    <script src="https://cdnjs.cloudflare.com/ajax/libs/wow/1.1.2/wow.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script>
        // Initialize WOW library for animations
        new WOW().init();
        
        // Network Quality Detection
        let networkQuality = 'good';
        let connectionSpeed = 0;
        
        function detectNetworkQuality() {{
            const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
            const networkIndicator = document.getElementById('networkIndicator');
            
            if (connection) {{
                connectionSpeed = connection.downlink || 0;
                
                if (connectionSpeed > 5) {{
                    networkQuality = 'good';
                    networkIndicator.textContent = 'Good Connection';
                    networkIndicator.className = 'network-indicator good';
                }} else if (connectionSpeed > 1.5) {{
                    networkQuality = 'medium';
                    networkIndicator.textContent = 'Medium Connection';
                    networkIndicator.className = 'network-indicator medium';
                }} else {{
                    networkQuality = 'poor';
                    networkIndicator.textContent = 'Slow Connection';
                    networkIndicator.className = 'network-indicator poor';
                }}
            }} else {{
                // Fallback: Use a simple bandwidth test
                const img = new Image();
                const startTime = new Date().getTime();
                img.onload = function() {{
                    const endTime = new Date().getTime();
                    const duration = (endTime - startTime) / 1000;
                    const speed = (img.fileSize / 1048576) / duration; // MBps
                    
                    if (speed > 5) {{
                        networkQuality = 'good';
                        networkIndicator.textContent = 'Good Connection';
                        networkIndicator.className = 'network-indicator good';
                    }} else if (speed > 1.5) {{
                        networkQuality = 'medium';
                        networkIndicator.textContent = 'Medium Connection';
                        networkIndicator.className = 'network-indicator medium';
                    }} else {{
                        networkQuality = 'poor';
                        networkIndicator.textContent = 'Slow Connection';
                        networkIndicator.className = 'network-indicator poor';
                    }}
                }};
                img.src = 'https://www.google.com/images/phd/px.gif?' + startTime;
                img.fileSize = 40000; // Approximate file size in bytes
            }}
            
            // Hide the indicator after 3 seconds
            setTimeout(() => {{
                networkIndicator.style.display = 'none';
            }}, 3000);
        }}
        
        // Initialize network quality detection
        detectNetworkQuality();
        
        // Player initialization with Plyr.js
        const player = new Plyr('#player', {{
            controls: [
                'play-large',
                'play',
                'progress',
                'current-time',
                'duration',
                'mute',
                'settings',
                'pip',
                'fullscreen'
            ],
            quality: {{
                default: 720,
                options: [1080, 720, 480, 360, 240],
                forced: true,
            }},
            dblclickFullscreen: false,
        }});
        
        // Store player in window object for global access
        window.player = player;
        
        // Custom loading indicator
        const customLoading = document.getElementById('customLoading');
        const videoTypeIndicator = document.getElementById('videoTypeIndicator');
        
        player.on('ready', (event) => {{
            const instance = event.detail.plyr;
            const container = instance.elements.container;
            let lastTap = 0;
            let isSeeking = false;
            
            // Double-tap to seek functionality
            container.addEventListener('touchend', event => {{
                const currentTime = new Date().getTime();
                const tapLength = currentTime - lastTap;
                
                if (tapLength < 300 && tapLength > 0 && !isSeeking) {{
                    isSeeking = true;
                    event.preventDefault();
                    
                    const containerRect = container.getBoundingClientRect();
                    const touchX = event.changedTouches[0].clientX;
                    const midpoint = containerRect.left + (containerRect.width / 2);
                    
                    if (touchX < midpoint) {{
                        instance.rewind(7);
                    }} else {{
                        instance.forward(7);
                    }}
                    
                    setTimeout(() => {{ isSeeking = false; }}, 300);
                }}
                lastTap = currentTime;
            }});
            
            // Auto-rotate to landscape when entering fullscreen
            instance.on('enterfullscreen', () => {{
                try {{
                    if (screen.orientation && typeof screen.orientation.lock === 'function') {{
                        screen.orientation.lock('landscape');
                    }}
                }} catch (e) {{ /* Ignore errors */ }}
            }});
            
            // Unlock screen orientation when exiting fullscreen
            instance.on('exitfullscreen', () => {{
                try {{
                    if (screen.orientation && typeof screen.orientation.unlock === 'function') {{
                        screen.orientation.unlock();
                    }}
                }} catch (e) {{ /* Ignore errors */ }}
            }});
        }});
        
        // Show loading indicator when loading video
        player.on('waiting', () => {{
            customLoading.style.display = 'block';
        }});
        
        player.on('playing', () => {{
            customLoading.style.display = 'none';
        }});
        
        // Auto quality selection based on network
        player.on('ready', () => {{
            if (networkQuality === 'good') {{
                player.quality = 1080;
            }} else if (networkQuality === 'medium') {{
                player.quality = 720;
            }} else {{
                player.quality = 480;
            }}
        }});
        
        let currentlyPlaying = null;
        function playVideo(event, url, element) {{
            event.preventDefault();
            
            // Show loading indicator
            customLoading.style.display = 'block';
            
            // Detect network quality before playing
            detectNetworkQuality();
            
            // Update the playing indicator
            if(currentlyPlaying) currentlyPlaying.classList.remove('playing');
            element.classList.add('playing');
            currentlyPlaying = element;
            
            // Check if the URL is an HLS stream
            const isHls = url.toLowerCase().includes('.m3u8');
            
            // Show video type indicator
            videoTypeIndicator.textContent = isHls ? 'HLS Stream' : 'MP4 Video';
            videoTypeIndicator.className = isHls ? 'video-type-indicator hls' : 'video-type-indicator mp4';
            videoTypeIndicator.style.display = 'block';
            
            // Hide the indicator after 3 seconds
            setTimeout(() => {{
                videoTypeIndicator.style.display = 'none';
            }}, 3000);
            
            if (isHls) {{
                // Handle HLS streams
                if (Hls.isSupported()) {{
                    const hls = new Hls();
                    hls.loadSource(url);
                    hls.attachMedia(player.media);
                    
                    // Auto-select quality based on network
                    hls.on(Hls.Events.MANIFEST_PARSED, function(event, data) {{
                        if (networkQuality === 'good') {{
                            // Select highest quality
                            hls.currentLevel = hls.levels.length - 1;
                        }} else if (networkQuality === 'medium') {{
                            // Select medium quality
                            hls.currentLevel = Math.floor(hls.levels.length / 2);
                        }} else {{
                            // Select lowest quality
                            hls.currentLevel = 0;
                        }}
                    }});
                    
                    hls.on(Hls.Events.ERROR, function(event, data) {{
                        if (data.fatal) {{
                            switch(data.type) {{
                                case Hls.ErrorTypes.NETWORK_ERROR:
                                    // Try to recover network error
                                    hls.startLoad();
                                    break;
                                case Hls.ErrorTypes.MEDIA_ERROR:
                                    // Try to recover media error
                                    hls.recoverMediaError();
                                    break;
                                default:
                                    // Cannot recover
                                    hls.destroy();
                                    break;
                            }}
                        }}
                    }});
                }} else if (player.media.canPlayType('application/vnd.apple.mpegurl')) {{
                    // For Safari, which has native HLS support
                    player.source = {{
                        type: 'video',
                        sources: [
                            {{ src: url, type: 'application/vnd.apple.mpegurl' }}
                        ]
                    }};
                }} else {{
                    // HLS is not supported
                    alert('HLS is not supported in your browser');
                    customLoading.style.display = 'none';
                    return;
                }}
            }} else {{
                // Handle MP4 videos
                player.source = {{
                    type: 'video',
                    sources: [
                        {{ src: url, type: 'video/mp4', size: 1080 }},
                        {{ src: url, type: 'video/mp4', size: 720 }},
                        {{ src: url, type: 'video/mp4', size: 480 }},
                        {{ src: url, type: 'video/mp4', size: 360 }},
                        {{ src: url, type: 'video/mp4', size: 240 }},
                    ]
                }};
                
                // Auto-select quality based on network
                if (networkQuality === 'good') {{
                    player.quality = 1080;
                }} else if (networkQuality === 'medium') {{
                    player.quality = 720;
                }} else {{
                    player.quality = 480;
                }}
            }}
            
            // Play the video
            player.play();
        }}

        // Accordion and Search script
        document.querySelectorAll('.accordion-header').forEach(btn => btn.addEventListener('click', () => {{
            btn.classList.toggle('active'); const content = btn.nextElementSibling;
            content.style.maxHeight = content.style.maxHeight ? null : content.scrollHeight + 'px';
        }}));

        function filterContent() {{
            const term = document.getElementById('searchInput').value.toLowerCase();
            document.querySelectorAll('.accordion-item').forEach(sub => {{
                let hasMatch = false;
                sub.querySelectorAll('.lecture-entry').forEach(lec => {{
                    const match = lec.querySelector('.lecture-title').textContent.toLowerCase().includes(term);
                    lec.style.display = match ? '' : 'none'; if(match) hasMatch = true;
                }});
                sub.style.display = hasMatch ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>
"""
