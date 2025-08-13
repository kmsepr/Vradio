import subprocess
import shutil
import time
from flask import Flask, Response, request, redirect, url_for

app = Flask(__name__)

# -------------------------------
# Check ffmpeg
# -------------------------------
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# -------------------------------
# Radio stations (sample, add more)
# -------------------------------
RADIO_STATIONS = [
    {"name": "Muthnabi Radio", "url": "http://cast4.my-control-panel.com/proxy/muthnabi/stream"},
    {"name": "Radio Nellikka", "url": "https://usa20.fastcast4u.com:2130/stream"},
    {"name": "AIR Calicut", "url": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8"},
    {"name": "Malayalam 1", "url": "http://167.114.131.90:5412/stream"},
    {"name": "Radio Digital Malayali", "url": "https://radio.digitalmalayali.in/listen/stream/radio.mp3"}
]

# -------------------------------
# Stream generator using ffmpeg
# -------------------------------
def generate_stream(url):
    import threading
    import queue

    q = queue.Queue(maxsize=100)  # buffer ~800KB

    def ffmpeg_worker():
        while True:
            try:
                process = subprocess.Popen(
                    [
                        "ffmpeg",
                        "-reconnect", "1",
                        "-reconnect_streamed", "1",
                        "-reconnect_delay_max", "15",
                        "-i", url,
                        "-vn",
                        "-ac", "1",
                        "-b:a", "24k",
                        "-f", "mp3",
                        "-"
                    ],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    bufsize=16384
                )

                while True:
                    chunk = process.stdout.read(16384)
                    if not chunk:
                        break
                    q.put(chunk)

            except Exception as e:
                print(f"⚠️ FFmpeg error: {e}")
                time.sleep(2)
            finally:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    process.kill()
                q.put(None)

    threading.Thread(target=ffmpeg_worker, daemon=True).start()

    while True:
        chunk = q.get()
        if chunk is None:
            continue  # restart
        yield chunk

# -------------------------------
# Stream endpoint
# -------------------------------
@app.route("/stream/<int:station_id>")
def stream_station(station_id):
    if 0 <= station_id < len(RADIO_STATIONS):
        url = RADIO_STATIONS[station_id]["url"]
        return Response(generate_stream(url), mimetype="audio/mpeg")
    return "Station not found", 404

# -------------------------------
# Play page (minimal)
# -------------------------------
@app.route("/play/<int:station_id>")
def play_station(station_id):
    if 0 <= station_id < len(RADIO_STATIONS):
        station = RADIO_STATIONS[station_id]
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>{station['name']}</title>
            <style>
                body {{ font-family:sans-serif; font-size:16px; text-align:center; padding:10px; background:#f0f0f0; }}
                button {{ font-size:16px; padding:10px 20px; margin:5px; border:none; border-radius:5px; }}
                #timer {{ font-size:14px; margin-top:5px; color:#333; }}
            </style>
        </head>
        <body>
            <h2>🎧 {station['name']}</h2>
            <audio id="player" src="/stream/{station_id}" autoplay controls></audio><br>

            <button onclick="prev()">⏮️ Prev</button>
            <button onclick="next()">⏭️ Next</button>
            <button onclick="stop()">⏹ Stop</button>
            <button onclick="sleepTimer()">⏲ Sleep</button>
            <div id="timer"></div>

            <script>
                let current = {station_id};
                let timerId;
                const total = {len(RADIO_STATIONS)};

                function prev() {{
                    current = (current-1+total)%total;
                    window.location.href='/play/'+current;
                }}

                function next() {{
                    current = (current+1)%total;
                    window.location.href='/play/'+current;
                }}

                function stop() {{
                    const p=document.getElementById('player');
                    p.pause();
                    p.currentTime=0;
                }}

                function sleepTimer() {{
                    let min = prompt("Minutes until stop","30");
                    if(min>0) {{
                        let sec = parseInt(min)*60;
                        clearInterval(timerId);
                        const p=document.getElementById('player');
                        timerId = setInterval(()=>{{
                            sec--;
                            document.getElementById('timer').textContent='⏳ Sleep: '+Math.floor(sec/60)+'m '+(sec%60)+'s';
                            if(sec<=0){{ p.pause(); clearInterval(timerId); document.getElementById('timer').textContent='⏹ Stopped'; }}
                        }},1000);
                    }}
                }}
            </script>
        </body>
        </html>
        """
    return "Station not found", 404

# -------------------------------
# Index page
# -------------------------------
@app.route("/")
def index():
    links = "".join(f"<li><a href='/play/{i}'>{s['name']}</a></li>" for i,s in enumerate(RADIO_STATIONS))
    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>📻 HMD 110 Radio</title>
        <style>
            body {{ font-family:sans-serif; font-size:16px; padding:10px; background:#fff; }}
            li {{ margin:5px 0; }}
            a {{ text-decoration:none; color:#007bff; }}
        </style>
    </head>
    <body>
        <h2>📻 HMD 110 Internet Radio</h2>
        <ul>{links}</ul>
        <div style="font-size:12px;color:#555;margin-top:10px;">Low-speed optimized 24kbps streams.</div>
    </body>
    </html>
    """

# -------------------------------
# Run app
# -------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)