import subprocess
import time
from flask import Flask, Response, redirect, request, send_from_directory
import os
import json
from pathlib import Path
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
STATIONS_FILE = "radio_stations.json"
THUMBNAILS_FILE = "station_thumbnails.json"
UPLOAD_FOLDER = 'static/logos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Get base URL from environment or use empty string
BASE_URL = os.getenv('BASE_URL', '')

# Initialize with default stations (using relative paths)
DEFAULT_STATIONS = {
    "muthnabi_radio": "/proxy/muthnabi/stream",
    "radio_keralam": "/RADIOKERAL",
    # ... other stations with relative paths ...
}

DEFAULT_THUMBNAILS = {
    "muthnabi_radio": "/static/default-radio.png",
    "radio_keralam": "/static/default-radio.png",
    # ... other thumbnails ...
}

def load_data(filename, default_data):
    """Load data from file or use defaults"""
    try:
        if Path(filename).exists():
            with open(filename, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading {filename}: {e}")
    return default_data

def save_data(filename, data):
    """Save data to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"⚠️ Error saving {filename}: {e}")

# Load data at startup
RADIO_STATIONS = load_data(STATIONS_FILE, DEFAULT_STATIONS)
STATION_THUMBNAILS = load_data(THUMBNAILS_FILE, DEFAULT_THUMBNAILS)

# 🔁 FFmpeg stream generator with transcoding
def generate_stream(relative_path):
    """Generate 64k mono MP3 stream from relative path"""
    full_url = f"http://your-stream-server.com{relative_path}"  # Configure this at deployment
    process = None
    while True:
        if process:
            process.kill()
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10",
                "-i", full_url,
                "-vn", "-ac", "1", "-b:a", "64k", "-f", "mp3", "-"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=8192
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

# 🎧 Stream endpoint
@app.route("/<station_name>")
def stream(station_name):
    relative_path = RADIO_STATIONS.get(station_name)
    if not relative_path:
        return "⚠️ Station not found", 404
    return Response(generate_stream(relative_path), mimetype="audio/mpeg")

# ➕ Add new station
@app.route("/add", methods=["POST"])
def add_station():
    name = request.form.get("name", "").strip().lower().replace(" ", "_")
    url = request.form.get("url", "").strip()

    # Handle logo upload
    logo_url = STATION_THUMBNAILS.get(name, "/static/default-radio.png")
    logo = request.files.get("logo")
    if logo and logo.filename:
        filename = secure_filename(f"{name}_{logo.filename}")
        logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        logo_url = f"/static/logos/{filename}"

    if name and url:
        RADIO_STATIONS[name] = url
        STATION_THUMBNAILS[name] = logo_url
        save_data(STATIONS_FILE, RADIO_STATIONS)
        save_data(THUMBNAILS_FILE, STATION_THUMBNAILS)
    return redirect("/")

# ✏️ Edit station
@app.route("/edit/<old_name>", methods=["POST"])
def edit_station(old_name):
    new_name = request.form.get("name", "").strip().lower().replace(" ", "_")
    new_url = request.form.get("url", "").strip()

    if not new_name or not new_url:
        return redirect("/")

    # Handle logo update
    logo = request.files.get("logo")
    logo_url = STATION_THUMBNAILS.get(old_name, "/static/default-radio.png")
    if logo and logo.filename:
        filename = secure_filename(f"{new_name}_{logo.filename}")
        logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        logo_url = f"/static/logos/{filename}"

    # Update station data
    if old_name in RADIO_STATIONS:
        if old_name != new_name:
            RADIO_STATIONS[new_name] = RADIO_STATIONS.pop(old_name)
        else:
            RADIO_STATIONS[new_name] = new_url

        STATION_THUMBNAILS[new_name] = logo_url
        if old_name != new_name and old_name in STATION_THUMBNAILS:
            del STATION_THUMBNAILS[old_name]

        save_data(STATIONS_FILE, RADIO_STATIONS)
        save_data(THUMBNAILS_FILE, STATION_THUMBNAILS)

    return redirect("/")

# 🗑️ Delete station
@app.route("/delete/<station_name>", methods=["POST"])
def delete_station(station_name):
    if station_name in RADIO_STATIONS:
        del RADIO_STATIONS[station_name]
        if station_name in STATION_THUMBNAILS:
            del STATION_THUMBNAILS[station_name]
        save_data(STATIONS_FILE, RADIO_STATIONS)
        save_data(THUMBNAILS_FILE, STATION_THUMBNAILS)
    return redirect("/")

# 🏠 Homepage UI - Now shows only transcoded URLs
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
            <img src='{STATION_THUMBNAILS.get(name, "/static/default-radio.png")}' class='station-thumbnail'>
            <div class='station-info'>
                <a href='{BASE_URL}/{name}'>{name.replace('_', ' ').title()}</a>
                <div class='card-buttons'>
                    <button class="edit-btn" onclick="openEditModal('{name}', '{RADIO_STATIONS[name]}')">✏️</button>
                    <button class="fav-btn" onclick="toggleFavourite('{name}')">⭐</button>
                    <form method='POST' action='/delete/{name}' style='display:inline;'>
                        <button type='submit' class='delete-btn'>🗑️</button>
                    </form>
                </div>
            </div>
        </div>
        """ for i, name in enumerate(reversed(list(RADIO_STATIONS)))
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <!-- [Previous HTML/CSS/JS remains exactly the same] -->
    </html>
    """

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == "__main__":
    # Create storage files if they don't exist
    if not Path(STATIONS_FILE).exists():
        save_data(STATIONS_FILE, DEFAULT_STATIONS)
    if not Path(THUMBNAILS_FILE).exists():
        save_data(THUMBNAILS_FILE, DEFAULT_THUMBNAILS)

    # Create default radio image if missing
    default_logo_path = Path('static/default-radio.png')
    if not default_logo_path.exists():
        os.makedirs('static', exist_ok=True)
        # Add a real default image here

    app.run(host="0.0.0.0", port=8000)