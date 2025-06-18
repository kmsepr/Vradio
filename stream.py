import subprocess
import time
import os
import json
import requests
import feedparser
from flask import Flask, Response, request, redirect

app = Flask(__name__)

# 📡 List of radio stations
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL",
}

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

def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()
        process = subprocess.Popen(
            ["ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "10",
             "-fflags", "nobuffer", "-flags", "low_delay", "-i", url, "-vn", "-ac", "1", "-b:a", "64k",
             "-buffer_size", "1024k", "-f", "mp3", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )
        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            process.kill()
            break
        except Exception as e:
            print(f"Stream error: {e}")
        print("Restarting stream...")
        time.sleep(5)

@app.route("/<station_name>")
def stream(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

@app.route("/add", methods=["POST"])
def add_station():
    name = request.form.get("name", "").strip().lower().replace(" ", "_")
    url = request.form.get("url", "").strip()
    if name and url:
        RADIO_STATIONS[name] = url
    return redirect("/")

@app.route("/podcast")
def podcast():
    rss_url = request.args.get("url")
    action = request.args.get("action")
    saved_podcasts = load_podcasts()

    if action == "remove" and rss_url:
        if rss_url in saved_podcasts:
            saved_podcasts.remove(rss_url)
            save_podcasts(saved_podcasts)
        return redirect("/podcast")

    if not rss_url:
        return f"""
        <html><head><title>Podcasts</title><meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: sans-serif; background: #1e1e2f; color: white; padding: 15px; }}
            .podcast {{ background: #2b2b3c; padding: 12px; border-radius: 8px; margin-bottom: 10px; }}
            .remove {{ background: #f44336; border: none; color: white; padding: 5px 10px; }}
            input {{ width: 100%; padding: 10px; margin: 10px 0; background: #333; border: none; color: white; }}
        </style></head><body>
        <h2>🎙️ Saved Podcasts</h2>
        {"".join(
            "<div class='podcast'><b>{}</b><br>{}<br><a href='/podcast?url={}'>View</a> "
            "<a href='/podcast?url={}&action=remove'><button class='remove'>Remove</button></a></div>".format(
                get_podcast_title(url), url, url, url
            )
            for url in saved_podcasts
        ) or "<p>No podcasts saved</p>"}
        <form method="get" action="/podcast">
            <input type="text" name="url" placeholder="Enter RSS feed URL" required>
            <input type="submit" value="Add Podcast">
        </form>
        </body></html>
        """

    # If a feed URL is specified, show episodes
    try:
        feed = feedparser.parse(rss_url)
        if not feed.entries:
            return "⚠️ Invalid or empty podcast feed."

        if rss_url not in saved_podcasts:
            saved_podcasts.append(rss_url)
            save_podcasts(saved_podcasts)

        episodes = sorted(feed.entries, key=lambda x: x.get('published_parsed', (0, 0, 0)), reverse=True)
        html = f"<h2>{feed.feed.get('title', 'Podcast')}</h2><p>{feed.feed.get('description', '')}</p>"
        for ep in episodes[:30]:
            audio = next((l.href for l in ep.enclosures if l.type.startswith("audio")), None)
            if audio:
                date = ep.get("published", "")
                html += f"<div><b>{ep.title}</b><br><small>{date}</small><br>{ep.get('summary', '')[:200]}...<br>" \
                        f"<audio controls src='{audio}'></audio><hr></div>"
        return f"<html><body style='background:#1e1e2f;color:white;padding:15px;font-family:sans-serif;'>{html}<br><a href='/podcast' style='color:lime'>← Back</a></body></html>"
    except Exception as e:
        return f"⚠️ Error loading podcast: {str(e)}"

@app.route("/podcast_search")
def podcast_search():
    query = request.args.get("q", "").strip()
    results_html = ""
    if query:
        try:
            res = requests.get("https://itunes.apple.com/search", params={
                "term": query, "media": "podcast", "limit": 10
            })
            data = res.json()
            for item in data.get("results", []):
                title = item.get("collectionName", "Untitled")
                feed_url = item.get("feedUrl")
                artwork = item.get("artworkUrl100", "")
                if feed_url:
                    results_html += f"""
                        <div style="display:flex;align-items:center;gap:10px;margin-bottom:15px;">
                            <img src="{artwork}" width="60">
                            <div>
                                <b>{title}</b><br>
                                <a href="/podcast?url={feed_url}">➕ Add & View</a>
                            </div>
                        </div><hr>
                    """
        except Exception as e:
            results_html = f"<p>Error: {str(e)}</p>"

    return f"""
    <html><head><title>Search Podcasts</title><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>body{{background:#1e1e2f;color:white;font-family:sans-serif;padding:15px}}input{{width:100%;padding:10px;margin:10px 0;background:#333;border:none;color:white}}</style>
    </head><body>
    <h2>🔍 Search Global Podcasts</h2>
    <form method="get"><input type="text" name="q" placeholder="Search podcasts..." value="{query}" required></form>
    {results_html or "<p>Type above to search podcasts.</p>"}
    <p><a href="/podcast" style="color:#4CAF50;">← Back to My Podcasts</a></p>
    </body></html>
    """

@app.route("/")
def index():
    def pastel_color(i):
        r = (100 + (i * 40)) % 256
        g = (150 + (i * 60)) % 256
        b = (200 + (i * 80)) % 256
        return f"{r}, {g}, {b}"

    links_html = "".join(
        f"<div class='card' data-name='{name}' style='background-color:rgba({pastel_color(i)},0.85);'><a href='/{name}'>{name}</a><button class='fav-btn' onclick=\"toggleFavourite('{name}')\">⭐</button></div>"
        for i, name in enumerate(reversed(list(RADIO_STATIONS)))
    )

    return f"""
    <html><head><title>Radio</title><meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body{{background:#1e1e2f;color:white;font-family:sans-serif;margin:0}}
        .header{{background:#2b2b3c;padding:10px;display:flex;align-items:center}}
        .menu-icon{{font-size:1.5rem;cursor:pointer;margin-right:10px}}
        .side-menu{{position:fixed;top:0;left:-220px;width:200px;height:100%;background:#2b2b3c;padding-top:60px;transition:left 0.3s;z-index:999}}
        .side-menu a{{display:block;padding:12px 20px;color:white;text-decoration:none;border-bottom:1px solid #444}}
        .side-menu a:hover{{background-color:#444}}
        .card{{padding:12px;border-radius:10px;text-align:center;position:relative;margin:10px}}
        .card a{{color:white;text-decoration:none}}
        .fav-btn{{position:absolute;top:6px;right:10px;background:none;border:none;color:gold;font-size:1.2rem;cursor:pointer}}
        .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;padding:10px}}
    </style>
    <script>
        function toggleMenu() {{
            const menu = document.getElementById("sideMenu");
            menu.style.left = (menu.style.left === "0px") ? "-220px" : "0px";
        }}
        function toggleFavourite(name) {{
            let favs = JSON.parse(localStorage.getItem("favourites") || "[]");
            if (favs.includes(name)) {{ favs = favs.filter(n => n !== name); }}
            else {{ favs.push(name); }}
            localStorage.setItem("favourites", JSON.stringify(favs));
            updateDisplay();
        }}
        function updateDisplay() {{
            const favs = JSON.parse(localStorage.getItem("favourites") || "[]");
            document.querySelectorAll(".card").forEach(card => {{
                const name = card.getAttribute("data-name");
                card.style.display = favs.includes(name) ? "block" : "none";
                const btn = card.querySelector(".fav-btn");
                if (btn) btn.textContent = favs.includes(name) ? "★" : "⭐";
            }});
        }}
        window.onload = updateDisplay;
    </script>
    </head>
    <body>
    <div class="header">
        <span class="menu-icon" onclick="toggleMenu()">☰</span>
        <h2>⭐ Favourite Radios</h2>
    </div>
    <div class="side-menu" id="sideMenu">
        <a href="/">🏠 Home</a>
        <a href="/podcast">🎙️ Podcasts</a>
        <a href="/podcast_search">🔍 Search Podcasts</a>
    </div>
    <div class="grid">{links_html}</div>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)