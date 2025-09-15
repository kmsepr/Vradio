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
    "air_kavarati": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio189/chunklist.m3u8",
    "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
    "manjeri_fm": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio101/chunklist.m3u8",
    "real_fm": "http://air.pc.cdn.bitgravity.com/air/live/pbaudio083/playlist.m3u8",
    # Add all other stations here
}

STATIONS_PER_PAGE = 5

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
        return "⚠️ Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

# -------------------------------
# Play page
# -------------------------------
@app.route("/play/<station_name>")
def play_station(station_name):
    if station_name not in RADIO_STATIONS:
        return "⚠️ Station not found", 404

    stations = list(RADIO_STATIONS.keys())
    current_index = stations.index(station_name)
    display_name = station_name.replace("_", " ").title()
    stream_url = f"/stream/{station_name}"

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>📻 Vradio - {display_name}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
        <style>
            body {{
                font-family:sans-serif;
                margin:0; padding:5px;
                background:#fff; font-size:12px;
            }}
            h1 {{ font-size:16px; text-align:center; color:#007bff; margin:5px 0; }}
            h2 {{ font-size:14px; text-align:center; margin:5px 0; }}
            audio {{ width:100%; margin:5px 0; }}
            .btn {{
                display:block; width:100%;
                text-align:center; padding:6px 0;
                margin:2px 0; border-radius:4px;
                text-decoration:none; color:white;
                font-size:12px; cursor:pointer;
            }}
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

            function updatePlayer(idx) {{
                currentIndex = idx;
                const station = stations[idx];
                document.querySelector("h2").textContent = "🎧 " + station.replace(/_/g," ").toUpperCase();
                player.src = "/stream/" + station;
                player.play();
                playPauseBtn.textContent = "⏸ Pause";
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

            function setSleepTimer(){{
                let minutes = prompt("Minutes until stop:","30");
                if(minutes && !isNaN(minutes) && minutes>0){{
                    let sec = parseInt(minutes)*60;
                    clearTimeout(window.sleepTimer);
                    clearInterval(window.countdownInterval);
                    window.sleepTimer = setTimeout(()=>{{
                        player.pause();
                        document.getElementById("timerInfo").textContent = "⏹ Sleep timer reached.";
                        alert("⏹ Sleep timer reached. Audio stopped.");
                    }}, sec*1000);

                    window.countdownInterval = setInterval(()=>{
                        sec -= 1;
                        if(sec<=0) clearInterval(window.countdownInterval);
                        else document.getElementById("timerInfo").textContent = "⏳ Sleep: "+Math.floor(sec/60)+"m "+(sec%60)+"s";
                    }},1000);
                }}
            }}

            // T9 keys: 4=Prev, 5=Play/Pause, 6=Next
            document.addEventListener("keydown", function(e){{
                if(e.key==="4") prevStation();
                else if(e.key==="5") togglePlayPause();
                else if(e.key==="6") nextStation();
            }});
        </script>
    </body>
    </html>
    """

# -------------------------------
# Homepage
# -------------------------------
@app.route("/")
def index():
    page = int(request.args.get("page",1))
    stations = list(RADIO_STATIONS.keys())
    total_pages = (len(stations)+STATIONS_PER_PAGE-1)//STATIONS_PER_PAGE
    station_json = json.dumps(stations)

    start = (page-1)*STATIONS_PER_PAGE
    end = start+STATIONS_PER_PAGE
    paged = stations[start:end]

    links = "".join([f"<a href='play/{s}' class='btn'>{s.replace('_',' ').title()}</a>" for s in paged])

    nav = ""
    if page>1:
        nav+=f"<a href='/?page=1' class='btn'>⏮️ First</a>"
        nav+=f"<a href='/?page={page-1}' class='btn'>◀️ Prev</a>"
    if page<total_pages:
        nav+=f"<a href='/?page={page+1}' class='btn'>Next ▶️</a>"
        nav+=f"<a href='/?page={total_pages}' class='btn'>Last ⏭️</a>"

    return f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
        <title>📻 Vradio</title>
        <style>
            body{{font-family:sans-serif; font-size:12px; margin:0; padding:5px; background:#f0f0f0;}}
            h2{{font-size:14px;text-align:center;margin:5px 0;}}
            a.btn{{display:block;background:#007bff;color:white;text-decoration:none;padding:6px 0;margin:2px 0;border-radius:4px;text-align:center;}}
            .info{{font-size:11px;text-align:center;margin-top:4px;color:#555;}}
        </style>
    </head>
    <body>
        <h2>📻 Vradio (Page {page}/{total_pages})</h2>
        {links}
        <div class="nav">{nav}</div>
        <div class="info">T9 Keys: 1=First,2=Reload,3=Last,4=Prev,5=Random,6=Next</div>

        <script>
            const allStations={station_json};
            document.addEventListener("keydown", function(e){{
                let currentPage