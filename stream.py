import shutil
import subprocess, time
import os
from io import BytesIO
from datetime import datetime
from threading import Lock
from flask import Flask, Response, request, render_template_string, send_file, jsonify

app = Flask(__name__)

# ✅ Check ffmpeg
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Full list of radio stations (unchanged)
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",
    "air_kavarati": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio189/chunklist.m3u8",
    "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
    "manjeri_fm": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio101/chunklist.m3u8",
    "real_fm": "http://air.pc.cdn.bitgravity.com/air/live/pbaudio083/playlist.m3u8",
    "safari_tv": "https://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/chunks.m3u8",
    "victers_tv": "https://932y4x26ljv8-hls-live.5centscdn.com/victers/tv.stream/victers/tv1/chunks.m3u8",
    "kairali_we": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/wetv_nim_https/050522/wetv/playlist.m3u8",
    "mazhavil_manorama": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/mazhavilmanorama_nim_https/050522/mazhavilmanorama/playlist.m3u8",
    "malayalam_1": "http://167.114.131.90:5412/stream",
    "radio_digital_malayali": "https://radio.digitalmalayali.in/listen/stream/radio.mp3",
    "malayalam_90s": "https://stream-159.zeno.fm/gm3g9amzm0hvv?zs-x-7jq8ksTOav9ZhlYHi9xw",
    "aural_oldies": "https://stream-162.zeno.fm/tksfwb1mgzzuv?zs=SxeQj1-7R0alsZSWJie5eQ",
    "radio_malayalam": "https://radiomalayalamfm.com/radio/8000/radio.mp3",
    "swaranjali": "https://stream-161.zeno.fm/x7mve2vt01zuv?zs-D4nK05-7SSK2FZAsvumh2w",
    "radio_beat_malayalam": "http://live.exertion.in:8050/radio.mp3",
    "shahul_radio": "https://stream-150.zeno.fm/cynbm5ngx38uv?zs=Ktca5StNRWm-sdIR7GloVg",
    "raja_radio": "http://159.203.111.241:8026/stream",
    "nonstop_hindi": "http://s5.voscast.com:8216/stream",
    "fm_gold": "https://airhlspush.pc.cdn.bitgravity.com/httppush/hispbaudio005/hispbaudio00564kbps.m3u8",
    "motivational_series": "http://104.7.66.64:8010",
    "deenagers_radio": "http://104.7.66.64:8003/",
    "hajj_channel": "http://104.7.66.64:8005",
    "abc_islam": "http://s10.voscast.com:9276/stream",
    "eram_fm": "http://icecast2.edisimo.com:8000/eramfm.mp3",
    "al_sumood_fm": "http://us3.internet-radio.com/proxy/alsumoodfm2020?mp=/stream",
    "nur_ala_nur": "http://104.7.66.64:8011/",
    "ruqya_radio": "http://104.7.66.64:8004",
    "seiyun_radio": "http://s2.radio.co/s26c62011e/listen",
    "noor_al_eman": "http://edge.mixlr.com/channel/boaht",
    "sam_yemen": "https://edge.mixlr.com/channel/kijwr",
    "afaq": "https://edge.mixlr.com/channel/rumps",
    "alfasi_radio": "https://qurango.net/radio/mishary_alafasi",
    "tafsir_quran": "https://radio.quranradiotafsir.com/9992/stream",
    "sirat_al_mustaqim": "http://104.7.66.64:8091/stream",
    "river_nile_radio": "http://104.7.66.64:8087",
    "quran_radio_cairo": "http://n02.radiojar.com/8s5u5tpdtwzuv",
    "quran_radio_nablus": "http://www.quran-radio.org:8002/",
    "al_nour": "http://audiostreaming.itworkscdn.com:9066/",
    "allahu_akbar_radio": "http://66.45.232.132:9996/stream",
    "omar_abdul_kafi_radio": "http://104.7.66.64:8007",
    "urdu_islamic_lecture": "http://144.91.121.54:27001/channel_02.aac",
    "hob_nabi": "http://216.245.210.78:8098/stream",
    "sanaa_radio": "http://dc5.serverse.com/proxy/pbmhbvxs/stream",
    "rubat_ataq": "http://stream.zeno.fm/5tpfc8d7xqruv",
    "al_jazeera": "http://live-hls-audio-web-aja.getaj.net/VOICE-AJA/index.m3u8",
    "bloomberg_tv": "https://bloomberg-bloomberg-3-br.samsung.wurl.tv/manifest/playlist.m3u8",
    "france_24": "https://live.france24.com/hls/live/2037218/F24_EN_HI_HLS/master_500.m3u8",
    "vom_radio": "https://radio.psm.mv/draair",

"mm": "
"http://surviving-audy-sadiqkm-fb03800f.koyeb.app/tv?station=mazhavil_manorama",
}

