import subprocess
import shutil
import os
from datetime import datetime
from flask import Flask, Response, request, send_file, jsonify, render_template_string

app = Flask(__name__)

# ---------------- CHECK FFMPEG ----------------
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# ---------------- RADIO STATIONS ----------------
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
     "radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",

"air_kavarati": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio189/chunklist.m3u8",
    "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
    "manjeri_fm": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio101/chunklist.m3u8",
    "real_fm": "http://air.pc.cdn.bitgravity.com/air/live/pbaudio083/playlist.m3u8",
    "safari_tv": "https://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/chunks.m3u8",
    "victers_tv": "https://932y4x26ljv8-hls-live.5centscdn.com/victers/tv.stream/victers/tv1/chunks.m3u8",
}

# ---------------- GLOBAL VARIABLES ----------------
play_process = None
record_process = None
record_file = None

# ---------------- CONTROL PAGE ----------------
@app.route("/")
def index():
    stations_html = "".join([f"<option value='{s}'>{s}</option>" for s in RADIO_STATIONS])
    html = f"""
    <html>
    <head><title>Radio Stream</title></head>
    <body style="font-family: Arial; text-align:center; margin-top:40px;">
        <h2>📻 Radio Streamer</h2>
        <label>Select Station:</label>
        <select id="station">{stations_html}</select><br><br>

        <button onclick="play()">▶️ Play</button>
        <button onclick="stop()">⏹ Stop</button>
        <button onclick="record()">⏺ Record</button>
        <button onclick="stopRecord()">💾 Stop & Download</button>

        <p id="status"></p>
        <audio id="player" controls autoplay></audio>

        <script>
        function play() {{
            let s = document.getElementById("station").value;
            document.getElementById("player").src = "/play?station=" + s;
            document.getElementById("status").innerText = "Playing " + s;
        }}
        function stop() {{
            fetch("/stop").then(r => r.json()).then(data => {{
                document.getElementById("player").src = "";
                document.getElementById("status").innerText = data.status;
            }});
        }}
        function record() {{
            let s = document.getElementById("station").value;
            fetch("/record?station=" + s).then(r => r.json()).then(data => {{
                document.getElementById("status").innerText = "Recording...";
            }});
        }}
        function stopRecord() {{
            window.location.href = "/stop_record";
        }}
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


# ---------------- PLAYBACK ----------------
@app.route("/play")
def play():
    global play_process
    station = request.args.get("station")

    if not station or station not in RADIO_STATIONS:
        return "Station not found", 400

    if play_process:
        play_process.kill()

    url = RADIO_STATIONS[station]
    play_process = subprocess.Popen([
        "ffmpeg", "-i", url, "-vn", "-f", "mp3", "pipe:1"
    ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def generate():
        while True:
            chunk = play_process.stdout.read(1024)
            if not chunk:
                break
            yield chunk

    return Response(generate(), mimetype="audio/mpeg")


@app.route("/stop")
def stop():
    global play_process
    if play_process:
        play_process.kill()
        play_process = None
    return jsonify({"status": "stopped playback"})


# ---------------- RECORDING ----------------
@app.route("/record")
def record():
    global record_process, record_file
    station = request.args.get("station")

    if not station or station not in RADIO_STATIONS:
        return jsonify({"error": "Station not found"}), 400

    os.makedirs("recordings", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    record_file = f"recordings/{station}_{ts}.mp3"
    url = RADIO_STATIONS[station]

    if record_process:
        record_process.terminate()

    record_process = subprocess.Popen([
        "ffmpeg", "-i", url, "-vn", "-acodec", "libmp3lame", record_file
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return jsonify({"status": "recording", "file": record_file})


@app.route("/record_size")
def record_size():
    global record_file
    if not record_file or not os.path.exists(record_file):
        return jsonify({"size": 0})
    size_kb = os.path.getsize(record_file) // 1024
    return jsonify({"size": size_kb})


@app.route("/stop_record")
def stop_record():
    global record_process, record_file
    if record_process:
        record_process.terminate()
        record_process = None

    if record_file and os.path.exists(record_file):
        return send_file(record_file, as_attachment=True)

    return "No recording found", 404


# ---------------- MAIN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)