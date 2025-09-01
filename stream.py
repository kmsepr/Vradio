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
    <head>
        <title>📻 VRadio</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f4f4; text-align: center; }
            h2 { margin-top: 20px; }
            .station { 
                background: #fff; 
                padding: 15px; 
                margin: 10px auto; 
                width: 90%; 
                max-width: 400px; 
                border-radius: 12px; 
                box-shadow: 0 3px 6px rgba(0,0,0,0.2);
            }
            button { 
                padding: 10px 15px; 
                margin: 5px; 
                border: none; 
                border-radius: 8px; 
                font-size: 14px; 
                cursor: pointer;
            }
            .play { background: #4CAF50; color: white; }
            .record { background: #ff9800; color: white; }
            .stop { background: #f44336; color: white; }
        </style>
    </head>
    <body>
        <h2>📻 Flask VRadio</h2>
        {% for name, url in stations.items() %}
        <div class="station">
            <b>{{name}}</b><br>
            <a href="/player?station={{name}}"><button class="play">▶ Play</button></a>
            <a href="/record?station={{name}}"><button class="record">⏺ Record</button></a>
            <a href="/stop"><button class="stop">⏹ Stop</button></a>
        </div>
        {% endfor %}
    </body>
    </html>
    """, stations=RADIO_STATIONS)


# 🎶 Separate play screen
@app.route("/player")
def player():
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404
    return render_template_string("""
    <html>
    <head>
        <title>▶ {{station}}</title>
        <style>
            body { font-family: Arial, sans-serif; background: black; color: white; text-align: center; }
            .container { margin-top: 60px; }
            .timer { font-size: 22px; margin: 10px; }
            audio { width: 90%; max-width: 400px; margin: 20px auto; display: block; }
            button { 
                padding: 12px 18px; 
                margin: 8px; 
                border: none; 
                border-radius: 12px; 
                font-size: 16px; 
                cursor: pointer;
            }
            .stop { background: #f44336; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>{{station}}</h2>
            <div class="timer">
                <span id="current">00:00</span> / <span id="duration">--:--</span>
            </div>
            <audio id="player" controls autoplay>
                <source src="/play?station={{station}}" type="audio/mpeg">
                Your browser does not support audio.
            </audio>
            <br>
            <a href="/stop"><button class="stop">⏹ Stop</button></a>
        </div>

        <script>
            const audio = document.getElementById("player");
            const cur = document.getElementById("current");
            const dur = document.getElementById("duration");

            audio.addEventListener("timeupdate", () => {
                let m = Math.floor(audio.currentTime / 60).toString().padStart(2,'0');
                let s = Math.floor(audio.currentTime % 60).toString().padStart(2,'0');
                cur.textContent = m + ":" + s;
            });

            audio.addEventListener("loadedmetadata", () => {
                if (!isNaN(audio.duration)) {
                    let m = Math.floor(audio.duration / 60).toString().padStart(2,'0');
                    let s = Math.floor(audio.duration % 60).toString().padStart(2,'0');
                    dur.textContent = m + ":" + s;
                } else {
                    dur.textContent = "LIVE";
                }
            });
        </script>
    </body>
    </html>
    """, station=station)


# 🎶 Play stream (raw audio route)
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