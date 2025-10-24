import os
import subprocess
from flask import Flask, Response, render_template_string, request, redirect, url_for, jsonify
from google.cloud import firestore

# -----------------------------
# FIRESTORE SETUP
# -----------------------------
# Path to your downloaded Firebase service account JSON
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/mnt/data/firebase_key.json"
db = firestore.Client()
stations_col = db.collection("radio_stations")

# -----------------------------
# UTILITY FUNCTIONS
# -----------------------------
def get_stations():
    """Return all stations as a dict {name: {url, quality}}"""
    stations = {}
    for doc in stations_col.stream():
        stations[doc.id] = doc.to_dict()
    return stations

def add_station(name, url, quality):
    stations_col.document(name).set({"url": url, "quality": quality})

def delete_station_fs(name):
    stations_col.document(name).delete()

# -----------------------------
# HARD-CODED STATIONS
# -----------------------------
STATIONS = {
    "Radio One": {"url": "http://stream.radio1.com/live", "quality": "medium"},
    "Radio Jornal": {"url": "https://player-ne10-radiojornal-app.stream.uol.com.br/live/radiojornalrecifeapp.m3u8",
    "quality": "medium"},

    "Jazz FM": {"url": "http://stream.jazzfm.com/live", "quality": "best"},
    "Classic Hits": {"url": "http://stream.classichits.com/live", "quality": "small"},
    "News Live": {"url": "http://stream.newslive.com/live", "quality": "medium"},
    "BBC Radio 1": {"url": "http://stream.bbc.co.uk/radio1", "quality": "best"},
    "NRJ France": {"url": "http://stream.nrj.fr", "quality": "medium"},
    "Radio Mirchi": {"url": "http://stream.radiomirchi.com/live", "quality": "best"},
    "Rock Nation": {"url": "http://stream.rocknation.com/live", "quality": "medium"},
    "Pop Central": {"url": "http://stream.popcentral.com/live", "quality": "medium"},
    "Smooth Jazz": {"url": "http://stream.smoothjazz.com/live", "quality": "best"},
    "Country Roads": {"url": "http://stream.countryroads.com/live", "quality": "medium"},
    "Classical Wave": {"url": "http://stream.classicalwave.com/live", "quality": "best"},
    "Electronic Vibes": {"url": "http://stream.electrovibes.com/live", "quality": "medium"},
    "Hip Hop Beats": {"url": "http://stream.hiphopbeats.com/live", "quality": "medium"},
    "Latin Grooves": {"url": "http://stream.latingrooves.com/live", "quality": "best"},
    "Oldies 80s": {"url": "http://stream.oldies80s.com/live", "quality": "small"},
    "News 24/7": {"url": "http://stream.news247.com/live", "quality": "medium"},
    "Relax FM": {"url": "http://stream.relaxfm.com/live", "quality": "best"},
    "Tech Talk Radio": {"url": "http://stream.techtalk.com/live", "quality": "medium"},
    "Global Hits": {"url": "http://stream.globalhits.com/live", "quality": "medium"},
    "Soul Station": {"url": "http://stream.soulstation.com/live", "quality": "best"},
    "Indie Wave": {"url": "http://stream.indiewave.com/live", "quality": "medium"},
    "Sports Radio": {"url": "http://stream.sportsradio.com/live", "quality": "medium"},
    "Morning FM": {"url": "http://stream.morningfm.com/live", "quality": "best"},
    "Evening Chill": {"url": "http://stream.eveningchill.com/live", "quality": "small"}
}

# Insert stations into Firestore if not already present
for name, info in STATIONS.items():
    if not stations_col.document(name).get().exists:
        add_station(name, info["url"], info["quality"])

# -----------------------------
# FLASK APP
# -----------------------------
app = Flask(__name__)

# -----------------------------
# HOME PAGE
# -----------------------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()
        quality = request.form.get("quality", "medium")
        if name and url:
            add_station(name, url, quality)
        return redirect(url_for("home"))

    stations = get_stations()
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
        <h3>🎶 Created stations</h3>
        {% for name, info in stations.items() %}
        <div class="station">
            <a href="{{ url_for('play_station', name=name) }}">{{ name }}</a><br>
            <button class="copy-btn" onclick="copyURL('{{ name }}', '{{ info.quality }}')">Copy URL</button>
            <button class="del-btn" onclick="deleteStation('{{ name }}')">Delete</button>
        </div>
        {% else %}
        <p>No stations yet.</p>
        {% endfor %}
    </body>
    </html>
    """
    return render_template_string(html, stations=stations)

# -----------------------------
# DELETE STATION
# -----------------------------
@app.route("/delete/<name>", methods=["POST"])
def delete_station(name):
    delete_station_fs(name)
    return jsonify({"status": "deleted"})

# -----------------------------
# STREAM ROUTE (AUDIO ONLY)
# -----------------------------
@app.route("/stream/<name>")
def play_station(name):
    stations = get_stations()
    if name not in stations:
        return "Station not found", 404

    info = stations[name]
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
# MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, threaded=True)
