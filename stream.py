import subprocess
import shutil
import os
from datetime import datetime
from flask import Flask, Response, request, render_template_string, send_file, jsonify

app = Flask(__name__)

# ✅ Check ffmpeg
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Full list of radio stations
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
}

# Track processes
ffmpeg_process = None
record_process = None
current_station = None
record_file = None


# 🏠 Home screen
@app.route("/")
def home():
    return render_template_string("""
    <html>
    <head>
        <title>📻 VRadio</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f4f4f4; text-align: center; }
            h2 { margin-top: 20px; }
            .station { 
                background: #fff; 
                padding: 15px; 
                margin: 10px auto; 
                width: 90%; 
                max-width: 400px; 
                border-radius: 12px; 
                box-shadow: 0 3px 6px rgba(0,0,0,0.2);
            }
            button { 
                padding: 10px 15px; 
                margin: 5px; 
                border: none; 
                border-radius: 8px; 
                font-size: 14px; 
                cursor: pointer;
                background: #4CAF50; 
                color: white;
            }
        </style>
    </head>
    <body>
        <h2>📻 Flask VRadio</h2>
        {% for name in stations.keys() %}
        <div class="station">
            <b>{{name}}</b><br>
            <a href="/player?station={{name}}"><button>▶ Select</button></a>
        </div>
        {% endfor %}
    </body>
    </html>
    """, stations=RADIO_STATIONS)


# 🎶 Player screen with keypad support
@app.route("/player")
def player():
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404

    # Convert station names to list for next/prev navigation
    station_list = list(RADIO_STATIONS.keys())
    current_index = station_list.index(station)

    return render_template_string("""
    <html>
    <head>
        <title>▶ {{station}}</title>
        <style>
            body { font-family: Arial, sans-serif; background: black; color: white; text-align: center; }
            .container { margin-top: 60px; }
            audio { width: 90%; max-width: 400px; margin: 20px auto; display: block; }
            button { padding: 12px 18px; margin: 8px; border: none; border-radius: 12px; font-size: 16px; cursor: pointer; }
            .record { background: #ff9800; color: white; }
            .stop { background: #f44336; color: white; }
        </style>
        <script>
            const stationList = {{ station_list|tojson }};
            let currentIndex = {{ current_index }};

            function goToStation(index) {
                if (index < 0) index = stationList.length - 1;
                if (index >= stationList.length) index = 0;
                window.location.href = "/player?station=" + stationList[index];
            }

            function toggleRecord() {
                fetch("/record?station=" + stationList[currentIndex])
                    .then(res => res.text())
                    .then(html => {
                        const w = window.open("", "_blank");
                        w.document.write(html);
                    });
            }

            document.addEventListener('keydown', function(e) {
                const key = e.key;
                if (key === "0") {  // record / stop record
                    toggleRecord();
                } else if (key === "1") {  // home
                    window.location.href = "/";
                } else if (key === "4") {  // previous
                    goToStation(currentIndex - 1);
                } else if (key === "6") {  // next
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
            <br>
            <small>Keypad shortcuts: 0=Record, 1=Home, 4=Prev, 6=Next</small>
        </div>
    </body>
    </html>
    """, station=station, station_list=station_list, current_index=current_index)


# 🎶 Stream playback
@app.route("/play")
def play():
    global ffmpeg_process, current_station
    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404

    url = RADIO_STATIONS[station]

    # Stop previous playback
    if ffmpeg_process:
        ffmpeg_process.kill()

    current_station = station

    # Stream audio to browser
    ffmpeg_process = subprocess.Popen(
        ["ffmpeg", "-i", url, "-c", "copy", "-f", "mp3", "pipe:1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL
    )

    def generate():
        while True:
            data = ffmpeg_process.stdout.read(1024)
            if not data:
                break
            yield data

    return Response(generate(), mimetype="audio/mpeg")


# ⏺️ Record screen
@app.route("/record")
def record():
    global record_process, record_file

    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404

    url = RADIO_STATIONS[station]

    os.makedirs("recordings", exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    record_file = f"recordings/{station.replace(' ', '_')}_{timestamp}.mp3"

    # Stop previous recording
    if record_process:
        record_process.kill()

    record_process = subprocess.Popen(
        ["ffmpeg", "-i", url, "-map_metadata", "-1", "-c", "copy", record_file],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return render_template_string("""
    <html>
    <head>
        <title>⏺ Recording</title>
        <style>
            body { font-family: Arial, sans-serif; background: black; color: white; text-align: center; }
            .container { margin-top: 60px; }
            .status { font-size: 18px; margin: 15px; }
            button { padding: 12px 18px; margin: 8px; border: none; border-radius: 12px; font-size: 16px; cursor: pointer; background: #f44336; color: white; }
        </style>
        <script>
            async function updateSize() {
                let res = await fetch('/record_size');
                let data = await res.json();
                document.getElementById("size").innerText = data.size + " KB";
                if (data.active) {
                    setTimeout(updateSize, 1000);
                }
            }
            updateSize();
        </script>
    </head>
    <body>
        <div class="container">
            <h2>⏺ Recording: {{station}}</h2>
            <div class="status">File Size: <span id="size">0 KB</span></div>
            <a href="/stop_record"><button>⏹ Stop Recording</button></a>
        </div>
    </body>
    </html>
    """, station=station)


# 📏 Recording size API
@app.route("/record_size")
def record_size():
    global record_file, record_process
    if record_file and os.path.exists(record_file) and record_process:
        size = os.path.getsize(record_file) // 1024
        return jsonify({"size": size, "active": True})
    return jsonify({"size": 0, "active": False})


# ⏹️ Stop recording and download
@app.route("/stop_record")
def stop_record():
    global record_process, record_file
    if record_process:
        record_process.kill()
        record_process = None
    if record_file and os.path.exists(record_file):
        return send_file(record_file, as_attachment=True)
    return "No recording found", 404


# ⏹️ Stop all playback
@app.route("/stop")
def stop():
    global ffmpeg_process
    if ffmpeg_process:
        ffmpeg_process.kill()
        ffmpeg_process = None
    return "⏹️ Stopped playback"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)