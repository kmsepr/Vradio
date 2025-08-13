import subprocess
import time
import shutil
import json
from flask import Flask, Response, request

app = Flask(__name__)

# ✅ Check if ffmpeg is available
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Radio stations
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",
    "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
    "real_fm": "http://air.pc.cdn.bitgravity.com/air/live/pbaudio083/playlist.m3u8",
    # ... add all other stations here
}

STATIONS_PER_PAGE = 10
KEEPALIVE_INTERVAL = 30  # seconds

# 🔄 Transcode/stream generator
def generate_stream(url):
    last_data_time = time.time()
    process = None

    while True:
        if process:
            process.kill()
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-reconnect", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "15",
                "-fflags", "+nobuffer+flush_packets+discardcorrupt",
                "-flags", "low_delay",
                "-analyzeduration", "700000",
                "-probesize", "300000",
                "-thread_queue_size", "384",
                "-i", url,
                "-vn",
                "-ac", "1",
                "-b:a", "24k",
                "-bufsize", "48k",
                "-f", "mp3",
                "-"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=8192,
        )
        try:
            while True:
                chunk = process.stdout.read(8192)
                if chunk:
                    last_data_time = time.time()
                    yield chunk
                elif time.time() - last_data_time > KEEPALIVE_INTERVAL:
                    yield b"\0" * 10
                    last_data_time = time.time()
        except GeneratorExit:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")
            time.sleep(5)

