import subprocess
import time
import shutil
from flask import Flask, Response, request, redirect

app = Flask(__name__)

# ✅ Check if ffmpeg is available
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

STATIONS_PER_PAGE = 10
KEEPALIVE_INTERVAL = 30  # seconds


def generate_stream(url):
    while True:
        process = subprocess.Popen(
   [
    "ffmpeg",
    "-reconnect", "1",
    "-reconnect_streamed", "1",
    "-reconnect_delay_max", "10",
    "-timeout", "5000000",           # ⏱ prevent hang on bad connection
    "-i", url,
    "-vn",
    "-ac", "1",
    "-b:a", "40k",                   # 🎧 low-bitrate mono
    "-bufsize", "2M", 

    "-f", "mp3",
    "-"
      ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=4096   # moderate buffer
        )

        print(f"🎵 Streaming from: {url}")

        try:
            for chunk in iter(lambda: process.stdout.read(4096), b""):
                yield chunk
        except GeneratorExit:
            process.kill()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")
        finally:
            process.kill()
            print("🔁 Restarting FFmpeg in 3s...")
            time.sleep(3)

@app.route("/stream/<station_name>")
def stream_station(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")


@app.route("/<station_name>")
def direct_station_redirect(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return redirect(url)


@app.route("/")
def index():
    page = int(request.args.get("page", 1))
    station_names = list(RADIO_STATIONS.keys())
    total_pages = (len(station_names) + STATIONS_PER_PAGE - 1) // STATIONS_PER_PAGE

    start = (page - 1) * STATIONS_PER_PAGE
    end = start + STATIONS_PER_PAGE
    paged_stations = station_names[start:end]

    links_html = "".join(
        f"<a href='/stream/{name}'>{name.replace('_', ' ').title()}</a>"
        for name in paged_stations
    )

    nav_html = ""
    if page > 1:
        nav_html += f"<a href='/?page=1'>⏮️ First</a>"
        nav_html += f"<a href='/?page={page - 1}'>◀️ Prev</a>"
    if page < total_pages:
        nav_html += f"<a href='/?page={page + 1}'>Next ▶️</a>"
        nav_html += f"<a href='/?page={total_pages}'>Last ⏭️</a>"

    html = f"""
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>🎧 Radio Streams</title>
        <style>
            body {{
                font-family: sans-serif;
                font-size: 14px;
                padding: 10px;
                margin: 0;
                background: #f0f0f0;
            }}
            h2 {{
                font-size: 16px;
                text-align: center;
                margin: 10px 0;
            }}
            a {{
                display: block;
                background: #007bff;
                color: white;
                text-decoration: none;
                padding: 8px;
                margin: 4px 0;
                border-radius: 6px;
                text-align: center;
                font-size: 13px;
            }}
            .nav {{
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
                margin-top: 10px;
                gap: 4px;
            }}
            .info {{
                font-size: 11px;
                text-align: center;
                margin-top: 8px;
                color: #555;
            }}
        </style>
    </head>
    <body>
        <h2>🎙️ Audio Streams (Page {page}/{total_pages})</h2>
        {links_html}
        <div class="nav">{nav_html}</div>
        <div class="info">🔢 T9 Keys: 1=First, 4=Prev, 6=Next, 3=Last, 5=Random, 0=Exit</div>

        <script>
        document.addEventListener("keydown", function(e) {{
            const key = e.key;
            let page = {page};
            let total = {total_pages};

            if (key === "1") {{
                window.location.href = "/?page=1";
            }} else if (key === "2") {{
                window.location.reload();
            }} else if (key === "3") {{
                window.location.href = "/?page=" + total;
            }} else if (key === "4" && page > 1) {{
                window.location.href = "/?page=" + (page - 1);
            }} else if (key === "5") {{
                const links = document.querySelectorAll("a[href^='/stream/']");
                const random = links[Math.floor(Math.random() * links.length)];
                if (random) random.click();
            }} else if (key === "6" && page < total) {{
                window.location.href = "/?page=" + (page + 1);
            }} else if (key === "7") {{
                window.scrollTo({{ top: 0, behavior: "smooth" }});
            }} else if (key === "8") {{
                window.scrollTo({{ top: document.body.scrollHeight, behavior: "smooth" }});
            }} else if (key === "9") {{
                window.location.href = "/?page=" + (page < total ? page + 1 : 1);
            }} else if (key === "0") {{
                window.location.href = "about:blank";
            }}
        }});
        </script>
    </body>
    </html>
    """
    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)