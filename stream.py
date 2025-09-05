import shutil
import subprocess, time
import os
from io import BytesIO
from datetime import datetime
from threading import Lock
from flask import Flask, Response, request, render_template_string, send_file, jsonify
import tempfile

app = Flask(__name__)

# ✅ Check ffmpeg availability
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Radio/TV stations
RADIO_STATIONS = {
    "mazhavil_manorama": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/mazhavilmanorama_nim_https/050522/mazhavilmanorama/playlist.m3u8",
    "victers_tv": "https://932y4x26ljv8-hls-live.5centscdn.com/victers/tv.stream/victers/tv1/chunks.m3u8",
    "safari_tv": "https://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/chunks.m3u8",
    "bloomberg_tv": "https://bloomberg-bloomberg-3-br.samsung.wurl.tv/manifest/playlist.m3u8",
    "france_24": "https://live.france24.com/hls/live/2037218/F24_EN_HI_HLS/master_500.m3u8",
}

hls_processes = {}
hls_dirs = {}

# ── Recording state ──
current_station = None
recording_active = False
record_buffer = None
record_lock = Lock()

# ── Stream generator ──
def generate_stream(url, station, mode="audio"):
    global record_buffer, recording_active, current_station
    current_station = station

    ffmpeg_cmd = [
        "ffmpeg",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "10",
        "-i", url
    ]

    if mode == "audio":
        ffmpeg_cmd += ["-vn", "-ac", "1", "-b:a", "40k", "-f", "mp3", "-"]
    else:
        ffmpeg_cmd += [
            "-vf", "scale=-2:360",
            "-c:v", "libx264", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "64k",
            "-f", "mpegts", "-"
        ]

    while True:
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=4096
        )
        try:
            for chunk in iter(lambda: process.stdout.read(4096), b""):
                if mode == "audio" and recording_active and current_station == station:
                    with record_lock:
                        if record_buffer is not None:
                            record_buffer.write(chunk)
                yield chunk
        except GeneratorExit:
            process.kill()
            break
        finally:
            process.kill()
            time.sleep(3)

# ── Routes ──

@app.route("/")
def home():
    station_list = list(RADIO_STATIONS.keys())
    return render_template_string("""
<html>
<head>
<title>📺 VRadio/TV</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body {
  font-family: Arial, sans-serif;
  background: #121212;
  color: #fff;
  text-align: center;
}
h2 { margin: 20px 0; }
.station-card {
  background: #1e1e1e;
  margin: 8px auto;
  padding: 10px;
  border-radius: 6px;
  width: 90%;
  max-width: 300px;
}
button {
  margin: 5px;
  padding: 8px 12px;
  font-size: 16px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
}
.play-btn { background: #4caf50; color: white; }
.tv-btn { background: #2196f3; color: white; }
.direct-btn { background: #ff9800; color: white; }
</style>
</head>
<body>
  <h2>📻 VRadio / 📺 VTV</h2>
  {% for s in stations %}
    <div class="station-card">
      <div><b>{{s}}</b></div>
      <button class="play-btn" onclick="window.location.href='/play?station={{s}}'">▶ Audio</button>
      <button class="tv-btn" onclick="window.location.href='/tv?station={{s}}'">📺 TV (HLS)</button>
      <button class="direct-btn" onclick="window.location.href='/tv_direct?station={{s}}'">⚡ Direct</button>
    </div>
  {% endfor %}
</body>
</html>
""", stations=station_list)

# 🎶 Audio route
@app.route("/play")
def play():
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404
    return Response(generate_stream(RADIO_STATIONS[station], station, "audio"), mimetype="audio/mpeg")

# 📺 HLS TV route
@app.route("/tv")
def tv():
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404

    url = RADIO_STATIONS[station]

    if station not in hls_processes:
        tmpdir = tempfile.mkdtemp()
        hls_dirs[station] = tmpdir
        playlist = os.path.join(tmpdir, "index.m3u8")

        cmd = [
            "ffmpeg", "-y",
            "-i", url,
            "-vf", "scale=-2:360",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "aac", "-b:a", "64k",
            "-f", "hls",
            "-hls_time", "2",
            "-hls_list_size", "6",
            "-hls_flags", "append_list+delete_segments",
            playlist
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        hls_processes[station] = proc

    return send_file(os.path.join(hls_dirs[station], "index.m3u8"), mimetype="application/vnd.apple.mpegurl")

# Serve .ts files
@app.route("/tv/<station>/<path:filename>")
def tv_segments(station, filename):
    if station not in hls_dirs:
        return "Station not active", 404
    path = os.path.join(hls_dirs[station], filename)
    if not os.path.exists(path):
        return "Segment not found", 404
    return send_file(path)

# 📺 Direct MPEG-TS route
@app.route("/tv_direct")
def tv_direct():
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404
    return Response(generate_stream(RADIO_STATIONS[station], station, "video"), mimetype="video/mp2t")

# ── Run ──
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)