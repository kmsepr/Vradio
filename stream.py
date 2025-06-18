import subprocess
import time
import os
import json
import feedparser
import requests
from bs4 import BeautifulSoup
from flask import Flask, Response, request, redirect, jsonify

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
        podcast_favs = json.loads(request.cookies.get('podcastFavorites', '[]'))
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Podcasts</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: sans-serif; 
            background: #1e1e2f; 
            color: white; 
            padding: 10px;
            margin: 0;
            font-size: 14px;
        }}
        .container {{ 
            max-width: 100%;
            margin: 0 auto;
            padding: 5px;
        }}
        h2 {{ 
            color: #4CAF50; 
            font-size: 18px;
            margin: 10px 0;
        }}
        .podcast-list {{ 
            list-style: none; 
            padding: 0;
            margin: 0;
        }}
        .podcast-item {{
            background: #2b2b3c;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 5px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .podcast-item a {{
            color: #4CAF50;
            text-decoration: none;
            flex-grow: 1;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            font-size: 14px;
        }}
        .fav-star {{
            color: gold;
            cursor: pointer;
            font-size: 16px;
            margin-left: 8px;
            flex-shrink: 0;
        }}
        .search-container {{
            margin-bottom: 15px;
        }}
        .search-input {{
            width: 100%;
            padding: 10px;
            border-radius: 5px;
            border: none;
            background: #2b2b3c;
            color: white;
            font-size: 14px;
        }}
        .search-button {{
            width: 100%;
            padding: 10px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            margin-top: 8px;
            font-size: 14px;
        }}
    </style>
    <script>
        function togglePodcastFavorite(url) {{
            let favs = JSON.parse(localStorage.getItem('podcastFavorites') || []);
            if (favs.includes(url)) {{
                favs = favs.filter(u => u !== url);
            }} else {{
                favs.push(url);
            }}
            localStorage.setItem('podcastFavorites', JSON.stringify(favs));
            updateFavoriteStars();
        }}
        
        function updateFavoriteStars() {{
            const favs = JSON.parse(localStorage.getItem('podcastFavorites') || []);
            document.querySelectorAll('.podcast-star').forEach(star => {{
                const url = star.getAttribute('data-url');
                star.textContent = favs.includes(url) ? '★' : '☆';
            }});
        }}
        
        window.onload = updateFavoriteStars;
    </script>
