import os
import json
import subprocess
import logging
from flask import Flask, Response, render_template_string, request, redirect, url_for, send_file, jsonify

# -----------------------------
# CONFIG & LOGGING
# -----------------------------
LOG_PATH = "/mnt/data/radio.log"
STATIONS_JSON = "/mnt/data/stations.json"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)

# -----------------------------
# LOAD/SAVE STATIONS
# -----------------------------
def load_stations():
    if os.path.exists(STATIONS_JSON):
        try:
            with open(STATIONS_JSON, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_stations(data):
    with open(STATIONS_JSON, "w") as f:
        json.dump(data, f, indent=2)

STATIONS = load_stations()

# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    global STATIONS
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()
        quality = request.form.get("quality", "medium")
        if name and url:
            STATIONS[name] = {"url": url, "quality": quality}
            save_stations(STATIONS)
        return redirect(url_for("home"))

    html = """
    <!doctype html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Radio Home</title>
        <style>
            body { font-family: sans-serif; text-align:center; background:#111; color:#eee; }
            input, select, button { padding:6px; margin:4px; border-radius:8px; border:none; }
            input, select { width:70%; max-width:250px; }
            .station { background:#222; margin:6px auto; padding:10px; border-radius:10px; width:90%; max-width:300px; }
            .copy-btn, .del-btn { margin-top:5px; background:#444; color:#fff; border:none; padding:6px 10px; border-radius:8px; }
            .copy-btn:hover, .del-btn:hover { background:#666; }
            a { color:#4cf; text-decoration:none; }
        </style>
        <script>
        function copyURL(station, quality){
            const url = window.location.origin + '/stream/' + encodeURIComponent(station) + '?quality=' + quality;
            navigator.clipboard.writeText(url).then(()=>{
                alert('Copied: ' + url);
            });
        }
        function deleteStation(name){
            if(confirm('Delete ' + name + '?')){
                fetch('/delete/' + encodeURIComponent(name), {method:'POST'})
                .then(()=>location.reload());
            }
        }
        </script>
    </head>
    <body>
        <h2>📻 Add Station</h2>
        <form method="post">
            <input name="name" placeholder="Station Name" required><br>
            <input name="url" placeholder="Stream URL" required><br>
            <select name="quality">
                <option value="small">Small (32kbps)</option>
                <option value="medium" selected>Medium (64kbps)</option>
                <option value="best">Best (128kbps)</option>
            </select><br>
            <button type="submit">Add Station</button>
        </form>
        <h3>🎶 Your Stations</h3>
        {% for name, info in stations.items() %}
        <div class="station">
            <a href="{{ url_for('play_station', name=name) }}">{{ name }}</a><br>
            <button class="copy-btn" onclick="copyURL('{{ name }}', '{{ info.quality }}')">Copy URL</button>
            <button class="del-btn" onclick="deleteStation('{{ name }}')">Delete</button>
        </div>
        {% else %}
        <p>No stations yet.</p>
        {% endfor %}
        <br>
        <a href="{{ url_for('backup_json') }}">📦 Download Backup (stations.json)</a>
    </body>
    </html>
    """
    return render_template_string(html, stations=STATIONS)

# -----------------------------
# DELETE STATION
# -----------------------------
@app.route("/delete/<name>", methods=["POST"])
def delete_station(name):
    global STATIONS
    if name in STATIONS:
        del STATIONS[name]
        save_stations(STATIONS)
        return jsonify({"status": "deleted"})
    return jsonify({"error": "not found"}), 404

# -----------------------------
# STREAM ROUTE (AUDIO ONLY)
# -----------------------------
@app.route("/stream/<name>")
def play_station(name):
    if name not in STATIONS:
        return "Station not found", 404

    info = STATIONS[name]
    audio_url = info["url"]
    quality = request.args.get("quality", info.get("quality", "medium"))

    bitrate = {"small": "32k", "medium": "64k", "best": "128k"}.get(quality, "64k")

    def generate():
        cmd = [
            "ffmpeg", "-re", "-i", audio_url,
            "-b:a", bitrate, "-ac", "1", "-f", "mp3", "pipe:1", "-loglevel", "quiet"
        ]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        try:
            for chunk in iter(lambda: process.stdout.read(4096), b""):
                yield chunk
        finally:
            process.terminate()

    return Response(generate(), mimetype="audio/mpeg")

# -----------------------------
# BACKUP JSON
# -----------------------------
@app.route("/backup")
def backup_json():
    if not os.path.exists(STATIONS_JSON):
        return jsonify({"error": "No stations file found"}), 404
    return send_file(STATIONS_JSON, as_attachment=True)

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)