import subprocess
import shutil
import os
from flask import Flask, Response, request, render_template_string

app = Flask(__name__)

# ✅ Check if ffmpeg is available
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Radio stations
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "islam_radio": "http://live.radioislam.org.za:8000/;stream.mp3",
    "calicut_radio": "http://radio.garden/api/ara/content/listen/xyz123",  # example
}

current_process = None
current_station = None
recording_process = None

# 🏠 Home screen
@app.route("/")
def home():
    html = """
    <h1>📻 Flask Radio Recorder</h1>
    <p>Select a station to Play or Record:</p>
    <ul>
    {% for name, url in stations.items() %}
        <li>
            <b>{{ name }}</b> 
            [<a href="/play/{{ name }}">▶️ Play</a>] 
            [<a href="/record/{{ name }}">⏺️ Record</a>] 
            [<a href="/stop">⏹️ Stop</a>]
        </li>
    {% endfor %}
    </ul>
    """
    return render_template_string(html, stations=RADIO_STATIONS)


# 🎶 Play route
@app.route("/play/<station>")
def play(station):
    global current_process, current_station

    if station not in RADIO_STATIONS:
        return "Station not found", 404

    url = RADIO_STATIONS[station]

    def generate():
        global current_process
        if current_process:
            current_process.kill()
        # 🔊 Play without metadata
        current_process = subprocess.Popen(
            ["ffmpeg", "-i", url, "-f", "mp3", "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        while True:
            chunk = current_process.stdout.read(1024)
            if not chunk:
                break
            yield chunk

    current_station = station
    return Response(generate(), mimetype="audio/mpeg")


# ⏺️ Record route (while listening)
@app.route("/record/<station>")
def record(station):
    global recording_process

    if station not in RADIO_STATIONS:
        return "Station not found", 404

    url = RADIO_STATIONS[station]
    filename = f"{station}.mp3"

    if recording_process:
        recording_process.kill()

    # 🎤 Record exactly what’s playing, no metadata
    recording_process = subprocess.Popen(
        ["ffmpeg", "-i", url, "-f", "mp3", filename],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return f"Recording started: {filename}"


# ⏹️ Stop everything
@app.route("/stop")
def stop():
    global current_process, recording_process
    if current_process:
        current_process.kill()
        current_process = None
    if recording_process:
        recording_process.kill()
        recording_process = None
    return "Stopped."


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)