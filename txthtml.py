import os
import re

# NOTE: The 'subprocess' and 'CREDIT' imports are no longer needed here as the template is self-contained.

def parse_line(name):
    """
    Parses a line to find the Subject and Title using multiple patterns for flexibility.
    """
    # Pattern 1: (Subject by Teacher) Anything else
    match = re.search(r'^\((.*?)\)', name)
    if match:
        subject = match.group(1).strip()
        # Remove the subject part and clean up the rest for the title
        title = name.replace(match.group(0), '').strip().lstrip('|| ').strip()
        return subject, title

    # Pattern 2: Subject by Teacher || Title
    match = re.search(r'^(.*? (?:by|By) (?:Sir|Mam))\s*\|\|\s*(.*)', name)
    if match:
        return match.group(1).strip(), match.group(2).strip()

    # Pattern 3 (Fallback): Anything before || is the subject/topic
    if '||' in name:
        parts = name.split('||', 1)
        # If the part before || is short and looks like a lecture number, ignore it
        if len(parts[0].strip()) < 15:
             return parts[0].strip(), parts[1].strip()
        return parts[0].strip(), parts[1].strip()
        
    # Final fallback if no recognizable patterns are found
    return "Miscellaneous", name

def structure_data_in_order(urls):
    """
    Processes a list of (name, url) tuples, maintaining the original order,
    grouping lectures under subjects, and linking related videos and PDFs.
    """
    structured_list = []
    subject_map = {}
    
    # First, pre-process all URLs to group videos and PDFs by their exact name
    temp_map = {}
    for name, url in urls:
        if name not in temp_map:
            temp_map[name] = {"videos": [], "pdfs": []}
        
        if ".pdf" in url.lower():
            temp_map[name]["pdfs"].append(url)
        else:  # Assume anything not a PDF is a video
            temp_map[name]["videos"].append(url)
            
    # Now, iterate through the original list to maintain order
    processed_names = set()
    for name, _ in urls:
        if name in processed_names:
            continue
        
        subject, title = parse_line(name)
        lecture_data = temp_map[name]

        # If this is a new subject, create an entry for it
        if subject not in subject_map:
            new_subject_group = {"name": subject, "lectures": []}
            subject_map[subject] = new_subject_group
            structured_list.append(new_subject_group)
            
        # Add the lecture to the correct subject group
        subject_map[subject]["lectures"].append({
            "title": title,
            "videos": lecture_data["videos"],
            "pdfs": lecture_data["pdfs"]
        })
        processed_names.add(name)
        
    return structured_list

