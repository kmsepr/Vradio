import subprocess
import time
import os
import json
import feedparser
from flask import Flask, Response, request, redirect

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

def get_podcast_title(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        return feed.feed.get('title', feed_url.split('//')[-1].split('/')[0])
    except:
        return feed_url.split('//')[-1].split('/')[0]

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

# 🎙️ Enhanced Podcast routes
@app.route("/podcast")
def podcast():
    rss_url = request.args.get("url")
    action = request.args.get("action")
    saved_podcasts = load_podcasts()

    # Handle remove action
    if action == "remove" and rss_url:
        if rss_url in saved_podcasts:
            saved_podcasts.remove(rss_url)
            save_podcasts(saved_podcasts)
        return redirect("/podcast")

    if not rss_url:
        # Show podcast interface
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Podcasts</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ 
                    font-family: sans-serif; 
                    background: #1e1e2f; 
                    color: white; 
                    padding: 15px;
                    margin: 0;
                }}
                .container {{ 
                    max-width: 800px; 
                    margin: 0 auto;
                }}
                h2 {{ 
                    color: #4CAF50;
                    margin-top: 0;
                }}
                .podcast-list {{ 
                    list-style: none;
                    padding: 0;
                }}
                .podcast-item {{
                    background: #2b2b3c;
                    padding: 15px;
                    margin-bottom: 10px;
                    border-radius: 8px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .podcast-info {{
                    flex-grow: 1;
                }}
                .podcast-title {{
                    margin: 0;
                    color: #4CAF50;
                }}
                .podcast-url {{
                    color: #aaa;
                    font-size: 0.8rem;
                    margin: 5px 0 0 0;
                }}
                .podcast-actions {{
                    display: flex;
                    gap: 10px;
                }}
                .podcast-button {{
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 5px 10px;
                    cursor: pointer;
                    text-decoration: none;
                    font-size: 0.9rem;
                }}
                .remove-button {{
                    background: #f44336;
                }}
                .add-form {{
                    background: #2b2b3c;
                    padding: 15px;
                    border-radius: 8px;
                    margin-top: 20px;
                }}
                .add-form input {{
                    width: 100%;
                    padding: 10px;
                    margin-bottom: 10px;
                    border-radius: 4px;
                    border: none;
                    background: #1e1e2f;
                    color: white;
                }}
                .add-form input[type="submit"] {{
                    background: #4CAF50;
                    cursor: pointer;
                }}
            </style>
            <script>
                function confirmRemove(url) {{
                    if (confirm("Are you sure you want to remove this podcast?")) {{
                        window.location.href = `/podcast?url=${{url}}&action=remove`;
                    }}
                }}
            </script>
        </head>
        <body>
            <div class="container">
                <h2>🎧 My Podcasts</h2>
                
                <ul class="podcast-list">
                    {"".join(
                        f'''
                        <li class="podcast-item">
                            <div class="podcast-info">
                                <h3 class="podcast-title">{get_podcast_title(feed)}</h3>
                                <p class="podcast-url">{feed}</p>
                            </div>
                            <div class="podcast-actions">
                                <a href="/podcast?url={feed}" class="podcast-button">View</a>
                                <button onclick="confirmRemove('{feed}')" class="podcast-button remove-button">Remove</button>
                            </div>
                        </li>
                        '''
                        for feed in saved_podcasts
                    ) if saved_podcasts else "<p>No podcasts saved yet</p>"}
                </ul>
                
                <div class="add-form">
                    <h3>Add New Podcast</h3>
                    <form method="get" action="/podcast">
                        <input type="text" name="url" placeholder="Enter podcast RSS feed URL" required>
                        <input type="submit" value="Add Podcast">
                    </form>
                </div>
            </div>
        </body>
        </html>
        """

    # Parse and display podcast feed
    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            return "⚠️ Invalid or empty podcast feed."

        # Add to saved podcasts if not already there
        if rss_url not in saved_podcasts:
            saved_podcasts.append(rss_url)
            save_podcasts(saved_podcasts)

        # Sort episodes by date (newest first)
        episodes = sorted(
            feed.entries,
            key=lambda x: x.get('published_parsed', (0, 0, 0)),
            reverse=True
        )

        episodes_html = ""
        for entry in episodes[:50]:  # Show up to 50 episodes
            audio_url = next((link.href for link in entry.enclosures if link.type.startswith('audio')), None)
            if audio_url:
                date = entry.get('published', '')
                if hasattr(entry, 'published_parsed'):
                    try:
                        date = time.strftime('%Y-%m-%d', entry.published_parsed)
                    except:
                        pass
                
                episodes_html += f"""
                <div class="episode">
                    <h3>{entry.title}</h3>
                    <p><small>{date}</small></p>
                    <p>{entry.get('description', '')[:200]}...</p>
                    <audio controls preload="none">
                        <source src="{audio_url}" type="audio/mpeg">
                    </audio>
                    <hr>
                </div>
                """

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{feed.feed.title}</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{
                    font-family: sans-serif;
                    background: #1e1e2f;
                    color: white;
                    padding: 15px;
                    margin: 0;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                }}
                h2 {{
                    color: #4CAF50;
                    margin-top: 0;
                }}
                .episode {{
                    background: #2b2b3c;
                    padding: 15px;
                    margin-bottom: 15px;
                    border-radius: 8px;
                }}
                audio {{
                    width: 100%;
                    margin-top: 10px;
                }}
                hr {{
                    border: none;
                    border-top: 1px solid #444;
                    margin: 15px 0;
                }}
                .back-link {{
                    display: inline-block;
                    margin-top: 20px;
                    color: #4CAF50;
                    text-decoration: none;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>{feed.feed.title}</h2>
                <p>{feed.feed.get('description', '')}</p>
                
                {episodes_html if episodes_html else "<p>No episodes found</p>"}
                
                <a href="/podcast" class="back-link">← Back to Podcasts</a>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        return f"⚠️ Error loading podcast: {str(e)}"

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
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)