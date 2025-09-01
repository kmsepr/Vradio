import os
import subprocess
import shutil
from flask import Flask, render_template_string, request, redirect, Response, send_from_directory

app = Flask(__name__)

# ✅ Check ffmpeg
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Radio stations
RADIO_STATIONS = {
    "Muthnabi Radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "Kozhikode Radio": "http://sc-bb.1.fm:8017/",
}

# 🎙 Recording state
record_process = None
recording_file = None


@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head>
        <title>📻 Radio Player</title>
        <style>
            body { font-family: Arial; text-align: center; background: #f4f4f4; }
            h2 { margin-top: 20px; }
            .station { padding: 10px; margin: 8px; background: #fff;
                       border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
            a { text-decoration: none; color: #333; font-weight: bold; }
        </style>
    </head>
    <body>
        <h2>📻 Radio Stations</h2>
        {% for name, url in stations.items() %}
            <div class="station"><a href="/player?station={{name}}">▶ {{name}}</a></div>
        {% endfor %}
        <br><a href="/recordings">📂 View Recordings</a>
    </body>
    </html>
    """, stations=RADIO_STATIONS)


@app.route("/player")
def player():
    station_name = request.args.get("station")
    stream_url = RADIO_STATIONS.get(station_name)
    if not stream_url:
        return "Station not found", 404

    return render_template_string("""
    <html>
    <head>
        <title>{{station}}</title>
        <style>
            body { font-family: Arial; text-align: center; background: #f4f4f4; }
            h2 { margin-top: 20px; }
            audio { width: 80%; margin: 20px; }
            button { padding: 12px 18px; margin: 8px; border: none;
                     border-radius: 10px; font-size: 16px; cursor: pointer; }
            .controls { margin-top: 20px; }
            .record { background: #ff9800; color: white; }
        </style>
    </head>
    <body>
        <h2>▶ Playing {{station}}</h2>
        <audio id="player" controls autoplay>
            <source src="/proxy?url={{stream}}" type="audio/mpeg">
        </audio>
        <div class="controls">
            <form method="post" action="/toggle_record">
                <input type="hidden" name="station" value="{{station}}">
                <button type="submit" class="record">⏺ Record / ⏹ Stop</button>
            </form>
        </div>
        <br>
        <a href="/">⬅ Back</a>
    </body>
    </html>
    """, station=station_name, stream=stream_url)


@app.route("/proxy")
def proxy():
    url = request.args.get("url")

    def generate():
        process = subprocess.Popen(
            ["ffmpeg", "-i", url, "-f", "mp3", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        try:
            while True:
                data = process.stdout.read(4096)
                if not data:
                    break
                yield data
        finally:
            process.kill()

    return Response(generate(), mimetype="audio/mpeg")


@app.route("/toggle_record", methods=["POST"])
def toggle_record():
    global record_process, recording_file
    station = request.form.get("station")
    url = RADIO_STATIONS.get(station)
    if not url:
        return redirect("/")

    if record_process is None:
        # Start recording
        os.makedirs("recordings", exist_ok=True)
        recording_file = f"recordings/{station.replace(' ', '_')}.mp3"
        record_process = subprocess.Popen(
            ["ffmpeg", "-i", url, "-c:a", "mp3", recording_file],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print(f"▶ Started recording {station}")
    else:
        # Stop recording
        record_process.terminate()
        record_process = None
        print(f"⏹ Stopped recording. Saved: {recording_file}")

    return redirect(f"/player?station={station}")


@app.route("/recordings")
def list_recordings():
    files = os.listdir("recordings") if os.path.exists("recordings") else []
    return render_template_string("""
    <html>
    <head>
        <title>📂 Recordings</title>
        <style>
            body { font-family: Arial; text-align: center; background: #f4f4f4; }
            .rec { padding: 10px; margin: 8px; background: #fff;
                   border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
        </style>
    </head>
    <body>
        <h2>📂 Saved Recordings</h2>
        {% for f in files %}
            <div class="rec"><a href="/download/{{f}}">⬇ {{f}}</a></div>
        {% endfor %}
        <br><a href="/">⬅ Back</a>
    </body>
    </html>
    """, files=files)


@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory("recordings", filename, as_attachment=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)