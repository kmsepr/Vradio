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
    "muthnabi_radio": "http://cast4.my-control-panel.com:8084/stream",
    "example_fm": "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"
}

# 🎵 Global variables
ffmpeg_process = None
record_file = None


# ▶️ Play (with optional recording using tee)
@app.route("/play")
def play():
    global ffmpeg_process, record_file

    station = request.args.get("station")
    record = request.args.get("record", "0") == "1"

    if station not in RADIO_STATIONS:
        return "Station not found", 404

    # Stop old process
    if ffmpeg_process:
        ffmpeg_process.kill()
        ffmpeg_process = None

    url = RADIO_STATIONS[station]

    if record:
        os.makedirs("recordings", exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        record_file = f"recordings/{station}_{timestamp}.mp3"

        ffmpeg_process = subprocess.Popen(
            [
                "ffmpeg", "-i", url,
                "-map_metadata", "-1",
                "-c:a", "libmp3lame", "-b:a", "128k",
                "-f", "tee",
                f"[f=mp3]pipe:1|[f=mp3]{record_file}"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
    else:
        record_file = None
        ffmpeg_process = subprocess.Popen(
            ["ffmpeg", "-i", url, "-map_metadata", "-1", "-f", "mp3", "pipe:1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )

    def generate():
        while True:
            chunk = ffmpeg_process.stdout.read(4096)  # bigger buffer
            if not chunk:
                break
            yield chunk

    return Response(generate(), mimetype="audio/mpeg")


# ⏹️ Stop all playback
@app.route("/stop")
def stop():
    global ffmpeg_process
    if ffmpeg_process:
        ffmpeg_process.kill()
        ffmpeg_process = None
    return "⏹️ Stopped playback"


# 💾 Stop & download recording
@app.route("/stop_record")
def stop_record():
    global record_file
    if record_file and os.path.exists(record_file):
        return send_file(record_file, as_attachment=True)
    return "No recording found", 404


# 🖥️ Simple UI
@app.route("/")
def index():
    return render_template_string("""
    <html>
    <head><title>Radio Stream</title></head>
    <body>
        <h2>📻 Radio Player</h2>
        <audio id="player" controls autoplay></audio><br>
        
        <button onclick="playStation('muthnabi_radio', false)">▶️ Play Muthnabi</button>
        <button onclick="playStation('example_fm', false)">▶️ Play Example</button>
        <button onclick="stopPlayback()">⏹ Stop</button>
        <button onclick="playStation('muthnabi_radio', true)">⏺ Record</button>
        <button onclick="stopRecord()">💾 Stop & Download</button>

        <script>
        function playStation(station, record){
            const audio = document.getElementById("player");
            audio.src = "/play?station=" + station + "&record=" + (record ? "1" : "0") + "&t=" + Date.now();
            audio.play();
        }
        function stopPlayback(){
            fetch("/stop").then(()=>document.getElementById("player").src="");
        }
        function stopRecord(){
            window.location = "/stop_record";
        }
        </script>
    </body>
    </html>
    """)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)