def generate_html(file_name, structured_list):
    """
    Generates the final HTML by populating the user-provided template with dynamic content.
    """
    
    # --- Part 1: Generate the dynamic HTML for the lecture list (accordion) ---
    content_html = ""
    if not structured_list:
        content_html = "<p class='text-center text-white'>No content found to display.</p>"
    else:
        for subject_data in structured_list:
            subject_name = subject_data["name"]
            lectures = subject_data["lectures"]
            
            lecture_html = ""
            for lecture in lectures:
                title = lecture["title"]
                # Create a link for each video, with the onclick event
                video_links = "".join(f'<button class="btn btn-primary btn-sm m-1" onclick="playVideo(event, \'{url}\')"><i class="bi bi-play-circle"></i> Play Video</button>' for url in lecture["videos"])
                # Create a link for each PDF
                pdf_links = "".join(f'<a href="{url}" target="_blank" class="btn btn-danger btn-sm m-1"><i class="bi bi-file-earmark-pdf"></i> View PDF</a>' for url in lecture["pdfs"])
                
                lecture_html += f"""
                <div class="list-group-item bg-dark text-light border-secondary">
                    <div class="d-flex w-100 justify-content-between">
                        <h6 class="mb-1">{title}</h6>
                    </div>
                    <div class="d-flex mt-2">
                        {video_links}{pdf_links}
                    </div>
                </div>
                """
            
            content_html += f"""
            <div class="accordion-item bg-dark">
                <h2 class="accordion-header" id="heading-{subject_name.replace(' ', '')}">
                    <button class="accordion-button bg-dark text-white collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapse-{subject_name.replace(' ', '')}">
                        {subject_name}
                    </button>
                </h2>
                <div id="collapse-{subject_name.replace(' ', '')}" class="accordion-collapse collapse" data-bs-parent="#lectureAccordion">
                    <div class="accordion-body p-0">
                        <div class="list-group">
                            {lecture_html}
                        </div>
                    </div>
                </div>
            </div>
            """

    # --- Part 2: The Base HTML Template (from your req.html) ---
    # NOTE: The player script is now inside the template for better organization.
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <link rel="shortcut icon" href="https://s.tfrbot.com/h/gL5VTi" type="image/x-icon">
    <meta property="og:image" content="https://s.tfrbot.com/h/gL5VTi" itemprop="thumbnailUrl">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>{{file_name}} | Babu Bhai Kundan</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.plyr.io/3.7.8/plyr.css" />
    <style>
        body { background-color: #121212; color: #e0e0e0; }
        .accordion-button:not(.collapsed) { background-color: #343a40; }
        .accordion-button:focus { box-shadow: none; }
    </style>
</head>
<body class="bg-black">
    <header>
        <nav class="navbar bg-dark p-lg-3 p-2">
            <div class="container-fluid">
                 <h4 class="navbar-brand text-light fw-bold">BabuBhaiKundan Player</h4>
            </div>
        </nav>
    </header>

    <div class="container-fluid mt-3">
        <h5 class="text-center p-2 flex-wrap text-center">{{file_name}}</h5>
        
        <div class="row justify-content-center">
            <div class="col-lg-10">
                <video id="player" playsinline controls></video>
            </div>
        </div>

        <div class="row justify-content-center mt-4">
            <div class="col-lg-10">
                <div class="accordion" id="lectureAccordion">
                    {{LECTURE_CONTENT}}
                </div>
            </div>
        </div>
    </div>
    
    <footer class="bg-dark text-center text-white mt-4">
        <div class="text-center p-3" style="background-color: rgba(0, 0, 0, 0.2);">
            © <script>document.write(new Date().getFullYear())</script> Copyright:
            <a class="text-white" href="https://telegram.me/kundan_yadav_bot">𝕂𝕦𝕟𝕕𝕒𝕟 𝕐𝕒𝕕𝕒𝕧 😎</a>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.plyr.io/3.7.8/plyr.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const video = document.getElementById('player');
            const player = new Plyr(video, {
                captions: { active: true, update: true, language: 'en' },
                controls: [ 'play-large', 'play', 'progress', 'current-time', 'mute', 'volume', 'captions', 'settings', 'pip', 'airplay', 'fullscreen' ],
                settings: ['captions', 'quality', 'speed', 'loop'],
                speed: { selected: 1, options: [0.5, 0.75, 1, 1.25, 1.5, 2] },
            });
            window.player = player;
            window.hls = new Hls();

            // Double tap to seek functionality
            const container = player.elements.container;
            let lastTap = 0;
            container.addEventListener('touchend', (event) => {
                const now = new Date().getTime();
                if ((now - lastTap) < 300) {
                    const rect = container.getBoundingClientRect();
                    const tapX = event.changedTouches[0].clientX - rect.left;
                    player.forward(tapX > rect.width / 2 ? 10 : -10);
                }
                lastTap = now;
            });
        });

        function playVideo(event, url) {
            event.preventDefault(); // <-- FIXES THE PAGE JUMPING ISSUE
            
            const video = document.getElementById('player');
            if (url.includes('.m3u8')) {
                if (Hls.isSupported()) {
                    window.hls.loadSource(url);
                    window.hls.attachMedia(video);
                    window.player.play();
                } else {
                    alert('HLS is not supported in your browser.');
                }
            } else {
                // For non-m3u8 files like MP4
                video.src = url;
                window.player.play();
            }
        }
    </script>
</body>
</html>
"""
    # --- Part 3: Replace placeholders in the template with dynamic content ---
    final_html = HTML_TEMPLATE.replace("{{file_name}}", file_name)
    final_html = final_html.replace("{{LECTURE_CONTENT}}", content_html)
    
    return final_html