</head>
<body>
    <div class="container">
        <h2>🎧 My Podcasts</h2>
        
        <div class="search-container">
            <form action="/podcasts/search" method="get">
                <input 
                    type="text" 
                    name="keyword" 
                    class="search-input" 
                    placeholder="Search public podcasts..."
                >
                <button type="submit" class="search-button">🔍 Search Public Podcasts</button>
            </form>
        </div>
        
        <ul class="podcast-list">
            {''.join(
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
</body>
</html>"""

    # Parse and display podcast feed
    feed = feedparser.parse(rss_url)
    if not feed.entries:
        return "⚠️ Invalid or empty podcast feed."

    # Add to saved podcasts if not already there
    if rss_url not in saved_podcasts:
        saved_podcasts.append(rss_url)
        save_podcasts(saved_podcasts)

    episodes_html = ""
    for entry in feed.entries[:10]:  # Show fewer episodes on small screens
        audio_url = next((link.href for link in entry.enclosures if link.type.startswith('audio')), None)
        if audio_url:
            episodes_html += f"""
            <div style="
                background: #2b2b3c;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 5px;
            ">
                <h3 style="
                    margin: 0 0 5px 0;
                    font-size: 14px;
                    color: #4CAF50;
                ">{entry.title}</h3>
                <p style="
                    margin: 0 0 8px 0;
                    font-size: 12px;
                    color: #ccc;
                ">{entry.get('description', 'No description')}</p>
                <audio controls style="
                    width: 100%;
                    height: 30px;
                ">
                    <source src="{audio_url}" type="audio/mpeg">
                </audio>
            </div>
            """

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>{feed.feed.title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <style>
        body {{
            font-family: sans-serif;
            background: #1e1e2f;
            color: white;
            padding: 10px;
            margin: 0;
            font-size: 14px;
        }}
        .container {{
            max-width: 100%;
            margin: 0 auto;
        }}
        h2 {{
            color: #4CAF50;
            margin: 10px 0;
            font-size: 16px;
        }}
        .back-link {{
            display: inline-block;
            margin-top: 15px;
            color: #4CAF50;
            text-decoration: none;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>{feed.feed.title}</h2>
        <p style="font-size: 12px; color: #aaa;">{feed.feed.get('description', '')}</p>
        {episodes_html}
        <a href="/podcast" class="back-link">← Back to Podcasts</a>
    </div>
</body>
</html>"""

# Public podcast search functions
def search_podcast_index(query):
    """Search PodcastIndex.org's public database"""
    try:
        url = f"https://podcastindex.org/search?q={query}"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for item in soup.select('.podcast-item')[:5]:  # Limit to 5 results for small screens
            title = item.select_one('.podcast-title').get_text(strip=True)
            author = item.select_one('.podcast-author').get_text(strip=True)
            image = item.select_one('.podcast-image img')['src'] if item.select_one('.podcast-image img') else ''
            feed_url = item.select_one('a.podcast-link')['href']
            
            results.append({
                'title': title[:50] + '...' if len(title) > 50 else title,
                'author': author[:30] + '...' if len(author) > 30 else author,
                'image': image,
                'feed_url': feed_url,
                'source': 'PodcastIndex'
            })
        return results
    except Exception as e:
        print(f"Error searching PodcastIndex: {e}")
        return []

def search_apple_podcasts(query):
    """Search Apple Podcasts"""
    try:
        url = f"https://itunes.apple.com/search?media=podcast&term={query}&limit=5"  # Limit to 5 results
        response = requests.get(url, timeout=10)
        data = response.json()
        
        return [{
            'title': item['collectionName'][:50] + '...' if len(item['collectionName']) > 50 else item['collectionName'],
            'author': item['artistName'][:30] + '...' if len(item['artistName']) > 30 else item['artistName'],
            'image': item['artworkUrl600'] if 'artworkUrl600' in item else '',
            'feed_url': item['feedUrl'],
            'source': 'Apple Podcasts'
        } for item in data.get('results', [])]
    except Exception as e:
        print(f"Error searching Apple Podcasts: {e}")
        return []

# Public podcast search route
@app.route("/podcasts/search")
def podcast_search():
    keyword = request.args.get("keyword", "").strip()
    
    if not keyword:
        return """<!DOCTYPE html>
<html>
<head>
    <title>Podcast Search</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: sans-serif; 
            background: #1e1e2f; 
            color: white; 
            padding: 10px;
            margin: 0;
            font-size: 14px;
        }}
        .container {{ 
            max-width: 100%;
            margin: 0 auto;
            padding: 5px;
        }}
        h1 {{ 
            color: #4CAF50;
            font-size: 18px;
            margin: 10px 0;
        }}
        .search-box {{ 
            width: 100%;
            padding: 12px;
            border-radius: 5px;
            border: none;
            background: #2b2b3c;
            color: white;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        .search-button {{
            width: 100%;
            padding: 12px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            font-size: 14px;
        }}
        .no-results {{
            text-align: center;
            color: #888;
            margin-top: 30px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Search Public Podcasts</h1>
        <form method="get" action="/podcasts/search">
            <input 
                type="text" 
                name="keyword" 
                class="search-box" 
                placeholder="Enter podcast name or topic..."
                autofocus
            >
            <button type="submit" class="search-button">Search</button>
        </form>
        <div class="no-results">
            <p>Search for podcasts from public databases</p>
        </div>
    </div>
</body>
</html>"""
    
    # Search multiple public databases
    all_results = []
    all_results.extend(search_podcast_index(keyword))
    all_results.extend(search_apple_podcasts(keyword))
    
    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Results for "{keyword}"</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <style>
        * {{ box-sizing: border-box; }}
        body {{ 
            font-family: sans-serif; 
            background: #1e1e2f; 
            color: white; 
            padding: 10px;
            margin: 0;
            font-size: 14px;
        }}
        .container {{ 
            max-width: 100%;
            margin: 0 auto;
            padding: 5px;
        }}
        .search-header {{ 
            margin-bottom: 15px;
        }}
        h1 {{ 
            color: #4CAF50;
            font-size: 18px;
            margin: 10px 0;
        }}
        .search-box {{ 
            width: 100%;
            padding: 12px;
            border-radius: 5px;
            border: none;
            background: #2b2b3c;
            color: white;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        .results-container {{ 
            display: grid;
            grid-template-columns: 1fr;
            gap: 10px;
        }}
        .podcast-card {{
            background: #2b2b3c;
            border-radius: 5px;
            overflow: hidden;
        }}
        .podcast-image {{
            width: 100%;
            height: 100px;
            object-fit: cover;
        }}
        .podcast-info {{
            padding: 10px;
        }}
        .podcast-title {{ 
            color: #4CAF50;
            margin: 0 0 5px 0;
            font-size: 14px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .podcast-author {{ 
            color: #aaa; 
            margin: 0 0 5px 0;
            font-size: 12px;
        }}
        .podcast-source {{
            display: inline-block;
            background: #444;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
        }}
        .add-button {{
            display: block;
            width: 100%;
            padding: 8px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 3px;
            cursor: pointer;
            margin-top: 8px;
            font-size: 12px;
        }}
        .no-results {{
            text-align: center;
            color: #888;
            margin-top: 30px;
        }}
        .back-link {{
            display: inline-block;
            margin-top: 15px;
            color: #4CAF50;
            text-decoration: none;
            font-size: 14px;
        }}
    </style>
    <script>
        function addPodcast(feedUrl) {{
            fetch('/add-podcast', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{ feed_url: feedUrl }}),
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success) {{
                    alert('✓ Podcast added');
                }} else {{
                    alert('✗ Error: ' + data.message);
                }}
            }})
            .catch(error => {{
                alert('✗ Network error');
            }});
        }}
    </script>
</head>
<body>
    <div class="container">
        <div class="search-header">
            <h1>🔍 Results for "{keyword}"</h1>
            <form method="get" action="/podcasts/search">
                <input 
                    type="text" 
                    name="keyword" 
                    value="{keyword}"
                    class="search-box" 
                    placeholder="Search podcasts..."
                >
                <button type="submit" class="add-button">Search Again</button>
            </form>
        </div>
        
        <div class="results-container">
            {''.join(
                f'''
                <div class="podcast-card">
                    <img src="{podcast['image']}" class="podcast-image" onerror="this.style.display='none'">
                    <div class="podcast-info">
                        <h3 class="podcast-title" title="{podcast['title']}">{podcast['title']}</h3>
                        <p class="podcast-author">{podcast['author']}</p>
                        <span class="podcast-source">{podcast['source']}</span>
                        <button 
                            class="add-button" 
                            onclick="addPodcast('{podcast['feed_url']}')"
                        >
                            ➕ Add to My Podcasts
                        </button>
                    </div>
                </div>
                '''
                for podcast in all_results
            ) if all_results else '''
            <div class="no-results">
                <p>No podcasts found matching "{keyword}"</p>
                <p>Try different search terms</p>
            </div>
            '''}
        </div>
        
        <a href="/podcast" class="back-link">← Back to My Podcasts</a>
    </div>
</body>
</html>"""

@app.route("/add-podcast", methods=["POST"])
def add_podcast():
    data = request.json
    feed_url = data.get('feed_url')
    
    if not feed_url:
        return jsonify({'success': False, 'message': 'No feed URL provided'}), 400
    
    try:
        saved_podcasts = load_podcasts()
        if feed_url not in saved_podcasts:
            saved_podcasts.append(feed_url)
            save_podcasts(saved_podcasts)
            return jsonify({'success': True, 'message': 'Podcast added successfully'})
        else:
            return jsonify({'success': False, 'message': 'Podcast already exists'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

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

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1" />
    <title>Radio Favourites</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: sans-serif;
            background: #1e1e2f;
            color: white;
            margin: 0;
            padding: 10px;
            font-size: 14px;
        }}
        .header {{
            display: flex;
            align-items: center;
            background: #2b2b3c;
            padding: 8px;
            margin-bottom: 10px;
        }}
        .menu-icon {{
            font-size: 20px;
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
            padding-top: 50px;
            transition: left 0.3s;
            z-index: 999;
            overflow-y: auto;
        }}
        .side-menu a {{
            display: block;
            padding: 12px 15px;
            color: white;
            text-decoration: none;
            border-bottom: 1px solid #444;
            font-size: 14px;
        }}
        .side-menu a:hover {{
            background-color: #444;
        }}
        h1 {{
            font-size: 16px;
            margin: 0;
        }}
        .scroll-container {{
            max-height: calc(100vh - 60px);
            overflow-y: auto;
            padding: 5px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 8px;
        }}
        .card {{
            padding: 8px;
            border-radius: 5px;
            text-align: center;
            position: relative;
            font-size: 12px;
        }}
        .card a {{
            color: white;
            text-decoration: none;
            display: block;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .fav-btn {{
            position: absolute;
            top: 5px;
            right: 5px;
            background: none;
            border: none;
            color: gold;
            font-size: 14px;
            cursor: pointer;
            padding: 0;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        .add-form {{
            max-width: 100%;
            margin: 10px auto;
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: #2a2a3a;
            padding: 10px;
            border-radius: 5px;
        }}
        .add-form input {{
            padding: 8px;
            font-size: 12px;
            border-radius: 3px;
            border: 1px solid #666;
            background: #1e1e2f;
            color: white;
        }}
        .add-form input[type=submit] {{
            background: #007acc;
            cursor: pointer;
            border: none;
            padding: 8px;
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
        <a href="/podcasts/search" onclick="toggleMenu();">🔍 Search Podcasts</a>
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
                if (btn) btn.textContent = favs.includes(name) ? "★" : "☆";
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
</html>"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)