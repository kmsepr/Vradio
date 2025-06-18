import subprocess
import time
from flask import Flask, Response, redirect, request
import json
import os
from pathlib import Path

app = Flask(__name__)

STATIONS_FILE = "radio_stations.json"

# ------------------------------
# 📻 Default categorized stations
# ------------------------------
DEFAULT_STATIONS = {
    "News": {
        "al_jazeera": "http://live-hls-audio-web-aja.getaj.net/VOICE-AJA/index.m3u8",
        "asianet_news": "https://vidcdn.vidgyor.com/asianet-origin/audioonly/chunks.m3u8",
        "manorama_news": "http://103.199.161.254/Content/manoramanews/Live/Channel(ManoramaNews)/index.m3u8",
    },
    "Islamic": {
        "deenagers_radio": "http://104.7.66.64:8003/",
        "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream"
    },
    "Malayalam": {
        "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL"
    },
    "Hindi": {
        "nonstop_hindi": "http://s5.voscast.com:8216/stream"
    },
    "English": {
        "bloomberg_tv": "https://bloomberg-bloomberg-3-br.samsung.wurl.tv/manifest/playlist.m3u8"
    }
}

# ------------------------------
# 📦 Load or initialize data
# ------------------------------
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

# Flatten all stations into a single dict for direct access
FLAT_STATION_MAP = {
    station_id: url
    for category in RADIO_STATIONS.values()
    for station_id, url in category.items()
}

# ------------------------------
# 🔊 FFmpeg stream generator
# ------------------------------
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

# ------------------------------
# 🎯 Direct flat route: /station_id
# ------------------------------
@app.route("/<station_id>")
def direct_stream(station_id):
    if station_id in FLAT_STATION_MAP:
        return Response(generate_stream(FLAT_STATION_MAP[station_id]), mimetype="audio/mpeg")
    return "Station not found", 404

# ------------------------------
# 🗑 Delete station by category
# ------------------------------
@app.route("/delete/<category>/<station_name>", methods=["POST"])
def delete_station(category, station_name):
    if category in RADIO_STATIONS and station_name in RADIO_STATIONS[category]:
        del RADIO_STATIONS[category][station_name]
        if not RADIO_STATIONS[category]:
            del RADIO_STATIONS[category]
        save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

# ------------------------------
# ➕ Add new station
# ------------------------------
@app.route("/add", methods=["POST"])
def add_station():
    category = request.form.get("category", "").strip()
    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip()

    if not category or not name or not url:
        return "Missing fields", 400

    if category not in RADIO_STATIONS:
        RADIO_STATIONS[category] = {}
    RADIO_STATIONS[category][name] = url
    save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

# ------------------------------
# 🖥 Web UI
# ------------------------------
@app.route("/")
def index():
    categories_html = "".join(
        f"""
        <div class='category-card' onclick="showStations('{category}')">
            <h3>{category}</h3>
            <p>{len(stations)} stations</p>
        </div>
        """ for category, stations in RADIO_STATIONS.items()
    )

    stations_html = "".join(
        f"""
        <div class='station-card' data-category='{category}'>
            <div class='station-header'>
                <span class='station-name' onclick="playStream('/{name}')">{name.replace('_', ' ').title()}</span>
                <form method='POST' action='/delete/{category}/{name}' style='display:inline;'>
                    <button type='submit'>🗑️</button>
                </form>
            </div>
        </div>
        """ for category, stations in RADIO_STATIONS.items() 
        for name in stations
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Radio</title>
        <style>
            body {{
                font-family: sans-serif;
                background: #111;
                color: white;
                padding: 20px;
            }}
            .categories {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 10px;
                margin-bottom: 20px;
            }}
            .category-card {{
                background: #222;
                padding: 10px;
                border-radius: 8px;
                cursor: pointer;
            }}
            .station-card {{
                background: #222;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 8px;
            }}
            .station-name {{
                color: #4CAF50;
                font-weight: bold;
                cursor: pointer;
            }}
            .station-header {{
                display: flex;
                justify-content: space-between;
            }}
            button {{
                background: none;
                color: white;
                border: 1px solid #555;
                border-radius: 4px;
                cursor: pointer;
            }}
            .back-button {{
                cursor: pointer;
                color: #4CAF50;
                margin-bottom: 10px;
            }}
            input {{
                width: 100%;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 4px;
                border: none;
            }}
            .submit-btn {{
                background: #4CAF50;
                color: white;
                padding: 10px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <h1>📻 Radio Stations</h1>

        <div id="categories" class="categories">{categories_html}</div>

        <div id="stations-container" style="display:none;">
            <div class="back-button" onclick="showCategories()">← Back</div>
            <div id="stations"></div>
        </div>

        <h2>Add New Station</h2>
        <form method="POST" action="/add">
            <input name="category" placeholder="Category (e.g. News)" required>
            <input name="name" placeholder="Station ID (e.g. al_jazeera)" required>
            <input name="url" placeholder="Stream URL" required>
            <button type="submit" class="submit-btn">Add</button>
        </form>

        <script>
            const allHTML = `{stations_html}`

            function showStations(category) {{
                document.getElementById('categories').style.display = 'none';
                document.getElementById('stations-container').style.display = 'block';
                const container = document.getElementById('stations');
                container.innerHTML = '';
                const temp = document.createElement('div');
                temp.innerHTML = allHTML;
                temp.querySelectorAll(`[data-category="${{category}}"]`).forEach(el => container.appendChild(el));
            }}

            function showCategories() {{
                document.getElementById('categories').style.display = 'grid';
                document.getElementById('stations-container').style.display = 'none';
            }}

            function playStream(url) {{
                window.open(url, '_blank');
            }}
        </script>
    </body>
    </html>
    """

# ------------------------------
# 🏁 Run the app
# ------------------------------
if __name__ == "__main__":
    if not Path(STATIONS_FILE).exists():
        save_data(STATIONS_FILE, DEFAULT_STATIONS)
    app.run(host="0.0.0.0", port=8000, threaded=True)