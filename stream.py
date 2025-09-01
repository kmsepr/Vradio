import os
import shutil
import subprocess
import threading
from datetime import datetime
from flask import Flask, Response, request, render_template_string, jsonify
from queue import Queue

app = Flask(__name__)

# ✅ Check ffmpeg
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Your stations list (add more yourself)
RADIO_STATIONS = {
    "Muthnabi Radio": "https://example.com/muthnabi.m3u8",
    "Peace FM": "https://example.com/peace.m3u8",
    "Islamic Voice": "https://example.com/voice.m3u8",
}

# 🔊 Global state
clients = []
current_station = None
ffmpeg_thread = None
recording = False
record_file = None


def ffmpeg_worker(station_url):
    """Run ffmpeg, feed audio to clients + recorder."""
    global recording, record_file

    command = [
        "ffmpeg", "-i", station_url,
        "-vn",
        "-acodec", "libmp3lame", "-ac", "1", "-ar", "44100", "-b:a", "64k",
        "-f", "mp3", "pipe:1"
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    for chunk in iter(lambda: process.stdout.read(4096), b""):
        # Send to connected clients
        for q in clients[:]:
            try:
                q.put(chunk, timeout=0.1)
            except:
                clients.remove(q)
        # Save if recording
        if recording and record_file:
            record_file.write(chunk)


def start_ffmpeg(station_url):
    """Ensure ffmpeg is running for selected station."""
    global ffmpeg_thread
    if not ffmpeg_thread or not ffmpeg_thread.is_alive():
        ffmpeg_thread = threading.Thread(target=ffmpeg_worker, args=(station_url,), daemon=True)
        ffmpeg_thread.start()


@app.route("/")
def index():
    station_links = "".join(
        f"<li><a href='/set_station?name={name}'>{name}</a></li>"
        for name in RADIO_STATIONS.keys()
    )
    return render_template_string("""
    <html>
    <head>
        <title>Radio Player</title>
        <style>
            body { font-family: sans-serif; text-align: center; padding: 20px; }
            button { font-size: 18px; margin: 5px; padding: 10px; }
        </style>
        <script>
            function toggleRecord() {
                fetch('/toggle_record').then(r => r.json()).then(d => {
                    document.getElementById('rec-status').innerText = d.status;
                });
            }
            function updateSize() {
                fetch('/record_size').then(r => r.json()).then(d => {
                    document.getElementById('rec-size').innerText = d.size;
                });
            }
            setInterval(updateSize, 2000);
            document.addEventListener("keydown", function(e) {
                if (e.key === "5") { toggleRecord(); }
            });
        </script>
    </head>
    <body>
        <h2>📻 Radio Player</h2>
        <p>Current: {{ current_station or "None" }}</p>
        <audio controls autoplay src="/play"></audio>
        <br><br>
        <button onclick="toggleRecord()">⏺ Record / Stop</button>
        <div id="rec-status">Not recording</div>
        <div id="rec-size"></div>
        <br>
        <small>Keypad shortcuts: 5=Record/Stop</small>
        <h3>Stations</h3>
        <ul>{{ station_links|safe }}</ul>
    </body>
    </html>
    """, current_station=current_station, station_links=station_links)


@app.route("/set_station")
def set_station():
    global current_station
    name = request.args.get("name")
    if name in RADIO_STATIONS:
        current_station = name
        start_ffmpeg(RADIO_STATIONS[name])
    return ("<script>location.href='/'</script>")


@app.route("/play")
def play():
    def generate():
        q = Queue()
        clients.append(q)
        try:
            while True:
                yield q.get()
        finally:
            clients.remove(q)

    return Response(generate(), mimetype="audio/mpeg")


@app.route("/toggle_record")
def toggle_record():
    global recording, record_file
    if not recording:
        os.makedirs("recordings", exist_ok=True)
        filename = datetime.now().strftime("recordings/%Y%m%d_%H%M%S.mp3")
        record_file = open(filename, "wb")
        recording = True
        return jsonify(status="Recording started")
    else:
        recording = False
        if record_file:
            record_file.close()
            record_file = None
        return jsonify(status="Recording stopped")


@app.route("/record_size")
def record_size():
    if record_file and not record_file.closed:
        size = os.path.getsize(record_file.name) / 1024
        return jsonify(size=f"{size:.1f} KB")
    return jsonify(size="0 KB")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)