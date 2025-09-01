import os, subprocess, shutil
from flask import Flask, Response, request, redirect, render_template_string

app = Flask(__name__)

if not shutil.which("ffmpeg"):
    raise RuntimeError("⚠️ ffmpeg not found")

RADIO_STATIONS = {
    "Muthnabi Radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "Kozhikode Radio": "http://sc-bb.1.fm:8017/",
}

ffmpeg_process = None
current_url = None
recording_file = None


def start_ffmpeg(url, record=False):
    """Start ffmpeg with tee if recording"""
    global ffmpeg_process, recording_file
    stop_ffmpeg()

    cmd = ["ffmpeg", "-i", url, "-c:a", "mp3"]

    if record:
        os.makedirs("recordings", exist_ok=True)
        recording_file = f"recordings/{url.split('//')[-1].replace('/', '_')}.mp3"
        cmd += ["-f", "tee", f"[f=mp3]pipe:1|[f=mp3]{recording_file}"]
    else:
        cmd += ["-f", "mp3", "pipe:1"]

    ffmpeg_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)


def stop_ffmpeg():
    global ffmpeg_process
    if ffmpeg_process:
        ffmpeg_process.terminate()
        ffmpeg_process = None


@app.route("/player")
def player():
    station = request.args.get("station")
    url = RADIO_STATIONS.get(station)
    if not url:
        return "Station not found", 404
    return render_template_string("""
    <h2>{{station}}</h2>
    <audio controls autoplay>
        <source src="/proxy?url={{url}}" type="audio/mpeg">
    </audio>
    <form method="post" action="/toggle_record">
        <input type="hidden" name="station" value="{{station}}">
        <button type="submit">⏺ Start / Stop</button>
    </form>
    """, station=station, url=url)


@app.route("/proxy")
def proxy():
    url = request.args.get("url")
    # always start ffmpeg if not running
    if not ffmpeg_process:
        start_ffmpeg(url, record=False)

    def generate():
        while True:
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
    if ffmpeg_process:
        stop_ffmpeg()
        print("⏹ stopped")
    else:
        start_ffmpeg(url, record=True)
        print("▶ recording + playing")
    return redirect(f"/player?station={station}")


if __name__ == "__main__":
    app.run("0.0.0.0", 8000, debug=True)