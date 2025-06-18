import subprocess
import time
from flask import Flask, Response, redirect, request
import json
from pathlib import Path
import re

app = Flask(__name__)
STATIONS_FILE = "radio_stations.json"

# 🎧 Default stations
DEFAULT_STATIONS = {
    "News": {
        "al_jazeera": {
            "name": "Al Jazeera",
            "url": "http://live-hls-audio-web-aja.getaj.net/VOICE-AJA/index.m3u8"
        },
        "asianet_news": {
            "name": "Asianet News",
            "url": "https://vidcdn.vidgyor.com/asianet-origin/audioonly/chunks.m3u8"
        }
    },
    "Islamic": {
        "muthnabi_radio": {
            "name": "Muthnabi Radio",
            "url": "http://cast4.my-control-panel.com/proxy/muthnabi/stream"
        }
    },
    "YouTube": {
        "shajahan_rahmani": {
            "name": "Shajahan Rahmani",
            "url": "http://capitalist-anthe-pscj-4a28f285.koyeb.app/shajahan_rahmani"
        },
        "media_one": {
            "name": "Mediaone",
            "url": "http://capitalist-anthe-pscj-4a28f285.koyeb.app/media_one"
        }
    }
}

def load_data(filename, default_data):
    try:
        if Path(filename).exists():
            with open(filename, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return default_data

def save_data(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {filename}: {e}")

RADIO_STATIONS = load_data(STATIONS_FILE, DEFAULT_STATIONS)

# Flat map for FFmpeg proxy routes
FLAT_STATION_MAP = {
    sid: station["url"]
    for category in RADIO_STATIONS.values()
    for sid, station in category.items()
    if not station["url"].startswith("http://your-koyeb") and not sid.startswith("http")
}

def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()
        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10", "-fflags", "nobuffer", "-flags", "low_delay",
                "-i", url, "-vn", "-ac", "1", "-b:a", "64k", "-f", "mp3", "-"
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
            print(f"Stream error: {e}")
            time.sleep(5)

@app.route("/<station_id>")
def direct_stream(station_id):
    if station_id in FLAT_STATION_MAP:
        return Response(generate_stream(FLAT_STATION_MAP[station_id]), mimetype="audio/mpeg")
    return "Station not found", 404

@app.route("/delete/<category>/<station_id>", methods=["POST"])
def delete_station(category, station_id):
    if category in RADIO_STATIONS and station_id in RADIO_STATIONS[category]:
        del RADIO_STATIONS[category][station_id]
        if not RADIO_STATIONS[category]:
            del RADIO_STATIONS[category]
        save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

@app.route("/add", methods=["POST"])
def add_station():
    category = request.form.get("category", "").strip()
    url = request.form.get("url", "").strip()
    name = request.form.get("name", "").strip()

    if not category or not url:
        return "Missing fields", 400

    if not name:
        name = url  # fallback to URL as display

    station_id = re.sub(r'\W+', '_', name.lower())

    new_station = {
        "name": name,
        "url": url
    }

    if category not in RADIO_STATIONS:
        RADIO_STATIONS[category] = {}
    RADIO_STATIONS[category][station_id] = new_station
    save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

@app.route("/")
def index():
    html_stations = ""
    for category, stations in RADIO_STATIONS.items():
        for sid, station in stations.items():
            display_name = station.get("name", sid.replace("_", " ").title())
            url = station.get("url", "")
            is_manual = sid.startswith("http") or url.startswith("http://") or url.startswith("https://")
            play_link = url if sid.startswith("http") else f"/{sid}"
            html_stations += f"""
            <div class='station-card' data-category="{category}">
                <div class='station-header'>
                    <span class='station-name' onclick="playStream('{play_link}')">{display_name}</span>
                    <form method='POST' action='/delete/{category}/{sid}' style='display:inline;'>
                        <button type='submit'>🗑️</button>
                    </form>
                </div>
            </div>
            """

    html_categories = "".join(
        f"""
        <div class='category-card' onclick="showStations('{cat}')">
            <h3>{cat}</h3>
            <p>{len(stations)} stations</p>
        </div>
        """ for cat, stations in RADIO_STATIONS.items()
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Radio</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background:#111; color:#fff; font-family:sans-serif; padding:20px; }}
            .categories {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; }}
            .category-card, .station-card {{ background:#222; border-radius:8px; padding:10px; margin-bottom:10px; cursor:pointer; }}
            .station-header {{ display:flex; justify-content:space-between; align-items:center; }}
            .station-name {{ color:#4CAF50; font-weight:bold; cursor:pointer; }}
            button {{ background:none; border:1px solid #555; color:white; padding:4px 8px; border-radius:4px; cursor:pointer; }}
            input {{ width:100%; padding:10px; margin-bottom:10px; border:none; border-radius:4px; }}
            .submit-btn {{ background:#4CAF50; color:white; border:none; width:100%; padding:10px; border-radius:4px; }}
            .back-button {{ color:#4CAF50; margin-bottom:10px; cursor:pointer; }}
        </style>
    </head>
    <body>
        <h1>📻 Radio Stations</h1>
        <div id="categories" class="categories">{html_categories}</div>

        <div id="stations-container" style="display:none;">
            <div class="back-button" onclick="showCategories()">← Back</div>
            <div id="stations"></div>
        </div>

        <div id="add-form">
            <h2>Add New Station</h2>
            <form method="POST" action="/add">
                <input name="category" placeholder="Category (e.g. Malayalam)" required>
                <input name="name" placeholder="Display Name (e.g. Media One)">
                <input name="url" placeholder="Stream URL (http://...)" required>
                <button class="submit-btn" type="submit">Add Station</button>
            </form>
        </div>

        <script>
            const allHTML = `{html_stations}`

            function showStations(category) {{
                document.getElementById('categories').style.display = 'none';
                document.getElementById('stations-container').style.display = 'block';
                document.getElementById('add-form').style.display = 'none';
                const container = document.getElementById('stations');
                container.innerHTML = '';
                const temp = document.createElement('div');
                temp.innerHTML = allHTML;
                temp.querySelectorAll(`[data-category="${{category}}"]`).forEach(el => container.appendChild(el));
            }}

            function showCategories() {{
                document.getElementById('categories').style.display = 'grid';
                document.getElementById('stations-container').style.display = 'none';
                document.getElementById('add-form').style.display = 'block';
            }}

            function playStream(url) {{
                window.open(url, '_blank');
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    if not Path(STATIONS_FILE).exists():
        save_data(STATIONS_FILE, DEFAULT_STATIONS)
    app.run(host="0.0.0.0", port=8000, threaded=True)