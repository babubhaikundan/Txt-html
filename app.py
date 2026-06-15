from flask import Flask
app = Flask(__name__)

@app.route('/')
def hello_world():
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Txt to Html Bot</title>

    <!-- Mobile first -->
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

    <!-- SEO / Preview -->
    <meta name="description" content="Telegram File Stream Bot by Kundan Yadav. Stream videos directly from Telegram with resume support.">
    <meta property="og:title" content="BBK File Stream Bot">
    <meta property="og:description" content="Fast, secure Telegram file streaming with resume playback.">
    <meta property="og:image" content="https://babubhaikundan.pages.dev/Assets/logo/bbk.png">

    <!-- Minimal CSS -->
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        body {
            background: radial-gradient(circle at top, #1a1a2e, #000);
            color: #fff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 16px;
        }

        .card {
            max-width: 420px;
            width: 100%;
            background: rgba(255, 255, 255, 0.06);
            backdrop-filter: blur(10px);
            border-radius: 14px;
            padding: 24px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.6);
        }

        .logo {
            width: 90px;
            height: 90px;
            border-radius: 50%;
            margin: 0 auto 16px;
            box-shadow: 0 0 25px rgba(233, 30, 140, 0.6);
        }

        h1 {
            font-size: 1.4rem;
            margin-bottom: 8px;
            letter-spacing: 0.5px;
        }

        p {
            font-size: 0.95rem;
            opacity: 0.85;
            line-height: 1.5;
            margin-bottom: 18px;
        }

        .status {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.8rem;
            background: linear-gradient(90deg, #00c853, #64dd17);
            color: #000;
            font-weight: 600;
            margin-bottom: 18px;
        }

        .btn {
            display: block;
            text-decoration: none;
            margin-top: 10px;
            padding: 12px;
            border-radius: 10px;
            font-weight: 600;
            background: linear-gradient(135deg, #e91e63, #9c27b0);
            color: #fff;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(233,30,140,0.6);
        }

        .footer {
            margin-top: 20px;
            font-size: 0.75rem;
            opacity: 0.5;
        }
    </style>
</head>

<body>

    <div class="card">
        <img 
            src="https://babubhaikundan.pages.dev/Assets/logo/bbk.png"
            alt="BBK Logo"
            class="logo"
        >

        <h1>Txt to Html Bot</h1>

        <div class="status">● ONLINE</div>

        <p>
            Stream Telegram files directly in your browser with resume playback,
            fast byte-range streaming and modern video player support.
        </p>

        <a href="https://t.me/k_txt_to_html_bot" class="btn">
            Open Telegram Bot
        </a>

        <a href="https://t.me/babubhaikundan" class="btn" style="background: linear-gradient(135deg,#2196f3,#03a9f4);">
            Join Updates Channel
        </a>

        <div class="footer">
            © <script>document.write(new Date().getFullYear())</script>
            Kundan Yadav • All rights reserved
        </div>
    </div>

</body>
</html>
"""


if __name__ == "__main__":
    app.run()
