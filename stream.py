import os
import shutil
import subprocess
import threading
from datetime import datetime
from flask import Flask, Response, request, render_template_string, jsonify
from queue import Queue

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

# 🔊 Global state
clients = []
current_station = None
ffmpeg_thread = None
recording = False
record_file = None


def ffmpeg_worker(station_url):
    """Run ffmpeg, feed audio to clients + recorder."""
    global recording, record_file

    command = [
        "ffmpeg", "-i", station_url,
        "-vn",
        "-acodec", "libmp3lame", "-ac", "1", "-ar", "44100", "-b:a", "64k",
        "-f", "mp3", "pipe:1"
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    for chunk in iter(lambda: process.stdout.read(4096), b""):
        # Send to connected clients
        for q in clients[:]:
            try:
                q.put(chunk, timeout=0.1)
            except:
                clients.remove(q)
        # Save if recording
        if recording and record_file:
            record_file.write(chunk)


def start_ffmpeg(station_url):
    """Ensure ffmpeg is running for selected station."""
    global ffmpeg_thread
    if not ffmpeg_thread or not ffmpeg_thread.is_alive():
        ffmpeg_thread = threading.Thread(target=ffmpeg_worker, args=(station_url,), daemon=True)
        ffmpeg_thread.start()


@app.route("/")
def index():
    station_links = "".join(
        f"<li><a href='/set_station?name={name}'>{name}</a></li>"
        for name in RADIO_STATIONS.keys()
    )
    return render_template_string("""
    <html>
    <head>
        <title>Radio Player</title>
        <style>
            body { font-family: sans-serif; text-align: center; padding: 20px; }
            button { font-size: 18px; margin: 5px; padding: 10px; }
        </style>
        <script>
            function toggleRecord() {
                fetch('/toggle_record').then(r => r.json()).then(d => {
                    document.getElementById('rec-status').innerText = d.status;
                });
            }
            function updateSize() {
                fetch('/record_size').then(r => r.json()).then(d => {
                    document.getElementById('rec-size').innerText = d.size;
                });
            }
            setInterval(updateSize, 2000);
            document.addEventListener("keydown", function(e) {
                if (e.key === "5") { toggleRecord(); }
            });
        </script>
    </head>
    <body>
        <h2>📻 Radio Player</h2>
        <p>Current: {{ current_station or "None" }}</p>
        <audio controls autoplay src="/play"></audio>
        <br><br>
        <button onclick="toggleRecord()">⏺ Record / Stop</button>
        <div id="rec-status">Not recording</div>
        <div id="rec-size"></div>
        <br>
        <small>Keypad shortcuts: 5=Record/Stop</small>
        <h3>Stations</h3>
        <ul>{{ station_links|safe }}</ul>
    </body>
    </html>
    """, current_station=current_station, station_links=station_links)


@app.route("/set_station")
def set_station():
    global current_station
    name = request.args.get("name")
    if name in RADIO_STATIONS:
        current_station = name
        start_ffmpeg(RADIO_STATIONS[name])
    return ("<script>location.href='/'</script>")


@app.route("/play")
def play():
    def generate():
        q = Queue()
        clients.append(q)
        try:
            while True:
                yield q.get()
        finally:
            clients.remove(q)

    return Response(generate(), mimetype="audio/mpeg")


@app.route("/toggle_record")
def toggle_record():
    global recording, record_file
    if not recording:
        os.makedirs("recordings", exist_ok=True)
        filename = datetime.now().strftime("recordings/%Y%m%d_%H%M%S.mp3")
        record_file = open(filename, "wb")
        recording = True
        return jsonify(status="Recording started")
    else:
        recording = False
        if record_file:
            record_file.close()
            record_file = None
        return jsonify(status="Recording stopped")


@app.route("/record_size")
def record_size():
    if record_file and not record_file.closed:
        size = os.path.getsize(record_file.name) / 1024
        return jsonify(size=f"{size:.1f} KB")
    return jsonify(size="0 KB")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)