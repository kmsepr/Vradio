import subprocess
import shutil
import queue
import threading
from flask import Flask, Response

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
    # ... add all other stations here
}

# -------------------------------
# Stream generator
# -------------------------------
def generate_stream(url):
    q = queue.Queue(maxsize=50)

    def ffmpeg_worker():
        process = subprocess.Popen(
            ["ffmpeg", "-i", url, "-c:a", "libmp3lame", "-b:a", "40k", "-f", "mp3", "-"],
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
        return "Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

# -------------------------------
# Play page
# -------------------------------
@app.route("/play/<station_name>")
def play_station(station_name):
    if station_name not in RADIO_STATIONS:
        return "Station not found", 404

    stations = list(RADIO_STATIONS.keys())
    current_index = stations.index(station_name)
    display_name = station_name.replace("_", " ").title()
    stream_url = f"/stream/{station_name}"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Vradio - {display_name}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{ font-family:sans-serif; margin:0; padding:5px; background:#fff; font-size:12px; }}
            h1 {{ font-size:16px; text-align:center; color:#007bff; margin:5px 0; }}
            h2 {{ font-size:14px; text-align:center; margin:5px 0; }}
            audio {{ width:100%; margin:5px 0; }}
            .btn {{ display:block; width:100%; text-align:center; padding:6px 0; margin:2px 0; border-radius:4px; text-decoration:none; color:white; font-size:12px; cursor:pointer; }}
            .control-btn {{ background:#007bff; }}
            .timer-btn {{ background:#28a745; }}
            .timer-info {{ font-size:12px; text-align:center; color:#333; margin-top:4px; }}
        </style>
    </head>
    <body>
        <h1>📻 Vradio</h1>
        <h2>🎧 {display_name}</h2>

        <audio id="player" controls autoplay>
            <source src="{stream_url}" type="audio/mpeg">
            Your browser does not support audio.
        </audio>

        <a class="btn control-btn" onclick="prevStation()">⏮ Previous</a>
        <a class="btn control-btn" onclick="togglePlayPause()" id="playPauseBtn">⏸ Pause</a>
        <a class="btn control-btn" onclick="nextStation()">⏭ Next</a>
        <a class="btn control-btn" onclick="randomStation()">🔀 Random</a>
        <a class="btn timer-btn" onclick="setSleepTimer()">⏲ Sleep Timer</a>

        <div id="timerInfo" class="timer-info"></div>

        <script>
            const stations = {stations};
            let currentIndex = {current_index};
            const player = document.getElementById("player");
            const playPauseBtn = document.getElementById("playPauseBtn");
            let sleepTimer = null;

            function updatePlayer(idx) {{
                currentIndex = idx;
                const station = stations[idx];
                document.querySelector("h2").textContent = "🎧 " + station.replace(/_/g," ").toUpperCase();
                player.src = "/stream/" + station;
                player.play();
                playPauseBtn.textContent = "⏸ Pause";
                clearSleepTimer();
            }}

            function prevStation() {{
                let idx = currentIndex - 1;
                if(idx < 0) idx = stations.length-1;
                updatePlayer(idx);
            }}

            function nextStation() {{
                let idx = currentIndex + 1;
                if(idx >= stations.length) idx = 0;
                updatePlayer(idx);
            }}

            function randomStation() {{
                let idx = Math.floor(Math.random()*stations.length);
                updatePlayer(idx);
            }}

            function togglePlayPause() {{
                if(player.paused){{
                    player.play();
                    playPauseBtn.textContent = "⏸ Pause";
                }} else {{
                    player.pause();
                    playPauseBtn.textContent = "▶️ Play";
                }}
            }}

            function setSleepTimer() {{
                const minutes = prompt("Set sleep timer (minutes):");
                if(!minutes || isNaN(minutes)) return;
                const secs = parseInt(minutes)*60;
                clearSleepTimer();
                let sec = secs;
                document.getElementById("timerInfo").textContent = "Sleep timer: " + minutes + " min";
                sleepTimer = setInterval(()=> {{
                    sec--;
                    document.getElementById("timerInfo").textContent = "Sleep timer: " + Math.ceil(sec/60) + " min";
                    if(sec <= 0){{
                        clearSleepTimer();
                        player.pause();
                        alert("⏲ Sleep timer ended!");
                    }}
                }}, 1000);
            }}

            function clearSleepTimer() {{
                if(sleepTimer) clearInterval(sleepTimer);
                sleepTimer = null;
                document.getElementById("timerInfo").textContent = "";
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)