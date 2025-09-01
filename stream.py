import subprocess
import threading
import shutil
import os
from datetime import datetime
from flask import Flask, Response, request, render_template_string, send_file, jsonify
from flask import send_file, make_response

app = Flask(__name__)

# ✅ Check ffmpeg
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Radio stations
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",
    "air_kavarati": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio189/chunklist.m3u8",
    "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
    "manjeri_fm": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio101/chunklist.m3u8",
    "vom_radio": "https://radio.psm.mv/draair",
}

# 🎛 Process managers
ffmpeg_processes = {}    # station -> playback process
record_processes = {}    # station -> recording process
record_files = {}        # station -> recording file


# 🔹 Stop process safely
def stop_process(proc):
    if proc:
        proc.kill()
        proc.wait()


# 🏠 Home page
@app.route("/")
def home():
    page = int(request.args.get("page", 1))
    per_page = 5
    station_list = list(RADIO_STATIONS.keys())
    total_pages = (len(station_list) + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    stations_on_page = station_list[start:end]

    return render_template_string("""
    <html>
    <head>
    <title>📻 VRadio</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    body { font-family: Arial, sans-serif; background:#121212; color:#fff; text-align:center; padding:2vh 2vw; }
    h2 { font-size:5vw; margin-bottom:3vh; }
    .station-card { background:#1e1e1e; margin:2vh auto; padding:2vh; border-radius:12px; width:95%; max-width:600px; }
    .station-name { font-size:4vw; margin-bottom:2vh; }
    .station-card button { padding:2vh 2vw; font-size:3.5vw; border-radius:10px; border:none; cursor:pointer; background:#ff5722; color:white; width:100%; }
    .station-card button:hover { background:#e64a19; }
    .random-btn { background:#4caf50; margin-bottom:2vh; padding:2vh 2vw; font-size:4vw; width:95%; max-width:600px; }
    .random-btn:hover { background:#43a047; }
    .pagination { margin-top:2vh; }
    .pagination button { padding:1.5vh 2vw; margin:1vh; font-size:3vw; border:none; border-radius:10px; background:#333; color:#fff; cursor:pointer; }
    .pagination button:hover { background:#555; }
    </style>
    <script>
    const page = {{page}};
    const totalPages = {{total_pages}};
    const stationList = {{ station_list|tojson }};
    function goPage(p){ if(p<1)p=totalPages;if(p>totalPages)p=1; window.location.href="/?page="+p; }
    function randomPlay(){ const rand=Math.floor(Math.random()*stationList.length); window.location.href="/player?station="+stationList[rand]; }
    document.addEventListener('keydown', function(e){
      const key=e.key;
      if(key==="4"){goPage(page-1);} 
      else if(key==="6"){goPage(page+1);} 
      else if(key>="1" && key<="5"){const index=parseInt(key)-1; const stations={{ stations_on_page|tojson }}; if(stations[index]) window.location.href="/player?station="+stations[index];}
      else if(key==="0"){randomPlay();}
    });
    </script>
    </head>
    <body>
    <h2>📻 VRadio</h2>
    <button class="random-btn" onclick="randomPlay()">🎲 Random Play</button>

    {% for name in stations_on_page %}
    <div class="station-card">
      <div class="station-name">{{name}}</div>
      <button onclick="window.location.href='/player?station={{name}}'">▶ Play</button>
    </div>
    {% endfor %}

    <div class="pagination">
      <button onclick="goPage(page-1)">⬅ Prev</button>
      <button onclick="goPage(page+1)">Next ➡</button>
      <div>Page {{page}} of {{total_pages}}</div>
    </div>
    </body>
    </html>
    """, stations_on_page=stations_on_page, page=page, total_pages=total_pages, station_list=station_list)


@app.route("/player")
def player():
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404

    station_list = list(RADIO_STATIONS.keys())
    current_index = station_list.index(station)

    return render_template_string("""
<html>
<head>
<title>▶ {{station}}</title>
<style>
body { font-family: Arial; background:black; color:white; text-align:center; padding:2vh; }
h2 { font-size:5vw; }
audio { width:95%; max-width:600px; margin:2vh auto; display:block; }
button { padding:2vh 2vw; margin:2vh; border:none; border-radius:12px; font-size:3.5vw; cursor:pointer; }
.record { background:#ff9800; color:white; }
</style>
<script>
const stationList = {{ station_list|tojson }};
let currentIndex = {{ current_index }};
let recording = false;

async function toggleRecord(){
    const station = stationList[currentIndex];
    if(!recording){
        // Start playback + recording
        window.location.href="/play_and_record?station=" + station;
        recording = true;
        document.getElementById("rec-status").innerText="⏺ Recording";
        document.querySelector('.record').innerText="⏹ Stop Recording";
    } else {
        // Stop recording & download
        let res = await fetch("/stop_record?station=" + station);
        if(res.ok){
            let blob = await res.blob();
            let url = window.URL.createObjectURL(blob);
            let a = document.createElement("a");
            a.href = url;

            const contentDisposition = res.headers.get('Content-Disposition');
            let filename = station + "_recording.mp3";
            if(contentDisposition){
                const match = contentDisposition.match(/filename="?(.+)"?/);
                if(match) filename = match[1];
            }
            a.download = filename;
            a.click();
            window.URL.revokeObjectURL(url);
        }
        recording = false;
        document.getElementById("rec-status").innerText="Not recording";
        document.querySelector('.record').innerText="⏺ Start Recording";
    }
}

function goToStation(i){ 
    if(i<0) i=stationList.length-1; 
    if(i>=stationList.length) i=0; 
    window.location.href="/player?station="+stationList[i]; 
}

function randomStation(){ 
    const r=Math.floor(Math.random()*stationList.length); 
    goToStation(r); 
}

document.addEventListener('keydown', function(e){
    if(e.key==="5"){ toggleRecord(); }
    else if(e.key==="1"){ window.location.href="/"; }
    else if(e.key==="4"){ goToStation(currentIndex-1); }
    else if(e.key==="6"){ goToStation(currentIndex+1); }
    else if(e.key==="0"){ randomStation(); }
});
</script>
</head>
<body>
<h2>{{station}}</h2>
<audio controls autoplay>
  <source src="/play?station={{station}}" type="audio/mpeg">
</audio>
<button class="record" onclick="toggleRecord()">⏺ Start Recording</button>
<div id="rec-status">Not recording</div>
<br><small>Keys: 5=Record/Stop, 1=Home, 4=Prev, 0=Random, 6=Next</small>
</body>
</html>
""", station=station, station_list=station_list, current_index=current_index)


@app.route("/play_stream")
def play_stream():
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404

    record = request.args.get("record", "0") == "1"
    url = RADIO_STATIONS[station]

    # Stop any previous process for this station
    if station in ffmpeg_processes:
        stop_process(ffmpeg_processes[station])
        ffmpeg_processes.pop(station, None)
    if station in record_files and record:
        record_files.pop(station, None)

    os.makedirs("recordings", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    record_file = f"recordings/{station}_{timestamp}.mp3" if record else None

    # Build ffmpeg command
    cmd = ["ffmpeg", "-i", url, "-map", "0:a", "-c:a", "libmp3lame", "-b:a", "128k", "-f", "mp3", "-"]
    if record:
        cmd += ["-map", "0:a", "-c:a", "libmp3lame", "-b:a", "64k", record_file]

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    ffmpeg_processes[station] = proc
    if record_file:
        record_files[station] = record_file

    def generate():
        try:
            while True:
                data = proc.stdout.read(4096)
                if not data:
                    break
                yield data
        finally:
            stop_process(proc)
            ffmpeg_processes.pop(station, None)

    return Response(generate(), mimetype="audio/mpeg")

@app.route("/stop_record")
def stop_record():
    station = request.args.get("station")
    process = ffmpeg_processes.get(station)
    file_path = record_files.get(station)

    if process:
        process.kill()
        process.wait()
        ffmpeg_processes.pop(station, None)

    if file_path and os.path.exists(file_path):
        record_files.pop(station, None)
        response = make_response(send_file(file_path, as_attachment=True))
        filename = os.path.basename(file_path)
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response

    return "No recording found", 404

# ⏹ Stop playback
@app.route("/stop")
def stop():
    station = request.args.get("station")
    if station in ffmpeg_processes:
        stop_process(ffmpeg_processes[station])
        ffmpeg_processes.pop(station, None)
    return "⏹ Stopped playback"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)