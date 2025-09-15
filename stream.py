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
                    playPauseBtn.textContent