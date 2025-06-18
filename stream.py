import subprocess
import time
from flask import Flask, Response, request, redirect
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
        podcast_favs = json.loads(request.cookies.get('podcastFavorites', '[]'))
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Podcasts</title>
            <style>
                body {{ font-family: sans-serif; background: #1e1e2f; color: white; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .tab-container {{ margin-bottom: 20px; }}
                .tab-button {{
                    padding: 10px 15px;
                    background: #2b2b3c;
                    border: none;
                    color: white;
                    cursor: pointer;
                    margin-right: 5px;
                }}
                .tab-button.active {{ background: #4CAF50; }}
                .tab-content {{ display: none; }}
                .tab-content.active {{ display: block; }}
                .podcast-list {{ list-style: none; padding: 0; }}
                .podcast-item {{
                    background: #2b2b3c;
                    padding: 15px;
                    margin-bottom: 10px;
                    border-radius: 8px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }}
                .fav-star {{
                    color: gold;
                    cursor: pointer;
                    font-size: 1.2rem;
                    margin-left: 10px;
                }}
                .add-form {{ margin-top: 30px; }}
                input[type="text"] {{
                    width: 70%;
                    padding: 10px;
                    border-radius: 4px;
                    border: none;
                    background: #2b2b3c;
                    color: white;
                }}
                input[type="submit"] {{
                    padding: 10px 15px;
                    background: #4CAF50;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                }}
            </style>
            <script>
                function togglePodcastFavorite(url) {{
                    let favs = JSON.parse(localStorage.getItem('podcastFavorites') || '[]');
                    if (favs.includes(url)) {{
                        favs = favs.filter(u => u !== url);
                    }} else {{
                        favs.push(url);
                    }}
                    localStorage.setItem('podcastFavorites', JSON.stringify(favs));
                    updateFavoriteStars();
                }}
                
                function updateFavoriteStars() {{
                    const favs = JSON.parse(localStorage.getItem('podcastFavorites') || '[]');
                    document.querySelectorAll('.podcast-star').forEach(star => {{
                        const url = star.getAttribute('data-url');
                        star.textContent = favs.includes(url) ? '★' : '☆';
                    }});
                }}
                
                function showTab(tabId) {{
                    document.querySelectorAll('.tab-content').forEach(tab => {{
                        tab.classList.remove('active');
                    }});
                    document.querySelectorAll('.tab-button').forEach(btn => {{
                        btn.classList.remove('active');
                    }});
                    document.getElementById(tabId + '-tab').classList.add('active');
                    document.getElementById(tabId + '-btn').classList.add('active');
                }}
                
                window.onload = function() {{
                    updateFavoriteStars();
                    // Show favorites tab by default if it has items
                    const favs = JSON.parse(localStorage.getItem('podcastFavorites') || [];
                    if (favs.length > 0) {{
                        showTab('favorites');
                    }} else {{
                        showTab('all');
                    }}
                }};
            </script>
        </head>
        <body>
            <div class="container">
                <h2>🎧 Podcasts</h2>
                
                <div class="tab-container">
                    <button id="all-btn" class="tab-button active" onclick="showTab('all')">All Podcasts</button>
                    <button id="favorites-btn" class="tab-button" onclick="showTab('favorites')">Favorites</button>
                </div>
                
                <div id="all-tab" class="tab-content active">
                    <ul class="podcast-list">
                        {"".join(
                            f'''
                            <li class="podcast-item">
                                <a href="/podcast?url={feed}">{feed.split('//')[-1].split('/')[0]}</a>
                                <span class="podcast-star fav-star" data-url="{feed}" onclick="togglePodcastFavorite('{feed}')">☆</span>
                            </li>
                            '''
                            for feed in saved_podcasts
                        )}
                    </ul>
                </div>
                
                <div id="favorites-tab" class="tab-content">
                    <ul class="podcast-list" id="favorites-list"></ul>
                </div>
                
                <div class="add-form">
                    <h3>Add New Podcast</h3>
                    <form method="get">
                        <input type="text" name="url" placeholder="Enter podcast RSS feed URL" required>
                        <input type="submit" value="Add Podcast">
                    </form>
                </div>
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
    for entry in feed.entries[:15]:
        audio_url = next((link.href for link in entry.enclosures if link.type.startswith('audio')), None)
        if audio_url:
            episodes_html += f"""
            <div class="podcast-item">
                <h3>{entry.title}</h3>
                <p>{entry.get('description', 'No description available')}</p>
                <audio controls>
                    <source src="{audio_url}" type="audio/mpeg">
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
            .podcast-header {{ display: flex; align-items: center; gap: 15px; margin-bottom: 20px; }}
            .fav-btn {{ font-size: 1.5rem; color: gold; cursor: pointer; }}
            h2 {{ color: #4CAF50; margin: 0; }}
            .podcast-item {{ margin-bottom: 30px; padding: 15px; background: #2b2b3c; border-radius: 8px; }}
            audio {{ width: 100%; margin-top: 10px; }}
            .back-link {{ display: inline-block; margin-top: 20px; color: #4CAF50; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="podcast-header">
                <h2>{feed.feed.title}</h2>
            </div>
            <p>{feed.feed.get('description', '')}</p>
            {episodes_html}
            <a href="/podcast" class="back-link">← Back to Podcasts</a>
        </div>
    </body>
    </html>
    """

# 🔍 Global Search Route
@app.route("/search")
def search():
    query = request.args.get("q", "").lower()
    
    # Search radio stations
    radio_results = [
        {"type": "radio", "name": name, "url": f"/{name}"} 
        for name in RADIO_STATIONS.keys() 
        if query in name.lower()
    ]
    
    # Search podcasts
    podcast_results = [
        {"type": "podcast", "url": feed, "display": feed.split('//')[-1].split('/')[0]}
        for feed in load_podcasts()
        if query in feed.lower()
    ]
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Search Results</title>
        <style>
            body {{ font-family: sans-serif; background: #1e1e2f; color: white; padding: 20px; }}
            .container {{ max-width: 800px; margin: 0 auto; }}
            .search-header {{ margin-bottom: 20px; }}
            .search-box {{ 
                width: 100%; 
                padding: 12px; 
                font-size: 1rem;
                border-radius: 6px;
                border: none;
                background: #2b2b3c;
                color: white;
            }}
            .results {{ margin-top: 20px; }}
            .result-card {{
                background: #2b2b3c;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 8px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .result-type {{
                background: #4CAF50;
                padding: 3px 8px;
                border-radius: 4px;
                font-size: 0.8rem;
                margin-right: 10px;
            }}
            .result-name {{ flex-grow: 1; }}
            .fav-star {{
                color: gold;
                cursor: pointer;
                font-size: 1.2rem;
                margin-left: 10px;
            }}
        </style>
        <script>
            function toggleFavorite(type, id) {{
                const storageKey = type === 'radio' ? 'favourites' : 'podcastFavorites';
                let favs = JSON.parse(localStorage.getItem(storageKey) || []);
                
                if (favs.includes(id)) {{
                    favs = favs.filter(item => item !== id);
                }} else {{
                    favs.push(id);
                }}
                localStorage.setItem(storageKey, JSON.stringify(favs));
                updateFavoriteStars();
            }}
            
            function updateFavoriteStars() {{
                // Update radio stars
                const radioFavs = JSON.parse(localStorage.getItem('favourites') || []);
                document.querySelectorAll('.radio-star').forEach(star => {{
                    const name = star.getAttribute('data-name');
                    star.textContent = radioFavs.includes(name) ? '★' : '☆';
                }});
                
                // Update podcast stars
                const podcastFavs = JSON.parse(localStorage.getItem('podcastFavorites') || []);
                document.querySelectorAll('.podcast-star').forEach(star => {{
                    const url = star.getAttribute('data-url');
                    star.textContent = podcastFavs.includes(url) ? '★' : '☆';
                }});
            }}
            
            window.onload = updateFavoriteStars;
        </script>
    </head>
    <body>
        <div class="container">
            <div class="search-header">
                <h2>🔍 Search Results</h2>
                <form method="get" action="/search">
                    <input 
                        class="search-box" 
                        type="text" 
                        name="q" 
                        value="{query}" 
                        placeholder="Search radio stations and podcasts..."
                        autofocus
                    >
                </form>
            </div>
            
            <div class="results">
                {"".join(
                    f"""
                    <div class="result-card">
                        <div style="display: flex; align-items: center;">
                            <span class="result-type">{result['type'].upper()}</span>
                            <span class="result-name">{result.get('name', result.get('display', ''))}</span>
                        </div>
                        <div>
                            <a href="{result['url']}">Open</a>
                            <span 
                                class="fav-star {'radio-star' if result['type'] == 'radio' else 'podcast-star'}" 
                                data-{'name' if result['type'] == 'radio' else 'url'}="{result.get('name', result.get('url', ''))}"
                                onclick="toggleFavorite('{result['type']}', '{result.get('name', result.get('url', ''))}')"
                            >☆</span>
                        </div>
                    </div>
                    """ 
                    for result in radio_results + podcast_results
                )}
                {"" if radio_results or podcast_results else "<p>No results found</p>"}
            </div>
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

    saved_podcasts = load_podcasts()
    podcast_favs = json.loads(request.cookies.get('podcastFavorites', '[]'))
    
    podcast_html = "".join(
        f"""
        <div class='card' data-url='{feed}'>
            <a href='/podcast?url={feed}'>{feed.split('//')[-1].split('/')[0]}</a>
            <button class="fav-btn" onclick="togglePodcastFavourite('{feed}')">☆</button>
        </div>
        """ for feed in saved_podcasts if feed in podcast_favs
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
            .tab-buttons {{
                display: flex;
                background: #2b2b3c;
                padding: 5px;
            }}
            .tab-button {{
                flex: 1;
                padding: 10px;
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                text-align: center;
            }}
            .tab-button.active {{
                background: #4CAF50;
                border-radius: 4px;
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
                background: #2b2b3c;
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
            <h1>⭐ Media Hub</h1>
        </div>

        <div class="side-menu" id="sideMenu">
            <a href="#" onclick="showTab('radio'); toggleMenu();">📻 Radio</a>
            <a href="#" onclick="showTab('podcast'); toggleMenu();">🎙️ Podcasts</a>
            <a href="/search" onclick="toggleMenu();">🔍 Global Search</a>
        </div>

        <div class="tab-buttons">
            <button class="tab-button active" onclick="showTab('fav-radio')">Favorite Radios</button>
            <button class="tab-button" onclick="showTab('all-radio')">All Radios</button>
            <button class="tab-button" onclick="showTab('add-radio')">Add Radio</button>
        </div>

        <div id="fav-radio-tab" class="tab-content active">
            <div class="scroll-container">
                <div class="grid" id="favGrid"></div>
            </div>
        </div>

        <div id="all-radio-tab" class="tab-content">
            <div class="scroll-container">
                <div class="grid" id="stationGrid">{links_html}</div>
            </div>
        </div>

        <div id="add-radio-tab" class="tab-content">
            <form class="add-form" method="POST" action="/add">
                <input type="text" name="name" placeholder="Station name (no space)" required />
                <input type="text" name="url" placeholder="Stream URL" required />
                <input type="submit" value="Add Station" />
            </form>
        </div>

        <div id="podcast-tab" class="tab-content">
            <div class="scroll-container">
                <div class="grid" id="podcastGrid">{podcast_html}</div>
            </div>
        </div>

        <script>
            let activeTab = "fav-radio";

            function toggleFavourite(name) {{
                let favs = JSON.parse(localStorage.getItem("favourites") || []);
                if (favs.includes(name)) {{
                    favs = favs.filter(n => n !== name);
                }} else {{
                    favs.push(name);
                }}
                localStorage.setItem("favourites", JSON.stringify(favs));
                updateDisplay();
            }}
            
            function togglePodcastFavourite(url) {{
                let favs = JSON.parse(localStorage.getItem("podcastFavorites") || []);
                if (favs.includes(url)) {{
                    favs = favs.filter(u => u !== url);
                }} else {{
                    favs.push(url);
                }}
                localStorage.setItem("podcastFavorites", JSON.stringify(favs));
                updateDisplay();
            }}

            function updateDisplay() {{
                // Update radio favorites
                const radioFavs = JSON.parse(localStorage.getItem("favourites") || []);
                document.querySelectorAll(".fav-btn").forEach(btn => {{
                    const name = btn.parentElement.getAttribute("data-name");
                    if (name) {{
                        btn.textContent = radioFavs.includes(name) ? "★" : "☆";
                    }}
                }});
                
                // Update podcast favorites
                const podcastFavs = JSON.parse(localStorage.getItem("podcastFavorites") || []);
                document.querySelectorAll(".card[data-url]").forEach(card => {{
                    const url = card.getAttribute("data-url");
                    const btn = card.querySelector(".fav-btn");
                    if (btn) btn.textContent = podcastFavs.includes(url) ? "★" : "☆";
                }});
                
                // Update favorite grids
                const favGrid = document.getElementById("favGrid");
                if (favGrid) {{
                    favGrid.innerHTML = "";
                    radioFavs.forEach(name => {{
                        const el = document.querySelector(`[data-name='${{name}}']`);
                        if (el) favGrid.appendChild(el.cloneNode(true));
                    }});
                }}
                
                const podcastGrid = document.getElementById("podcastGrid");
                if (podcastGrid) {{
                    podcastGrid.innerHTML = "";
                    podcastFavs.forEach(url => {{
                        const el = document.querySelector(`[data-url='${{url}}']`);
                        if (el) podcastGrid.appendChild(el.cloneNode(true));
                    }});
                }}
            }}

            function showTab(tab) {{
                activeTab = tab;
                document.querySelectorAll(".tab-content").forEach(div => div.classList.remove("active"));
                document.querySelectorAll(".tab-button").forEach(btn => btn.classList.remove("active"));
                
                document.getElementById(tab + "-tab").classList.add("active");
                if (tab.startsWith("fav-") || tab.startsWith("all-") || tab.startsWith("add-")) {{
                    document.querySelector(`button[onclick="showTab('${{tab}}')"]`).classList.add("active");
                }}
                
                updateDisplay();
            }}

            function toggleMenu() {{
                const menu = document.getElementById("sideMenu");
                menu.style.left = (menu.style.left === "0px") ? "-220px" : "0px";
            }}

            window.onload = function() {{
                updateDisplay();
                // Show radio tab by default
                showTab('fav-radio');
            }};
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)