# ── State (single ffmpeg, in-memory recording) ────────────────────────────────

current_station = None
recording_active = False
record_buffer = None           # BytesIO when recording
record_lock = Lock()           # guard record_buffer access

# 🏠 Home screen with small cards for feature phones
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
body { 
    font-family: Arial, sans-serif; 
    background: #121212; 
    color: #fff; 
    text-align: center;
    padding: 1vh 1vw;
}
h2 { 
    font-size: 5vw;
    margin-bottom: 2vh;
}
.station-card { 
    background: #1e1e1e;
    margin: 0.5vh auto;
    padding: 0.5vh;
    border-radius: 6px;
    width: 90%;
    max-width: 200px;
    font-size: 2.8vw;
    box-shadow: 0 1px 2px rgba(0,0,0,0.2); 
}
.station-name { 
    font-size: 3.5vw;
    margin-bottom: 0.5vh;
}
.station-card button { 
    padding: 0.4vh 1vw;
    font-size: 3vw;
    border-radius: 6px;
    background: #ff5722;
    width: 100%;
}
.random-btn { 
    background: #4caf50;
    margin-bottom: 1.5vh;
    padding: 1vh 2vw;
    font-size: 3.5vw;
    width: 90%;
    max-width: 200px;
}
.pagination { margin-top: 1.5vh; font-size: 3vw; }
.pagination button { 
    padding: 0.6vh 1vw;
    font-size: 3vw;
    border-radius: 6px;
    background: #333;
}
@media (max-width: 480px) {
  h2 { font-size: 7vw; }
  .station-card, .station-card button { font-size: 4.5vw; max-width: 150px; }
  .station-name { font-size: 5vw; }
  .random-btn { font-size: 4.5vw; max-width: 150px; }
  .pagination button { font-size: 4.5vw; }
}
</style>
<script>
const page = {{page}};
const totalPages = {{total_pages}};
const stationList = {{ station_list|tojson }};
function goPage(p){ if(p<1)p=totalPages;if(p>totalPages)p=1; window.location.href="/?page="+p; }
function randomPlay(){ const rand=Math.floor(Math.random()*stationList.length); window.location.href="/player?station="+stationList[rand]; }
document.addEventListener('keydown', function(e){
  const key=e.key;
  if(key==="4"){goPage(page-1);} else if(key==="6"){goPage(page+1);} 
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
  <button onclick="goPage(page-1)">⬅ Prev Page</button>
  <button onclick="goPage(page+1)">Next Page ➡</button>
  <div>Page {{page}} of {{total_pages}}</div>
</div>
<small>Keypad: 6=Next, 4=Prev, 0=Random</small>
</body>
</html>
""", stations_on_page=stations_on_page, page=page, total_pages=total_pages, station_list=station_list)

# 🎶 Player screen with big UI
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
  
<style>
body { 
    font-family: Arial, sans-serif; 
    background: black; 
    color: white; 
    text-align: center; 
    padding: 2vh 2vw;
}
.container { margin-top: 5vh; }
h2 { font-size: 9vw; }
audio { 
    width: 96%;
    max-width: 500px;
    height: 55px;
    margin: 2vh auto;
    display: block;
}
button.record { 
    display: block;
    margin: 1.5vh auto;   /* center horizontally */
    padding: 1vh 3vw;     /* smaller padding */
    font-size: 5vw;       /* smaller font */
    border-radius: 8px;
    border: none;
    background: #ff9800;
    color: white;
    width: auto;          /* shrink to content */
    min-width: 120px;     /* keep touchable */
    max-width: 180px;
}
button.record:hover { background: #fb8000; }
#rec-status, #rec-size { font-size: 5vw; margin: 0.5vh 0;}
small { font-size: 3.5vw; }
@media (max-width: 480px) {
  h2 { font-size: 11vw; }
  audio { height: 65px; }
  button.record { 
      font-size: 6.5vw; 
      padding: 1.2vh 4vw; 
      min-width: 100px; 
      max-width: 160px;
  }
  #rec-status, #rec-size { font-size: 6.5vw; }
  small { font-size: 5vw; }
}
</style>
<script>
    const stationList = {{ station_list|tojson }};
    let currentIndex = {{ current_index }};
    let recording = false;
    let recordFile = null;
    const audio = document.querySelector('audio');
    function goToStation(index) {
        if (index < 0) index = stationList.length - 1;
        if (index >= stationList.length) index = 0;
        window.location.href = "/player?station=" + stationList[index];
    }
    function togglePlayStop() {
        if (audio.paused) {
            audio.play();
        } else {
            audio.pause();
            audio.currentTime = 0;
        }
    }
    async function toggleRecord() {
        let res = await fetch("/record?station=" + stationList[currentIndex]);
        let data = await res.json();
        if (data.status === "recording") {
            recording = true;
            recordFile = data.file;
            document.getElementById("rec-status").innerText = "⏺ Recording...";
            updateSize();
        } else if (data.status === "stopped") {
            recording = false;
            document.getElementById("rec-status").innerText = "⏹ Stopped";
            if (data.file) {
                window.location.href = "/stop_record";
            }
        }
    }
    async function updateSize() {
        if (!recording) return;
        let res = await fetch("/record_size");
        let data = await res.json();
        if (data.active) {
            document.getElementById("rec-size").innerText = data.size + " KB";
            setTimeout(updateSize, 1000);
        }
    }
    function randomStation() {
        const randIndex = Math.floor(Math.random() * stationList.length);
        goToStation(randIndex);
    }
    document.addEventListener('keydown', function(e) {
        const key = e.key;
        if (key === "5") {
            togglePlayStop();
        } else if (key === "*") {
            toggleRecord();
        } else if (key === "1") {
            window.location.href = "/";
        } else if (key === "4") {
            goToStation(currentIndex - 1);
        } else if (key === "0") {
            randomStation();
        } else if (key === "6") {
            goToStation(currentIndex + 1);
        }
    });
</script>
</head>
<body>
    <div class="container">
        <h2>{{station}}</h2>
        <audio controls autoplay>
            <source src="/play?station={{station}}" type="audio/mpeg">
            Your browser does not support audio.
        </audio>
        <br>
        <button class="record" onclick="toggleRecord()">⏺ Record / Stop</button>
        <div id="rec-status">Not recording</div>
        <div id="rec-size"></div>
        <br>
        <small>Keypad shortcuts: 5=Play/Stop, *=Record/Stop, 1=Home, 4=Prev, 0=Random, 6=Next</small>
    </div>
</body>
</html>
""", station=station, station_list=station_list, current_index=current_index)
# Home and Player routes are unchanged from your code (omitted here for brevity)
# Keep your exact templates/scripts; they work with the same endpoints:
#   /play, /record, /record_size, /stop_recorsubprocess

def generate_stream(url, station, mode="audio"):
    global record_buffer, recording_active, current_station
    current_station = station  # track active station

    ffmpeg_cmd = [
        "ffmpeg",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "10",
        "-i", url
    ]

    if mode == "audio":  
        # Radio-like audio stream
        ffmpeg_cmd += [
            "-vn",            # no video
            "-ac", "1",       # mono
            "-b:a", "40k",    # bitrate
            "-f", "mp3",
            "-"
        ]
        mime = "audio/mpeg"
    else:
        # TV mode → transcode to 360p HLS
        ffmpeg_cmd += [
            "-vf", "scale=-2:360",   # resize keeping aspect ratio, height=360p
            "-c:v", "libx264",       # video codec
            "-preset", "veryfast",
            "-c:a", "aac",           # audio codec
            "-b:a", "64k",
            "-f", "mpegts",          # transport stream
            "-"
        ]
        mime = "video/mp2t"

    while True:
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=4096
        )

        print(f"🎵▶ Streaming {mode.upper()}: {station} ({url})")
        try:
            for chunk in iter(lambda: process.stdout.read(4096), b""):
                # record only audio streams
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
            print("🔁 Restarting FFmpeg in 3s...")
            time.sleep(3)


