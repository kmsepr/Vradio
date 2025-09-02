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


# ▶️ Play (with optional recording)
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
            ["ffmpeg", "-i", url, "-map_metadata", "-1", "-f", "mp3", "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )

    def generate():
        while True:
            chunk = ffmpeg_process.stdout.read(1024)
            if not chunk:
                break
            yield chunk

    return Response(generate(), mimetype="audio/mpeg")


# ⏺️ Toggle recording (reuse /play)
@app.route("/record")
def record():
    station = request.args.get("station")
    if not station or station not in RADIO_STATIONS:
        return jsonify({"status": "error", "message": "Station not found"}), 404

    # Restart /play with record=1
    return jsonify({"status": "recording", "url": f"/play?station={station}&record=1"})


# 📏 Recording size
@app.route("/record_size")
def record_size():
    global record_file, ffmpeg_process
    if record_file and os.path.exists(record_file) and ffmpeg_process:
        size = os.path.getsize(record_file) // 1024
        return jsonify({"size": size, "active": True, "file": record_file})
    return jsonify({"size": 0, "active": False})


# ⏹️ Stop recording (but keep playback)
@app.route("/stop_record")
def stop_record():
    global record_file
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


# 🖥️ Simple UI
@app.route("/")
def index():
    return render_template_string("""
    <html>
    <head><title>Radio Stream</title></head>
    <body>
        <h2>📻 Radio Player</h2>
        <audio id="player" controls autoplay></audio><br>
        
        <button onclick="play('muthnabi_radio')">▶️ Play Muthnabi</button>
        <button onclick="play('example_fm')">▶️ Play Example</button>
        <button onclick="stop()">⏹ Stop</button>
        <button onclick="record('muthnabi_radio')">⏺ Record</button>
        <button onclick="stopRecord()">💾 Stop & Download</button>

        <script>
        function play(station){
            document.getElementById("player").src = "/play?station="+station;
        }
        function stop(){
            fetch("/stop").then(()=>document.getElementById("player").src="");
        }
        function record(station){
            fetch("/record?station="+station)
            .then(r=>r.json()).then(d=>{
                if(d.url){
                    document.getElementById("player").src = d.url;
                }
            });
        }
        function stopRecord(){
            window.location = "/stop_record";
        }
        </script>
    </body>
    </html>
    """)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)