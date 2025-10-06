import subprocess
import time
import shutil
import os
from flask import Flask, Response, request

app = Flask(__name__)

# --- Configuration ---
# ⚠️ Ensure this file exists in the same directory as the script!
VIDEO_INPUT_FILE = "radio_bg.jpg" 
STATIONS_PER_PAGE = 5

# Check ffmpeg and video input
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")
if not os.path.exists(VIDEO_INPUT_FILE):
    # This is a critical error for the video stream implementation
    raise RuntimeError(f"Video input file not found: {VIDEO_INPUT_FILE}. Please place an image file (e.g., a simple logo) in the script directory.")
# ---------------------


# 📡 Full list of radio stations
RADIO_STATIONS = {
    "oman_radio": "https://partwota.cdn.mgmlcdn.com/omanrdoorg/omanrdo.stream_aac/chunklist.m3u8",
    "quran_radio_nablus": "http://www.quran-radio.org:8002/",
    "al_nour": "http://audiostreaming.itworkscdn.com:9066/",
    "allahu_akbar_radio": "http://66.45.232.132:9996/stream",
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
    "river_nile_radio": "http://104.7.66.64:8087",
    "quran_radio_cairo": "http://n02.radiojar.com/8s5u5tpdtwzuv",
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


def generate_stream(url):
    """
    Transcodes the audio stream into a low-framerate video stream (image + audio).
    This is intended to prevent audio timeouts on mobile/Chromium power-saving policies.
    """
    
    command = [
        "ffmpeg",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "10",

        # --- VIDEO INPUT/OPTIONS (Static Image) ---
        "-loop", "1",                      # Loop the image indefinitely
        "-i", VIDEO_INPUT_FILE,            # Input the static image
        "-r", "1",                         # Framerate: 1 FPS (minimal data)
        "-tune", "stillimage",             # Optimization for static image encoding
        "-shortest",                       # Stop video encoding when the audio stream ends
        
        "-i", url,                         # Input the audio stream

        # --- OUTPUT MAPPING & ENCODING ---
        "-map", "0:v:0",                   # Map the first video stream (the image)
        "-map", "1:a:0",                   # Map the first audio stream (the radio)
        "-c:v", "libx264",                 # Video codec: H.264
        "-b:v", "100k",                    # Video bitrate (low)
        "-c:a", "aac",                     # Audio codec: AAC (common for video containers)
        "-b:a", "40k",                     # Audio bitrate
        
        "-pix_fmt", "yuv420p",             # Ensures compatibility with most players
        
        "-f", "flv",                       # Output format: Flash Video (FLV)
        "-"                                # Output to stdout
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=4096
    )

    try:
        for chunk in iter(lambda: process.stdout.read(4096), b""):
            yield chunk
    except GeneratorExit:
        process.kill()
        print("Stream closed by client.")
    except Exception as e:
        print(f"Stream error: {e}")
    finally:
        process.kill()
        time.sleep(3)


@app.route("/stream/<station_name>")
def stream_station(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "Station not found", 404
    
    # 🚨 MIME TYPE CHANGED to video/x-flv for the video stream
    return Response(generate_stream(url), mimetype="video/x-flv")


@app.route("/play/<station_name>")
def play_page(station_name):
    stations = list(RADIO_STATIONS.keys())
    if station_name not in stations:
        return "Station not found", 404

    idx = stations.index(station_name)
    prev_station = stations[idx - 1] if idx > 0 else stations[-1]
    next_station = stations[(idx + 1) % len(stations)]
    stations_json = [s.replace('_', ' ') for s in stations] # Clean names for JS list

    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Now Playing</title>
        <style>
            body {{ font-family: sans-serif; background: #000; color: #fff; text-align: center; margin:0; padding:10px; }}
            h2 {{ font-size:16px; margin:12px 0; }}
            /* 🚨 CSS adjusted for VIDEO element */
            video {{ width:100%; max-width:240px; margin:10px auto; display:block; height:180px; background:#333; }} 
            .controls {{ display:flex; flex-wrap:wrap; justify-content:center; gap:6px; margin:10px 0; }}
            button {{ flex:1 1 30%; padding:8px 10px; font-size:13px; border-radius:8px; border:none; background:#007bff; color:white; min-width:90px; }}
            .info {{ font-size:11px; color:#bbb; margin-top:10px; }}
            /* Mini mode adjustments for video */
            .mini h2, .mini .controls, .mini .info {{ display:none; }}
            .mini video {{ width:70%; height:120px; margin:5px auto; }}
        </style>
    </head>
    <body>
        <div id="playerUI" class="full">
            <h2>🎧 {station_name.replace('_',' ').title()}</h2>
            
            <video id="player" controls autoplay playsinline muted=true onloadedmetadata="this.muted=false" preload="auto">
                <source src="/stream/{station_name}" type="video/x-flv">
                Your browser does not support the video tag.
            </video>
            <div class="controls">
                <button onclick="goToStation('{prev_station}')">⏮ Prev (4)</button>
                <button onclick="togglePlay()">⏯ Play/Pause (5)</button>
                <button onclick="goToStation('{next_station}')">Next (6) ⏭</button>
                <button onclick="randomStation()">🎲 Random (0)</button>
                <button onclick="toggleSleep()" id="sleepBtn">⏱ Sleep (20m)</button>
            </div>
            <div class="info">🔢 T9 Keys → 1=Mini/Full | 4=Prev | 5=Play/Pause | 6=Next | 0=Random | *=Sleep</div>
        </div>
        <script>
        const STATIONS = {stations_json};
        const CURRENT = "{station_name}";
        const player = document.getElementById("player");

        function goToStation(station) {{
            if (player) {{
                player.pause();
                player.src = "";
            }}
            window.location.href = "/play/" + station;
        }}

        function randomStation() {{
            const others = STATIONS.filter(s => s !== CURRENT);
            const pick = others.length ? others[Math.floor(Math.random() * others.length)]
                                       : STATIONS[Math.floor(Math.random() * STATIONS.length)];
            goToStation(pick);
        }}

        function togglePlay() {{
            if(player.paused) player.play();
            else player.pause();
        }}

        function toggleMiniFull() {{
            const ui = document.getElementById("playerUI");
            if (ui.classList.contains("mini")) {{
                ui.classList.remove("mini");
                ui.classList.add("full");
            }} else {{
                ui.classList.remove("full");
                ui.classList.add("mini");
            }}
        }}

        // --- Sleep Timer ---
        let timerSeconds = 0;
        let countdown = null;
        let timerActive = false;
        const sleepBtn = document.getElementById("sleepBtn");

        function formatTime(s) {{
            const m = Math.floor(s / 60);
            const sec = s % 60;
            return String(m).padStart(2,'0') + ":" + String(sec).padStart(2,'0');
        }}

        function updateTimerUI() {{
            if(timerActive){{
                sleepBtn.innerText = "⏱ Sleep On (" + formatTime(timerSeconds) + ")";
            }}
        }}

        function tick() {{
            if(!timerActive) return;
            if(timerSeconds <= 0){{
                player.pause();
                stopTimer();
                return;
            }}
            timerSeconds--;
            updateTimerUI();
        }}

        function startTimer() {{
            timerSeconds = 20*60; 
            timerActive = true;
            clearInterval(countdown);
            updateTimerUI();
            countdown = setInterval(tick,1000);
        }}

        function stopTimer() {{
            timerActive = false;
            clearInterval(countdown);
            countdown = null;
            sleepBtn.innerText = "⏱ Sleep (20m)";
        }}

        function toggleSleep() {{
            if(timerActive) stopTimer(); else startTimer();
        }}
        
        // --- T9 Keys ---
        document.addEventListener("keydown", function(e){{
            if(e.key === "1") toggleMiniFull();
            else if(e.key === "4") goToStation("{prev_station}");
            else if(e.key === "5") togglePlay();
            else if(e.key === "6") goToStation("{next_station}");
            else if(e.key === "0") randomStation();
            else if(e.key === "*") toggleSleep();
        }});
        </script>
    </body>
    </html>
    """
    return html

@app.route("/")
def index():
    page = int(request.args.get("page", 1))
    stations = list(RADIO_STATIONS.keys())
    total_pages = (len(stations)+STATIONS_PER_PAGE-1)//STATIONS_PER_PAGE

    start = (page-1)*STATIONS_PER_PAGE
    end = start+STATIONS_PER_PAGE
    paged_stations = stations[start:end]

    links_html = "".join(f"<a href='/play/{s}'>{s.replace('_',' ').title()}</a>" for s in paged_stations)

    nav_html = ""
    if page > 1:
        nav_html += f"<a href='/?page=1'>⏮️ First</a><a href='/?page={page-1}'>◀️ Prev</a>"
    if page < total_pages:
        nav_html += f"<a href='/?page={page+1}'>Next ▶️</a><a href='/?page={total_pages}'>Last ⏭️</a>"

    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>📻 Vradio</title>
        <style>
            body {{ font-family:sans-serif; font-size:14px; padding:10px; margin:0; background:#f0f0f0; }}
            h2 {{ font-size:16px; text-align:center; margin:10px 0; }}
            a {{ display:block; background:#007bff; color:white; text-decoration:none; padding:8px; margin:4px 0; border-radius:6px; text-align:center; font-size:13px; }}
            .nav {{ display:flex; justify-content:space-between; flex-wrap:wrap; margin-top:10px; gap:4px; }}
            .info {{ font-size:11px; text-align:center; margin-top:8px; color:#555; }}
        </style>
    </head>
    <body>
        <h2>🎙️ Video Streams (Page {page}/{total_pages})</h2>
        {links_html}
        <div class="nav">{nav_html}</div>
        <div class="info">🔢 T9 Keys: 1=Mini/Full, 4=Prev Page, 6=Next Page, 0=Random</div>
        <script>
        document.addEventListener("keydown", function(e){{
            let page = {page};
            let total = {total_pages};
            if(e.key==="1") window.location.href="/?page=1"; // quick home
            else if(e.key==="3") window.location.href="/?page="+total;
            else if(e.key==="4" && page>1) window.location.href="/?page="+(page-1);
            else if(e.key==="6" && page<total) window.location.href="/?page="+(page+1);
            else if(e.key==="0"){{
                const links = document.querySelectorAll("a[href^='/play/']");
                const random = links[Math.floor(Math.random()*links.length)];
                if(random) random.click();
            }}
        }});
        </script>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