# keep existing audio route
@app.route("/play")
def play():
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404
    url = RADIO_STATIONS[station]
    return Response(generate_stream(url, station, "audio"), mimetype="audio/mpeg")


# new TV route
@app.route("/tv")
def tv():
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404
    url = RADIO_STATIONS[station]
    return Response(generate_stream(url, station, "video"), mimetype="video/mp2t")


# 🎙 Toggle recording (no files written; buffer in RAM)
@app.route("/record")
def record():
    global recording_active, record_buffer, current_station

    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return jsonify({"status": "error", "message": "Station not found"}), 404

    # Track which station is currently recording
    current_station = station  

    if not recording_active:
        # Start: create a fresh in-memory buffer
        with record_lock:
            record_buffer = BytesIO()
        recording_active = True
        return jsonify({"status": "recording", "file": None})
    else:
        # Stop: prepare to download
        recording_active = False
        size_kb = 0
        with record_lock:
            if record_buffer is not None:
                size_kb = record_buffer.tell() // 1024
        return jsonify({"status": "stopped", "file": "/stop_record", "size": size_kb})

# 📏 Recording size API (RAM only)
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
        # Prepare a read handle
        record_buffer.seek(0)
        data = BytesIO(record_buffer.read())
        # free existing buffer
        record_buffer.close()
        record_buffer = None

    # Timestamped download name
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{(current_station or 'recording')}_{stamp}.mp3"

    # ✅ Reset station after stopping
    current_station = None  

    return send_file(
        data,
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name=filename
    )


# ── Your existing Home / Player UI routes go here unchanged ───────────────────
# (Keep your same @app.route("/") home() and @app.route("/player") player() functions)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)