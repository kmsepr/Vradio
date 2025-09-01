import subprocess
import shutil
import os
from datetime import datetime
from flask import Flask, Response, request, render_template_string, send_file, jsonify

app = Flask(__name__)

# ✅ Check ffmpeg
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Radio stations
RADIO_STATIONS = {
    "Muthnabi Radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "Kuran Radio": "http://qurango.net/radio/mishary",
}

# Track processes
ffmpeg_process = None
record_process = None
current_station = None
record_file = None


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
                background: #4CAF50; 
                color: white;
            }
        </style>
    </head>
    <body>
        <h2>📻 Flask VRadio</h2>
        {% for name in stations.keys() %}
        <div class="station">
            <b>{{name}}</b><br>
            <a href="/player?station={{name}}"><button>▶ Select</button></a>
        </div>
        {% endfor %}
    </body>
    </html>
    """, stations=RADIO_STATIONS)


# 🎶 Player screen
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
            audio { width: 90%; max-width: 400px; margin: 20px auto; display: block; }
            button { padding: 12px 18px; margin: 8px; border: none; border-radius: 12px; font-size: 16px; cursor: pointer; }
            .record { background: #ff9800; color: white; }
            .stop { background: #f44336; color: white; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>{{station}}</h2>
            <audio controls autoplay>
                <source src="/play?station={{station}}" type="audio/mpeg">
                Your browser does not support audio.
            </audio>
            <br>
            <a href="/record?station={{station}}" target="_blank"><button class="record">⏺ Record</button></a>
        </div>
    </body>
    </html>
    """, station=station)


# 🎶 Stream playback
@app.route("/play")
def play():
    global ffmpeg_process, current_station
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


# ⏺️ Record screen
@app.route("/record")
def record():
    global record_process, record_file

    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404

    url = RADIO_STATIONS[station]

    os.makedirs("recordings", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    record_file = f"recordings/{station.replace(' ', '_')}_{timestamp}.mp3"

    # Stop previous recording
    if record_process:
        record_process.kill()

    record_process = subprocess.Popen(
        ["ffmpeg", "-i", url, "-map_metadata", "-1", "-c", "copy", record_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return render_template_string("""
    <html>
    <head>
        <title>⏺ Recording</title>
        <style>
            body { font-family: Arial, sans-serif; background: black; color: white; text-align: center; }
            .container { margin-top: 60px; }
            .status { font-size: 18px; margin: 15px; }
            button { padding: 12px 18px; margin: 8px; border: none; border-radius: 12px; font-size: 16px; cursor: pointer; background: #f44336; color: white; }
        </style>
        <script>
            async function updateSize() {
                let res = await fetch('/record_size');
                let data = await res.json();
                document.getElementById("size").innerText = data.size + " KB";
                if (data.active) {
                    setTimeout(updateSize, 1000);
                }
            }
            updateSize();
        </script>
    </head>
    <body>
        <div class="container">
            <h2>⏺ Recording: {{station}}</h2>
            <div class="status">File Size: <span id="size">0 KB</span></div>
            <a href="/stop_record"><button>⏹ Stop Recording</button></a>
        </div>
    </body>
    </html>
    """, station=station)


# 📏 Recording size API
@app.route("/record_size")
def record_size():
    global record_file, record_process
    if record_file and os.path.exists(record_file) and record_process:
        size = os.path.getsize(record_file) // 1024
        return jsonify({"size": size, "active": True})
    return jsonify({"size": 0, "active": False})


# ⏹️ Stop recording and download
@app.route("/stop_record")
def stop_record():
    global record_process, record_file
    if record_process:
        record_process.kill()
        record_process = None
    if record_file and os.path.exists(record_file):
        return send_file(record_file, as_attachment=True)
    return "No recording found", 404


# ⏹️ Stop all playback
@app.route("/stop")
def stop():
    global ffmpeg_process
    if ffmpeg_process:
        ffmpeg_process.kill()
        ffmpeg_process = None
    return "⏹️ Stopped playback"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)