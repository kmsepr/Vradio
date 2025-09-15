import subprocess
import shutil
import json
import queue
import threading
from flask import Flask, Response, request

app = Flask(__name__)

# Check ffmpeg
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# -------------------------------
# Radio stations
# -------------------------------
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",
    "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
    "malayalam_1": "http://167.114.131.90:5412/stream",
    "radio_malayalam": "https://radiomalayalamfm.com/radio/8000/radio.mp3",
    # Add other stations here...
}

STATIONS_PER_PAGE = 10

# -------------------------------
# Stream generator
# -------------------------------
def generate_stream(url):
    q = queue.Queue(maxsize=50)

    def ffmpeg_worker():
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
                "-thread_queue_size", "1024",
                "-i", url,
                "-vn",
                "-ac", "1",
                "-b:a", "24k",
                "-bufsize", "192k",
                "-f", "mp3",
                "-"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=4096,
        )

        try:
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                q.put(chunk)
        finally:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            q.put(None)

    threading.Thread(target=ffmpeg_worker, daemon=True).start()

    while True:
        chunk = q.get()
        if chunk is None:
            break
        yield chunk

# -------------------------------
# Raw stream endpoint
# -------------------------------
@app.route("/stream/<station_name>")
def stream_station(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

# -------------------------------
# Play page
# -------------------------------
@app.route("/play/<station_name>")
def play_station(station_name):
    if station_name not in RADIO_STATIONS:
        return "⚠️ Station not found", 404

    station_names = list(RADIO_STATIONS.keys())
    current_index = station_names.index(station_name)
    display_name = station_name.replace("_", " ").title()
    stream_url = f"/stream/{station_name}"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Vradio - {display_name}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ font-family: sans-serif; text-align:center; padding:20px; background:#fff; }}
            h1 {{ font-size:28px; margin-bottom:5px; color:#007bff; }}
            h2 {{ font-size:22px; margin-bottom:10px; }}
            .info {{ margin:10px 0; color:#555; font-size:16px; }}
            .control-btn {{
                display:inline-block; padding:8px 12px; margin:5px;
                background:#007bff; color:white; border-radius:5px; font-size:14px; text-decoration:none;
                cursor:pointer;
            }}
            .timer-btn {{
                display:inline-block; padding:8px 12px; margin:5px;
                background:#28a745; color:white; border-radius:5px; font-size:14px; text-decoration:none;
                cursor:pointer;
            }}
            .timer-info {{ font-size:14px; color:#333; margin-top:6px; }}
            audio {{ width:100%; margin-top:10px; border-radius:6px; }}
        </style>
    </head>
    <body>
        <h1>🎙️ Vradio</h1>
        <h2>🎧 Now Playing</h2>
        <div class="info"><strong id="stationName">{display_name}</strong></div>

        <audio id="player" controls autoplay>
            <source src="{stream_url}" type="audio/mpeg">
            Your browser does not support the audio element.
        </audio>

        <div style="margin-top:10px;">
            <a class="control-btn" onclick="prevStation()">⏮ Previous</a>
            <a class="control-btn" onclick="togglePlayPause()" id="playPauseBtn">⏸ Pause</a>
            <a class="control-btn" onclick="nextStation()">⏭ Next</a>
            <a class="control-btn" onclick="randomStation()">🔀 Random</a>
        </div>

        <div>
            <a class="timer-btn" onclick="setSleepTimer()">⏲ Sleep Timer</a>
        </div>
        <div id="timerInfo" class="timer-info"></div>

        <script>
            const stations = {station_names};
            let currentIndex = {current_index};
            const player = document.getElementById("player");
            const stationNameElem = document.getElementById("stationName");
            let sleepTimer = null;
            let countdownInterval = null;

            function updatePlayer(index) {{
                currentIndex = index;
                const station = stations[currentIndex];
                stationNameElem.textContent = station.replace(/_/g, " ").toUpperCase();
                player.src = "/stream/" + station;
                player.play();
                document.getElementById("playPauseBtn").textContent = "⏸ Pause";
            }}

            function prevStation() {{
                let idx = currentIndex - 1;
                if (idx < 0) idx = stations.length - 1;
                updatePlayer(idx);
            }}

            function nextStation() {{
                let idx = currentIndex + 1;
                if (idx >= stations.length) idx = 0;
                updatePlayer(idx);
            }}

            function randomStation() {{
                let idx = Math.floor(Math.random() * stations.length);
                updatePlayer(idx);
            }}

            function togglePlayPause() {{
                if (player.paused) {{
                    player.play();
                    document.getElementById("playPauseBtn").textContent = "⏸ Pause";
                }} else {{
                    player.pause();
                    document.getElementById("playPauseBtn").textContent = "▶️ Play";
                }}
            }}

            function setSleepTimer() {{
                let minutes = prompt("Enter minutes until stop:", "30");
                if (minutes && !isNaN(minutes) && minutes > 0) {{
                    let secondsLeft = parseInt(minutes) * 60;
                    clearInterval(countdownInterval);
                    clearTimeout(sleepTimer);

                    sleepTimer = setTimeout(() => {{
                        player.pause();
                        document.getElementById("timerInfo").textContent = "⏹ Sleep timer reached.";
                        alert("⏹ Sleep timer reached. Audio stopped.");
                    }}, secondsLeft * 1000);

                    countdownInterval = setInterval(() => {{
                        secondsLeft--;
                        if (secondsLeft <= 0) clearInterval(countdownInterval);
                        else document.getElementById("timerInfo").textContent =
                            "⏳ Sleep timer: " + Math.floor(secondsLeft/60) + "m " + (secondsLeft%60) + "s left";
                    }}, 1000);
                }}
            }}

            // T9 key control
            document.addEventListener("keydown", function(e) {{
                const key = e.key;
                if (key === "4") prevStation();
                else if (key === "5") togglePlayPause();
                else if (key === "6") nextStation();
            }});
        </script>
    </body>
    </html>
    """

# -------------------------------
# Index page
# -------------------------------
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
        <title>🎙️ Vradio</title>
        <style>
            body {{ font-family:sans-serif; font-size:14px; padding:10px; margin:0; background:#f0f0f0; }}
            h2 {{ font-size:16px; text-align:center; margin:10px 0; }}
            a {{ display:block; background:#007bff; color:white; text-decoration:none; padding:8px; margin:4px 0; border-radius:6px; text-align:center; font-size:13px; }}
            .nav {{ display:flex; justify-content:space-between; flex-wrap:wrap; margin-top:10px; gap:4px; }}
            .info {{ font-size:11px; text-align:center; margin-top:8px; color:#555; }}
        </style>
    </head>
    <body>
        <h2>🎙️ Vradio (Page {page}/{total_pages})</h2>
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
            else if (key === "0") window.location.href = "about:blank";
        }});
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)