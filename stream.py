import subprocess
import shutil
import os
from datetime import datetime
from flask import Flask, Response, request, render_template_string

app = Flask(__name__)

# ✅ Check ffmpeg
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Radio stations
RADIO_STATIONS = {
    "Muthnabi Radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "Kuran Radio": "http://qurango.net/radio/mishary",
}

# Track FFmpeg processes
ffmpeg_process = None
record_process = None
current_station = None

# 🏠 Home screen
@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head><title>📻 Flask VRadio</title></head>
    <body>
        <h2>📻 Radio Streaming</h2>
        <ul>
        {% for name, url in stations.items() %}
            <li>
                <b>{{name}}</b> 
                [<a href="/play?station={{name}}">▶️ Play</a>] 
                [<a href="/record?station={{name}}">⏺️ Record</a>] 
            </li>
        {% endfor %}
        </ul>
        <br>
        <a href="/stop">⏹️ Stop All</a>
    </body>
    </html>
    """, stations=RADIO_STATIONS)


# 🎶 Play route
@app.route("/play")
def play():
    global ffmpeg_process, record_process, current_station
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404

    url = RADIO_STATIONS[station]

    # Stop previous playback
    if ffmpeg_process:
        ffmpeg_process.kill()

    current_station = station

    # Stream audio to browser
    ffmpeg_process = subprocess.Popen(
        ["ffmpeg", "-i", url, "-c", "copy", "-f", "mp3", "pipe:1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    def generate():
        while True:
            data = ffmpeg_process.stdout.read(1024)
            if not data:
                break
            yield data

    return Response(generate(), mimetype="audio/mpeg")


# ⏺️ Record route
@app.route("/record")
def record():
    global record_process, current_station

    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404

    url = RADIO_STATIONS[station]

    # Make recordings folder
    os.makedirs("recordings", exist_ok=True)

    # Timestamped filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"recordings/{station.replace(' ', '_')}_{timestamp}.mp3"

    # Stop previous recording
    if record_process:
        record_process.kill()

    # Start robust recording without metadata
    record_process = subprocess.Popen(
        ["ffmpeg", "-i", url, "-map_metadata", "-1", "-c", "copy", filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return f"⏺️ Recording started: {filename}"


# ⏹️ Stop all playback & recording
@app.route("/stop")
def stop():
    global ffmpeg_process, record_process
    if ffmpeg_process:
        ffmpeg_process.kill()
        ffmpeg_process = None
    if record_process:
        record_process.kill()
        record_process = None
    return "⏹️ Stopped playback & recording"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)