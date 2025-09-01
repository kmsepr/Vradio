import subprocess
import shutil
from flask import Flask, Response, request, render_template_string

app = Flask(__name__)

# ✅ Check if ffmpeg is installed
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Example radio stations
RADIO_STATIONS = {
    "Muthnabi Radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "Kuran Radio": "http://qurango.net/radio/mishary",
}

# Track FFmpeg processes
ffmpeg_process = None
record_process = None


@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head>
        <title>Radio Stream</title>
    </head>
    <body>
        <h2>📻 Radio Streaming</h2>
        <ul>
        {% for name, url in stations.items() %}
            <li>
                {{name}} 
                <a href="/play?url={{url}}">▶️ Play</a>
                <a href="/record?url={{url}}">⏺️ Record</a>
            </li>
        {% endfor %}
        </ul>
        <br>
        <a href="/stop">⏹️ Stop All</a>
    </body>
    </html>
    """, stations=RADIO_STATIONS)


@app.route("/play")
def play():
    global ffmpeg_process, record_process
    url = request.args.get("url")

    # Stop previous play/record
    stop_all()

    # Start playback only
    ffmpeg_process = subprocess.Popen([
        "ffmpeg", "-i", url,
        "-c", "copy", "-f", "mp3",
        "pipe:1"
    ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def generate():
        while True:
            data = ffmpeg_process.stdout.read(1024)
            if not data:
                break
            yield data

    return Response(generate(), mimetype="audio/mpeg")


@app.route("/record")
def record():
    global ffmpeg_process, record_process
    url = request.args.get("url")

    # Stop previous play/record
    stop_all()

    # Start recording without metadata
    record_process = subprocess.Popen([
        "ffmpeg", "-i", url,
        "-map_metadata", "-1",  # 🚫 Remove metadata
        "-c", "copy", f"recording.mp3"
    ], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    # Also play while recording
    ffmpeg_process = subprocess.Popen([
        "ffmpeg", "-i", url,
        "-c", "copy", "-f", "mp3",
        "pipe:1"
    ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def generate():
        while True:
            data = ffmpeg_process.stdout.read(1024)
            if not data:
                break
            yield data

    return Response(generate(), mimetype="audio/mpeg")


@app.route("/stop")
def stop():
    stop_all()
    return "⏹️ Stopped playback & recording"


def stop_all():
    global ffmpeg_process, record_process
    if ffmpeg_process:
        ffmpeg_process.kill()
        ffmpeg_process = None
    if record_process:
        record_process.kill()
        record_process = None


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)