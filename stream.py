import shutil
import subprocess, time
import os
from io import BytesIO
from datetime import datetime
from threading import Lock
from flask import Flask, Response, request, render_template_string, send_file, jsonify
import tempfile
import threading

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
        mime = "audio/mpeg"
    else:
        ffmpeg_cmd += [
            "-vf", "scale=-2:360",
            "-c:v", "libx264", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "64k",
            "-f", "mpegts", "-"
        ]
        mime = "video/mp2t"

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
    return "<h2>📺 Radio/TV Server Running</h2><p>Use /play or /tv routes.</p>"

# 🎶 Audio route
@app.route("/play")
def play():
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404
    return Response(generate_stream(RADIO_STATIONS[station], station, "audio"), mimetype="audio/mpeg")

# 📺 HLS TV route (low latency)
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
            "-hls_time", "2",              # ⏱ 2s chunks
            "-hls_list_size", "6",         # keep last 6
            "-hls_flags", "append_list+delete_segments",  # start faster
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

# 📺 Direct MPEG-TS route (ultra low-latency, no HLS)
@app.route("/tv_direct")
def tv_direct():
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404
    return Response(generate_stream(RADIO_STATIONS[station], station, "video"), mimetype="video/mp2t")

# 🎙 Recording toggle
@app.route("/record")
def record():
    global recording_active, record_buffer, current_station
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return jsonify({"status": "error", "message": "Station not found"}), 404
    current_station = station
    if not recording_active:
        with record_lock:
            record_buffer = BytesIO()
        recording_active = True
        return jsonify({"status": "recording", "file": None})
    else:
        recording_active = False
        size_kb = 0
        with record_lock:
            if record_buffer is not None:
                size_kb = record_buffer.tell() // 1024
        return jsonify({"status": "stopped", "file": "/stop_record", "size": size_kb})

@app.route("/record_size")
def record_size():
    active = recording_active
    size_kb = 0
    with record_lock:
        if active and record_buffer is not None:
            size_kb = record_buffer.tell() // 1024
    return jsonify({"size": size_kb, "active": active})

@app.route("/stop_record")
def stop_record():
    global record_buffer, current_station
    with record_lock:
        if record_buffer is None or record_buffer.tell() == 0:
            return "No recording found", 404
        record_buffer.seek(0)
        data = BytesIO(record_buffer.read())
        record_buffer.close()
        record_buffer = None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{(current_station or 'recording')}_{stamp}.mp3"
    current_station = None
    return send_file(data, mimetype="audio/mpeg", as_attachment=True, download_name=filename)

# ── Run ──
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)