import os, subprocess, shutil, re, threading
from flask import Flask, Response, request, redirect, render_template_string, send_from_directory

app = Flask(__name__)

# ✅ Ensure ffmpeg is installed
if not shutil.which("ffmpeg"):
    raise RuntimeError("⚠️ ffmpeg not found. Please install ffmpeg.")

# 📡 Radio stations
RADIO_STATIONS = {
    "Muthnabi Radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "Kozhikode Radio": "http://sc-bb.1.fm:8017/",
}

# 🎙 Global state
ffmpeg_process = None
recording_file = None
is_recording = False
current_url = None


def start_ffmpeg(url, record=False):
    """Start ffmpeg with optional recording, capture ICY metadata"""
    global ffmpeg_process, recording_file, is_recording, current_url
    stop_ffmpeg()
    current_url = url

    cmd = ["ffmpeg", "-icy_metadata", "1", "-i", url, "-c:a", "mp3"]

    if record:
        os.makedirs("recordings", exist_ok=True)
        recording_file = f"recordings/{url.split('//')[-1].replace('/', '_')}.mp3"
        cmd += ["-f", "tee", f"[f=mp3]pipe:1|[f=mp3]{recording_file}"]
    else:
        cmd += ["-f", "mp3", "pipe:1"]

    ffmpeg_process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,  # 🔴 capture stderr for ICY titles
        bufsize=1,
        universal_newlines=True
    )
    is_recording = record

    if record:
        # Background thread to watch for metadata titles
        def read_metadata():
            global recording_file
            for line in ffmpeg_process.stderr:
                if "StreamTitle=" in line:
                    m = re.search(r"StreamTitle='([^']+)'", line)
                    if m:
                        title = m.group(1).strip()
                        safe_title = "".join(c for c in title if c.isalnum() or c in (" ", "_", "-"))
                        if safe_title:
                            new_name = f"recordings/{safe_title}.mp3"
                            try:
                                if os.path.exists(recording_file):
                                    os.rename(recording_file, new_name)
                                    recording_file = new_name
                                    print(f"💾 Renamed recording → {recording_file}")
                            except Exception as e:
                                print("Rename failed:", e)
        threading.Thread(target=read_metadata, daemon=True).start()


def stop_ffmpeg():
    """Stop current ffmpeg"""
    global ffmpeg_process, is_recording
    if ffmpeg_process:
        ffmpeg_process.terminate()
        ffmpeg_process = None
    is_recording = False


@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head>
        <title>📻 Radio Player</title>
        <style>
            body { font-family: Arial; text-align: center; background: #f4f4f4; }
            h2 { margin-top: 20px; }
            .station { padding: 12px; margin: 10px; background: #fff;
                       border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
            a { text-decoration: none; color: #333; font-weight: bold; }
        </style>
    </head>
    <body>
        <h2>📻 Choose a Station</h2>
        {% for name, url in stations.items() %}
            <div class="station"><a href="/player?station={{name}}">▶ {{name}}</a></div>
        {% endfor %}
        <br><a href="/recordings">📂 Saved Recordings</a>
    </body>
    </html>
    """, stations=RADIO_STATIONS)


@app.route("/player")
def player():
    station = request.args.get("station")
    url = RADIO_STATIONS.get(station)
    if not url:
        return "Station not found", 404
    return render_template_string("""
    <html>
    <head>
        <title>{{station}}</title>
        <style>
            body { font-family: Arial; text-align: center; background: #f4f4f4; }
            audio { width: 80%; margin: 20px; }
            button { padding: 12px 18px; margin: 8px; border: none;
                     border-radius: 10px; font-size: 16px; cursor: pointer; }
            .record { background: #ff9800; color: white; }
        </style>
    </head>
    <body>
        <h2>▶ {{station}}</h2>
        <audio controls autoplay>
            <source src="/proxy?url={{url}}" type="audio/mpeg">
        </audio>
        <form method="post" action="/toggle_record">
            <input type="hidden" name="station" value="{{station}}">
            <button type="submit" class="record">⏺ Record / ⏹ Stop</button>
        </form>
        <br><a href="/">⬅ Home</a>
    </body>
    </html>
    """, station=station, url=url)


@app.route("/proxy")
def proxy():
    global ffmpeg_process, current_url
    url = request.args.get("url")
    if not ffmpeg_process or url != current_url:
        start_ffmpeg(url, record=is_recording)

    def generate():
        while ffmpeg_process and ffmpeg_process.stdout:
            data = ffmpeg_process.stdout.read(4096)
            if not data:
                break
            yield data
    return Response(generate(), mimetype="audio/mpeg")


@app.route("/toggle_record", methods=["POST"])
def toggle_record():
    station = request.form.get("station")
    url = RADIO_STATIONS.get(station)
    if not url:
        return redirect("/")

    if is_recording:
        stop_ffmpeg()
        print("⏹ Recording stopped")
    else:
        start_ffmpeg(url, record=True)
        print("▶ Recording started")
    return redirect(f"/player?station={station}")


@app.route("/recordings")
def list_recordings():
    files = os.listdir("recordings") if os.path.exists("recordings") else []
    return render_template_string("""
    <h2>📂 Saved Recordings</h2>
    {% for f in files %}
        <div><a href="/download/{{f}}">⬇ {{f}}</a></div>
    {% endfor %}
    <br><a href="/">⬅ Home</a>
    """, files=files)


@app.route("/download/<path:filename>")
def download(filename):
    return send_from_directory("recordings", filename, as_attachment=True)


if __name__ == "__main__":
    app.run("0.0.0.0", 5000, debug=True)