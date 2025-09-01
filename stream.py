import subprocess
import time
import shutil
import os
import signal
from flask import Flask, Response, request, redirect

app = Flask(__name__)

# ✅ Check if ffmpeg is available
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Full list of radio stations
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",
    "air_kavarati": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio189/chunklist.m3u8",
    "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
    # ... keep rest intact ...
    "vom_radio": "https://radio.psm.mv/draair",
}

STATIONS_PER_PAGE = 10
KEEPALIVE_INTERVAL = 30  # seconds

# 🎙️ Track recording process
recording_process = None
recording_file = None


def generate_stream(url):
    while True:
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10",
                "-i", url,
                "-vn",
                "-ac", "1",
                "-b:a", "64k",
                "-f", "mp3",
                "-"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=4096
        )

        print(f"🎵 Streaming from: {url}")

        try:
            for chunk in iter(lambda: process.stdout.read(4096), b""):
                yield chunk
        except GeneratorExit:
            process.kill()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")
        finally:
            process.kill()
            print("🔁 Restarting FFmpeg in 3s...")
            time.sleep(3)


@app.route("/stream/<station_name>")
def stream_station(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")


@app.route("/record/<station_name>")
def record_station(station_name):
    """Start recording a station"""
    global recording_process, recording_file

    if recording_process:
        return f"⚠️ Already recording: {recording_file}"

    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404

    # 📂 Downloads folder
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    os.makedirs(downloads, exist_ok=True)
    recording_file = os.path.join(downloads, f"{station_name}_{int(time.time())}.mp3")

    recording_process = subprocess.Popen(
        [
            "ffmpeg", "-y", "-i", url,
            "-vn", "-acodec", "libmp3lame", "-b:a", "128k",
            recording_file
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return f"⏺️ Recording started: {recording_file}"


@app.route("/stop_record")
def stop_record():
    """Stop current recording"""
    global recording_process, recording_file
    if recording_process:
        recording_process.send_signal(signal.SIGINT)
        recording_process = None
        return f"⏹️ Recording stopped. Saved: {recording_file}"
    else:
        return "⚠️ No active recording."


@app.route("/<station_name>")
def direct_station_redirect(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return redirect(url)


@app.route("/")
def index():
    page = int(request.args.get("page", 1))
    station_names = list(RADIO_STATIONS.keys())
    total_pages = (len(station_names) + STATIONS_PER_PAGE - 1) // STATIONS_PER_PAGE

    start = (page - 1) * STATIONS_PER_PAGE
    end = start + STATIONS_PER_PAGE
    paged_stations = station_names[start:end]

    # Each station has Play + Record buttons
    links_html = "".join(
        f"""
        <div>
            <a href='/stream/{name}'>{name.replace('_', ' ').title()}</a>
            <a href='/record/{name}' style='background: red'>⏺️ Record</a>
        </div>
        """
        for name in paged_stations
    )

    nav_html = ""
    if page > 1:
        nav_html += f"<a href='/?page=1'>⏮️ First</a>"
        nav_html += f"<a href='/?page={page - 1}'>◀️ Prev</a>"
    if page < total_pages:
        nav_html += f"<a href='/?page={page + 1}'>Next ▶️</a>"
        nav_html += f"<a href='/?page={total_pages}'>Last ⏭️</a>"

    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>🎧 Radio Streams</title>
        <style>
            body {{
                font-family: sans-serif;
                font-size: 14px;
                padding: 10px;
                margin: 0;
                background: #f0f0f0;
            }}
            h2 {{
                font-size: 16px;
                text-align: center;
                margin: 10px 0;
            }}
            a {{
                display: inline-block;
                background: #007bff;
                color: white;
                text-decoration: none;
                padding: 6px 10px;
                margin: 4px;
                border-radius: 6px;
                text-align: center;
                font-size: 13px;
            }}
            .nav {{
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
                margin-top: 10px;
                gap: 4px;
            }}
            .info {{
                font-size: 11px;
                text-align: center;
                margin-top: 8px;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <h2>🎙️ Audio Streams (Page {page}/{total_pages})</h2>
        {links_html}
        <div class="nav">{nav_html}</div>
        <div class="info">⏺️ Use Record to save in Downloads | <a href='/stop_record' style='background: gray'>⏹️ Stop Recording</a></div>
    </body>
    </html>
    """
    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)