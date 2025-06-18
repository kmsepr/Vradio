import subprocess
import time
from flask import Flask, Response, send_from_directory
from flask import request, redirect
import os
import json
import feedparser

app = Flask(__name__)

# 📡 List of radio stations
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL",
    # ... (all your existing radio stations)
}

# 📻 Podcast configuration
PODCASTS_FILE = "podcasts.json"

def load_podcasts():
    if os.path.exists(PODCASTS_FILE):
        with open(PODCASTS_FILE, "r") as f:
            return json.load(f)
    return []

def save_podcasts(feeds):
    with open(PODCASTS_FILE, "w") as f:
        json.dump(feeds, f)

# 🔁 FFmpeg stream generator
def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()
        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10", "-fflags", "nobuffer", "-flags", "low_delay",
                "-i", url, "-vn", "-ac", "1", "-b:a", "64k", "-buffer_size", "1024k", "-f", "mp3", "-"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )
        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            process.kill()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")
        print("🔄 FFmpeg stopped, restarting stream...")
        time.sleep(5)

# 🎧 Stream a radio station
@app.route("/<station_name>")
def stream(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

# ➕ Add new station
@app.route("/add", methods=["POST"])
def add_station():
    name = request.form.get("name", "").strip().lower().replace(" ", "_")
    url = request.form.get("url", "").strip()
    if name and url:
        RADIO_STATIONS[name] = url
    return redirect("/")

# 🎙️ Podcast routes
@app.route("/podcast")
def podcast():
    rss_url = request.args.get("url")
    saved_podcasts = load_podcasts()

    if not rss_url:
        # Show podcast interface
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Podcasts</title>
            <style>
                body {{ font-family: sans-serif; background: #1e1e2f; color: white; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                h2 {{ color: #4CAF50; }}
                form {{ background: #2b2b3c; padding: 20px; border-radius: 8px; }}
                input[type="text"] {{ width: 70%; padding: 10px; border-radius: 4px; border: none; }}
                input[type="submit"] {{ padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }}
                ul {{ list-style: none; padding: 0; }}
                li {{ padding: 10px; border-bottom: 1px solid #444; }}
                li a {{ color: #4CAF50; text-decoration: none; }}
                .podcast-item {{ margin-bottom: 20px; }}
                audio {{ width: 100%; margin-top: 10px; }}
                .back-link {{ display: inline-block; margin-top: 20px; color: #4CAF50; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>🎧 Podcasts</h2>
                <form method="get">
                    <input type="text" name="url" placeholder="Enter podcast RSS feed URL" required>
                    <input type="submit" value="Load Podcast">
                </form>
                
                <h3>⭐ Saved Podcasts</h3>
                <ul>
                    {"".join(f'<li><a href="/podcast?url={feed}">{feed}</a></li>' for feed in saved_podcasts)}
                </ul>
            </div>
        </body>
        </html>
        """
    
    # Parse and display podcast feed
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        return "⚠️ Invalid or empty podcast feed."

    # Add to saved podcasts if not already there
    if rss_url not in saved_podcasts:
        saved_podcasts.append(rss_url)
        save_podcasts(saved_podcasts)

    episodes_html = ""
    for entry in feed.entries[:15]:  # Limit to 15 most recent episodes
        audio_url = next((link.href for link in entry.enclosures if link.type.startswith('audio')), None)
        if audio_url:
            episodes_html += f"""
            <div class="podcast-item">
                <h3>{entry.title}</h3>
                <p>{entry.get('description', 'No description available')}</p>
                <audio controls>
                    <source src="{audio_url}" type="audio/mpeg">
                    Your browser does not support the audio element.
                </audio>
                <p><small>{entry.get('published', '')}</small></p>
            </div>
            """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{feed.feed.title}</title>
        <style>
            body {{ font-family: sans-serif; background: #1e1e2f; color: white; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            h2 {{ color: #4CAF50; }}
            .podcast-item {{ margin-bottom: 30px; padding: 15px; background: #2b2b3c; border-radius: 8px; }}
            audio {{ width: 100%; margin-top: 10px; }}
            .back-link {{ display: inline-block; margin-top: 20px; color: #4CAF50; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>{feed.feed.title}</h2>
            <p>{feed.feed.get('description', '')}</p>
            
            {episodes_html}
            
            <a href="/podcast" class="back-link">← Back to Podcasts</a>
        </div>
    </body>
    </html>
    """

# 🏠 Homepage UI
@app.route("/")
def index():
    def pastel_color(i):
        r = (100 + (i * 40)) % 256
        g = (150 + (i * 60)) % 256
        b = (200 + (i * 80)) % 256
        return f"{r}, {g}, {b}"

    links_html = "".join(
    f"""
    <div class='card' data-name='{name}' style='background-color: rgba({pastel_color(i)}, 0.85);'>
        <a href='/{name}' target='_blank' rel='noopener noreferrer'>{name}</a>
        <button class="fav-btn" onclick="toggleFavourite('{name}')">⭐</button>
    </div>
    """ for i, name in enumerate(reversed(list(RADIO_STATIONS)))
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Radio Favourites</title>
        <style>
            body {{
                font-family: sans-serif;
                background: #1e1e2f;
                color: white;
                margin: 0;
                padding: 0;
            }}
            .header {{
                display: flex;
                align-items: center;
                background: #2b2b3c;
                padding: 10px;
            }}
            .menu-icon {{
                font-size: 1.5rem;
                cursor: pointer;
                margin-right: 10px;
            }}
            .side-menu {{
                position: fixed;
                top: 0;
                left: -220px;
                width: 200px;
                height: 100%;
                background: #2b2b3c;
                padding-top: 60px;
                transition: left 0.3s;
                z-index: 999;
            }}
            .side-menu a {{
                display: block;
                padding: 12px 20px;
                color: white;
                text-decoration: none;
                border-bottom: 1px solid #444;
            }}
            .side-menu a:hover {{
                background-color: #444;
            }}
            h1 {{
                font-size: 1.2rem;
                margin: 0;
            }}
            .scroll-container {{
                max-height: 70vh;
                overflow-y: auto;
                padding: 10px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                gap: 12px;
            }}
            .card {{
                padding: 12px;
                border-radius: 10px;
                text-align: center;
                position: relative;
            }}
            .card a {{
                color: white;
                text-decoration: none;
            }}
            .fav-btn {{
                position: absolute;
                top: 6px;
                right: 10px;
                background: none;
                border: none;
                color: gold;
                font-size: 1.2rem;
                cursor: pointer;
            }}
            .tab-content {{
                display: none;
            }}
            .tab-content.active {{
                display: block;
            }}
            .add-form {{
                max-width: 400px;
                margin: 20px auto;
                display: flex;
                flex-direction: column;
                gap: 10px;
                background: #2a2a3a;
                padding: 15px;
                border-radius: 8px;
            }}
            .add-form input {{
                padding: 10px;
                font-size: 1rem;
                border-radius: 5px;
                border: 1px solid #666;
                background: #1e1e2f;
                color: white;
            }}
            .add-form input[type=submit] {{
                background: #007acc;
                cursor: pointer;
                border: none;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <span class="menu-icon" onclick="toggleMenu()">☰</span>
            <h1>⭐ Favourite Radios</h1>
        </div>

        <div class="side-menu" id="sideMenu">
            <a href="#" onclick="showTab('all'); toggleMenu();">📻 All Stations</a>
            <a href="#" onclick="showTab('add'); toggleMenu();">➕ Add Station</a>
            <a href="/podcast" onclick="toggleMenu();">🎙️ Podcasts</a>
        </div>

        <div id="favTab" class="tab-content active">
            <div class="scroll-container">
                <div class="grid" id="favGrid"></div>
            </div>
        </div>

        <div id="allTab" class="tab-content">
            <div class="scroll-container">
                <div class="grid" id="stationGrid">{links_html}</div>
            </div>
        </div>

        <div id="addTab" class="tab-content">
            <form class="add-form" method="POST" action="/add">
                <input type="text" name="name" placeholder="Station name (no space)" required />
                <input type="text" name="url" placeholder="Stream URL" required />
                <input type="submit" value="Add Station" />
            </form>
        </div>

        <script>
            let activeTab = "fav";

            function toggleFavourite(name) {{
                let favs = JSON.parse(localStorage.getItem("favourites") || "[]");
                if (favs.includes(name)) {{
                    favs = favs.filter(n => n !== name);
                }} else {{
                    favs.push(name);
                }}
                localStorage.setItem("favourites", JSON.stringify(favs));
                updateDisplay();
            }}

            function updateDisplay() {{
                const favs = JSON.parse(localStorage.getItem("favourites") || "[]");
                document.querySelectorAll(".card").forEach(card => {{
                    const name = card.getAttribute("data-name");
                    card.style.display = (activeTab === "all" || (activeTab === "fav" && favs.includes(name))) ? "block" : "none";
                    const btn = card.querySelector(".fav-btn");
                    if (btn) btn.textContent = favs.includes(name) ? "★" : "⭐";
                }});

                const favGrid = document.getElementById("favGrid");
                if (favGrid) {{
                    favGrid.innerHTML = "";
                    favs.forEach(name => {{
                        const el = document.querySelector(`[data-name='${{name}}']`);
                        if (el) favGrid.appendChild(el.cloneNode(true));
                    }});
                }}
            }}

            function showTab(tab) {{
                activeTab = tab;
                document.querySelectorAll(".tab-content").forEach(div => div.classList.remove("active"));
                document.getElementById(tab + "Tab").classList.add("active");
                updateDisplay();
            }}

            function toggleMenu() {{
                const menu = document.getElementById("sideMenu");
                menu.style.left = (menu.style.left === "0px") ? "-220px" : "0px";
            }}

            window.onload = updateDisplay;
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)