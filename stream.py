import subprocess
import time
from flask import Flask, Response, redirect, request
import json
import os
from pathlib import Path

app = Flask(__name__)

STATIONS_FILE = "radio_stations.json"
DEFAULT_STATIONS = {
    "News": {
        "al_jazeera": "http://live-hls-audio-web-aja.getaj.net/VOICE-AJA",
        "asianet_news": "https://vidcdn.vidgyor.com/asianet-origin/audioonly/chunks.m3u8"
    },
    "Islamic": {
        "deenagers_radio": "http://104.7.66.64:8003/"
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

@app.route("/<category>/<station_name>")
def stream(category, station_name):
    if category in RADIO_STATIONS and station_name in RADIO_STATIONS[category]:
        url = RADIO_STATIONS[category][station_name]
        return Response(generate_stream(url), mimetype="audio/mpeg")
    return "Station not found", 404

@app.route("/delete/<category>/<station_name>", methods=["POST"])
def delete_station(category, station_name):
    if category in RADIO_STATIONS and station_name in RADIO_STATIONS[category]:
        del RADIO_STATIONS[category][station_name]
        if not RADIO_STATIONS[category]:
            del RADIO_STATIONS[category]
        save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

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
                <span class='station-name' onclick="playStream('/{category}/{name}')">{name.replace('_', ' ').title()}</span>
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
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #1e1e2f;
                color: white;
            }}
            .categories {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }}
            .category-card {{
                background: #2b2b3c;
                padding: 15px;
                border-radius: 8px;
                cursor: pointer;
            }}
            .stations-container {{
                display: none;
            }}
            .stations {{
                display: grid;
                gap: 10px;
            }}
            .station-card {{
                background: #2b2b3c;
                padding: 15px;
                border-radius: 8px;
            }}
            .station-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .station-name {{
                color: #4CAF50;
                font-weight: bold;
                cursor: pointer;
            }}
            button {{
                background: none;
                border: 1px solid #444;
                color: white;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
            }}
            .back-button {{
                margin-bottom: 10px;
                cursor: pointer;
                color: #4CAF50;
            }}
            form {{
                margin-top: 40px;
            }}
            input {{
                width: 100%;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 5px;
                border: none;
            }}
            .submit-btn {{
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <h1>Radio</h1>

        <div id="categories" class="categories">{categories_html}</div>

        <div id="stations-container" class="stations-container">
            <div class="back-button" onclick="showCategories()">← Back</div>
            <div id="stations" class="stations"></div>
        </div>

        <h2>Add New Station</h2>
        <form method="POST" action="/add">
            <input name="category" placeholder="Category (e.g. News)" required>
            <input name="name" placeholder="Station Name" required>
            <input name="url" placeholder="Stream URL (http://...)" required>
            <button type="submit" class="submit-btn">Add Station</button>
        </form>

        <script>
            const allStationsHTML = `{stations_html}`;

            function showStations(category) {{
                document.getElementById('categories').style.display = 'none';
                document.getElementById('stations-container').style.display = 'block';
                const container = document.getElementById('stations');
                container.innerHTML = '';
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = allStationsHTML;
                const items = tempDiv.querySelectorAll(`.station-card[data-category='${{category}}']`);
                items.forEach(el => container.appendChild(el.cloneNode(true)));
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
    if not Path(STATIONS_FILE).exists():
        save_data(STATIONS_FILE, DEFAULT_STATIONS)
    app.run(host="0.0.0.0", port=8000, threaded=True)