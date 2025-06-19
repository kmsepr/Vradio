import subprocess
import time
from flask import Flask, Response, redirect, request
import json
from pathlib import Path

app = Flask(__name__)
STATIONS_FILE = "radio_stations.json"

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
    "AIR": {
        "fm_gold": {"name": "FM Gold", "url": "https://airhlspush.pc.cdn.bitgravity.com/httppush/hispbaudio005/hispbaudio00564kbps.m3u8"},
        "air_kavarati": {"name": "AIR Kavarati", "url": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio189/chunklist.m3u8"}
    },
    "Islamic": {
        "muthnabi_radio": {"name": "Muthnabi Radio", "url": "http://cast4.my-control-panel.com/proxy/muthnabi/stream"},
        "deenagers_radio": {"name": "Deenagers Radio", "url": "http://104.7.66.64:8003/"}
    },
    "Malayalam": {
        "radio_nellikka": {"name": "Radio Nellikka", "url": "https://usa20.fastcast4u.com:2130/stream"},
        "radio_keralam": {"name": "Radio Keralam", "url": "http://ice31.securenetsystems.net/RADIOKERAL"}
    },
    "Others": {
        "nonstop_hindi": {"name": "Nonstop Hindi", "url": "http://s5.voscast.com:8216/stream"}
    },
    "TV": {
        "safari_tv": {"name": "Safari TV", "url": "https://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/chunks.m3u8"}
    },
    "YouTube": {
        "shajahan_rahmani": {"name": "Shajahan Rahmani", "url": "http://capitalist-anthe-pscj-4a28f285.koyeb.app/shajahan_rahmani"}
    }
}

def load_data(filename):
    if Path(filename).exists():
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_data(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

RADIO_STATIONS = load_data(STATIONS_FILE)

# Auto-populate if empty or missing
if not RADIO_STATIONS:
    RADIO_STATIONS = DEFAULT_STATIONS
    save_data(STATIONS_FILE, RADIO_STATIONS)

@app.route("/<station_id>")
def redirect_stream(station_id):
    for category in RADIO_STATIONS.values():
        if station_id in category:
            return redirect(category[station_id]["url"])
    return "Station not found", 404

@app.route("/delete/<category>/<station_id>", methods=["POST"])
def delete_station(category, station_id):
    if category in RADIO_STATIONS and station_id in RADIO_STATIONS[category]:
        del RADIO_STATIONS[category][station_id]
        if not RADIO_STATIONS[category]:
            del RADIO_STATIONS[category]
        save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

@app.route("/")
def index():
    html_stations = ""
    for category, stations in RADIO_STATIONS.items():
        for sid, station in stations.items():
            display_name = station.get("name", sid.replace("_", " ").title())
            html_stations += f"""
            <div class='station-card' data-category="{category}">
                <div class='station-header'>
                    <span class='station-name' onclick="playStream('/{sid}')">{display_name}</span>
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
            .back-button {{ color:#4CAF50; margin-bottom:10px; cursor:pointer; }}
        </style>
    </head>
    <body>
        <h1>📻 Radio Stations</h1>
        <div id="categories" class="categories">{html_categories}</div>

        <div id="stations-container" style="display:none;">
            <div class="back-button" onclick="showCategories()">← Back</div>
            <div id="stations">{html_stations}</div>
        </div>

        <script>
            function showStations(category) {{
                document.getElementById('categories').style.display = 'none';
                document.getElementById('stations-container').style.display = 'block';
                const cards = document.querySelectorAll('.station-card');
                cards.forEach(card => {{
                    card.style.display = card.dataset.category === category ? 'block' : 'none';
                }});
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)