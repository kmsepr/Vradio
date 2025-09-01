import subprocess
import time
import shutil
import os
from flask import Flask, Response, request, redirect, send_from_directory, render_template_string

app = Flask(__name__)

# ✅ Check if ffmpeg is available
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Full list of radio stations
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "islamic_radio": "https://node-33.zeno.fm/xyz123",
}

# 🎙️ Folder for recordings
RECORDINGS_DIR = "recordings"
os.makedirs(RECORDINGS_DIR, exist_ok=True)

recording_process = None
recording_file = None

@app.route("/")
def home():
    return render_template_string("""
    <h2>📻 Radio Stations</h2>
    <ul>
    {% for key, url in stations.items() %}
      <li><a href="/player/{{ key }}">{{ key }}</a></li>
    {% endfor %}
    </ul>
    <h3>🎙️ Saved Recordings</h3>
    <ul>
    {% for f in files %}
      <li><a href="/recordings/{{ f }}">{{ f }}</a></li>
    {% endfor %}
    </ul>
    """, stations=RADIO_STATIONS, files=os.listdir(RECORDINGS_DIR))


# 🎶 Proxy stream for playing
@app.route("/stream/<station>")
def stream(station):
    url = RADIO_STATIONS.get(station)
    if not url:
        return "Station not found", 404

    def generate():
        process = subprocess.Popen(
            ["ffmpeg", "-i", url, "-f", "mp3", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        try:
            while True:
                data = process.stdout.read(1024)
                if not data:
                    break
                yield data
        finally:
            process.kill()

    return Response(generate(), mimetype="audio/mpeg")


# 🎧 Player screen with controls
@app.route("/player/<station>")
def player(station):
    if station not in RADIO_STATIONS:
        return "Station not found", 404
    return render_template_string("""
    <h2>▶️ Now Playing: {{ station }}</h2>
    <audio controls autoplay src="/stream/{{ station }}"></audio><br><br>
    <form action="/record/start/{{ station }}" method="post">
        <button type="submit">⏺ Record</button>
    </form>
    <form action="/record/stop" method="post">
        <button type="submit">⏹ Stop Recording</button>
    </form>
    <a href="/">⬅ Back</a>
    """, station=station)


# 🎙️ Start recording while playing
@app.route("/record/start/<station>", methods=["POST"])
def start_recording(station):
    global recording_process, recording_file

    if station not in RADIO_STATIONS:
        return "Station not found", 404

    if recording_process is not None:
        return "Already recording!", 400

    url = RADIO_STATIONS[station]
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    recording_file = f"{station}_{timestamp}.mp3"
    filepath = os.path.join(RECORDINGS_DIR, recording_file)

    recording_process = subprocess.Popen(
        ["ffmpeg", "-i", url, "-c", "copy", filepath],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    return redirect(f"/player/{station}")


# ⏹ Stop recording
@app.route("/record/stop", methods=["POST"])
def stop_recording():
    global recording_process, recording_file

    if recording_process is None:
        return "No active recording", 400

    recording_process.terminate()
    recording_process = None
    saved_file = recording_file
    recording_file = None

    return redirect(f"/recordings/{saved_file}")


# 📂 Serve saved recordings
@app.route("/recordings/<path:filename>")
def get_recording(filename):
    return send_from_directory(RECORDINGS_DIR, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)