# 🎛 Raw transcoded stream (direct link)
@app.route("/stream/<station_name>")
def stream_station(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

# 🎧 Player with UI
@app.route("/play/<station_name>")
def play_station(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404

    display_name = station_name.replace("_", " ").title()
    stream_url = f"/stream/{station_name}"  # points to transcoded stream

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{display_name}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: sans-serif; text-align: center; background: #fff; padding: 20px; }}
            audio {{ width: 100%; margin-top: 20px; }}
            h2 {{ font-size: 24px; margin-bottom: 10px; }}
            .info {{ margin: 10px 0; color: #555; font-size: 14px; }}
            .timer-btn {{ display: inline-block; padding: 8px 12px; margin-top: 12px; background: #28a745; color: white; border-radius: 5px; font-size: 14px; text-decoration: none; }}
            .timer-info {{ font-size: 14px; color: #333; margin-top: 6px; }}
        </style>
    </head>
    <body>
        <h2>🎧 Now Playing</h2>
        <div class="info"><strong>{display_name}</strong></div>

        <audio id="player" controls autoplay>
            <source id="audioSource" src="{stream_url}" type="audio/mpeg">
            Your browser does not support audio.
        </audio>
        <div class="info" id="playTime">▶️ Playing: 0m 0s</div>

        <!-- Direct Link (raw transcoded stream) -->
        <a href="{stream_url}" target="_blank" class="timer-btn" style="background:#007bff;">🔗 Direct Link</a>

        <!-- Sleep Timer -->
        <a href="#" class="timer-btn" onclick="setSleepTimer()">⏲ Sleep Timer</a>
        <div id="timerInfo" class="timer-info"></div>

        <script>
            const player = document.getElementById("player");
            const source = document.getElementById("audioSource");
            const playTimeEl = document.getElementById("playTime");

            // Auto-retry on error
            player.addEventListener("error", function() {{
                console.warn("Stream error. Retrying...");
                setTimeout(() => {{
                    const newSrc = source.src.split("?")[0] + "?retry=" + Date.now();
                    source.src = newSrc;
                    player.load();
                    player.play().catch(err => console.warn("Autoplay failed:", err));
                }}, 2000);
            }});

            // Playing time counter
            let playSeconds = 0;
            setInterval(() => {{
                if (!player.paused) {{
                    playSeconds++;
                    playTimeEl.textContent = "▶️ Playing: " + Math.floor(playSeconds / 60) + "m " + (playSeconds % 60) + "s";
                }}
            }}, 1000);

            // Sleep timer
            let sleepTimer = null;
            let countdownInterval = null;
            function setSleepTimer() {{
                let minutes = prompt("Enter minutes until stop:", "30");
                if (minutes && !isNaN(minutes) && minutes > 0) {{
                    let secondsLeft = parseInt(minutes) * 60;
                    clearInterval(countdownInterval);
                    clearTimeout(sleepTimer);

                    sleepTimer = setTimeout(() => {{
                        player.pause();
                        alert("⏹ Sleep timer reached. Stream stopped.");
                        document.getElementById("timerInfo").textContent = "";
                    }}, secondsLeft * 1000);

                    countdownInterval = setInterval(() => {{
                        secondsLeft--;
                        if (secondsLeft <= 0) clearInterval(countdownInterval);
                        else document.getElementById("timerInfo").textContent =
                            "⏳ Sleep timer: " + Math.floor(secondsLeft/60) + "m " + (secondsLeft%60) + "s left";
                    }}, 1000);
                }}
            }}
        </script>
    </body>
    </html>
    """

# 📄 Main page: paginated list of stations
@app.route("/")
def index():
    page = int(request.args.get("page", 1))
    station_names = list(RADIO_STATIONS.keys())
    total_pages = (len(station_names) + STATIONS_PER_PAGE - 1) // STATIONS_PER_PAGE
    station_list_json = json.dumps(station_names)

    start = (page - 1) * STATIONS_PER_PAGE
    end = start + STATIONS_PER_PAGE
    paged_stations = station_names[start:end]

    links_html = "".join(
        f"<a href='play/{name}'>{name.replace('_', ' ').title()}</a>"
        for name in paged_stations
    )

    nav_html = ""
    if page > 1:
        nav_html += f"<a href='/?page=1'>⏮️ First</a>"
        nav_html += f"<a href='/?page={page - 1}'>◀️ Prev</a>"
    if page < total_pages:
        nav_html += f"<a href='/?page={page + 1}'>Next ▶️</a>"
        nav_html += f"<a href='/?page={total_pages}'>Last ⏭️</a>"

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>🎧 Radio Streams</title>
        <style>
            body {{ font-family: sans-serif; font-size: 14px; padding: 10px; margin: 0; background: #f0f0f0; }}
            h2 {{ font-size: 16px; text-align: center; margin: 10px 0; }}
            a {{ display: block; background: #007bff; color: white; text-decoration: none; padding: 8px; margin: 4px 0; border-radius: 6px; text-align: center; font-size: 13px; }}
            .nav {{ display: flex; justify-content: space-between; flex-wrap: wrap; margin-top: 10px; gap: 4px; }}
            .info {{ font-size: 11px; text-align: center; margin-top: 8px; color: #555; }}
        </style>
    </head>
    <body>
        <h2>🎙️ Audio Streams (Page {page}/{total_pages})</h2>
        {links_html}
        <div class="nav">{nav_html}</div>
        <div class="info">🔢 T9 Keys: 1=First, 4=Prev, 6=Next, 3=Last, 5=Random, 0=Exit</div>

        <script>
        const allStations = {station_list_json};
        document.addEventListener("keydown", function(e) {{
            const key = e.key;
            let page = {page};
            let total = {total_pages};

            if (key === "1") window.location.href = "/?page=1";
            else if (key === "2") window.location.reload();
            else if (key === "3") window.location.href = "/?page=" + total;
            else if (key === "4" && page > 1) window.location.href = "/?page=" + (page - 1);
            else if (key === "5") {{
                const randomStation = allStations[Math.floor(Math.random() * allStations.length)];
                window.location.href = "/play/" + randomStation;
            }}
            else if (key === "6" && page < total) window.location.href = "/?page=" + (page + 1);
            else if (key === "7") window.scrollTo({{ top: 0, behavior: "smooth" }});
            else if (key === "8") window.scrollTo({{ top: document.body.scrollHeight, behavior: "smooth" }});
            else if (key === "9") window.location.href = "/?page=" + (page < total ? page + 1 : 1);
            else if (key === "0") window.location.href = "about:blank";
        }});
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)