import subprocess
import time
from flask import Flask, Response, send_from_directory
import os

app = Flask(__name__)

# 📡 List of radio stations
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL",
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
    "asianet_news": "https://vidcdn.vidgyor.com/asianet-origin/audioonly/chunks.m3u8",
    "air_kavarati": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio189/chunklist.m3u8",
    "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
    "manjeri_fm": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio101/chunklist.m3u8",
    "real_fm": "http://air.pc.cdn.bitgravity.com/air/live/pbaudio083/playlist.m3u8",
    "vom_news": "https://psmnews.mv/stream/radio-dhivehi-raajjeyge-adu",
    "safari_tv": "https://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/chunks.m3u8",
    "victers_tv": "https://932y4x26ljv8-hls-live.5centscdn.com/victers/tv.stream/victers/tv1/chunks.m3u8",
    "kairali_we": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/wetv_nim_https/050522/wetv/playlist.m3u8",
    "flowers_tv": "http://103.199.161.254/Content/flowers/Live/Channel(Flowers)/index.m3u8",
    "dd_malayalam": "https://d3eyhgoylams0m.cloudfront.net/v1/manifest/93ce20f0f52760bf38be911ff4c91ed02aa2fd92/ed7bd2c7-8d10-4051-b397-2f6b90f99acb/562ee8f9-9950-48a0-ba1d-effa00cf0478/2.m3u8",
    "amrita_tv": "https://dr1zhpsuem5f4.cloudfront.net/master.m3u8",
    "24_news": "https://segment.yuppcdn.net/110322/channel24/playlist.m3u8",
    "mazhavil_manorama": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/mazhavilmanorama_nim_https/050522/mazhavilmanorama/playlist.m3u8",
    "manorama_news": "http://103.199.161.254/Content/manoramanews/Live/Channel(ManoramaNews)/index.m3u8",
    "aaj_tak": "https://feeds.intoday.in/aajtak/api/aajtakhd/master.m3u8",
    "bloomberg_tv": "https://bloomberg-bloomberg-3-br.samsung.wurl.tv/manifest/playlist.m3u8",
    "france_24": "https://live.france24.com/hls/live/2037218/F24_EN_HI_HLS/master_500.m3u8",
    "n1_news": "https://best-str.umn.cdn.united.cloud/stream?stream=sp1400&sp=n1info&channel=n1bos&u=n1info&p=n1Sh4redSecre7iNf0&player=m3u8",
    "vom_radio": "https://radio.psm.mv/draair",
}

# 🔄 FFmpeg stream generator
def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()

        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10", "-fflags", "nobuffer", "-flags", "low_delay",
                "-i", url, "-vn", "-ac", "1", "-b:a", "64k", "-buffer_size", "1024k", "-f", "mp3", "-"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        print(f"🎵 Streaming from: {url} (Mono, 40kbps)")

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            process.kill()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")

        print("🔄 FFmpeg stopped, restarting stream...")
        time.sleep(5)

# 🌍 Route for station streaming
@app.route("/<station_name>")
def stream(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

# 🚀 Serve XML file
@app.route("/RVR/vr.xml")
def serve_xml():
    xml_file_path = os.path.join(os.getcwd(), "RVR", "vr.xml")
    if os.path.exists(xml_file_path):
        return send_from_directory(os.path.join(os.getcwd(), "RVR"), "vr.xml", mimetype="application/xml")
    else:
        return "⚠️ File not found", 404


# 📄 Serve TXT file at /Radiobee/radiobee.txt
@app.route("/Radiobee/radiobee.txt")
def serve_radiobee():
    txt_path = os.path.join(os.getcwd(), "Radiobee", "radiobee.txt")
    if os.path.exists(txt_path):
        return send_from_directory(os.path.join(os.getcwd(), "Radiobee"), "radiobee.txt", mimetype="text/plain")
    else:
        return "⚠️ File not found", 404



# 🏠 Homepage with links
@app.route("/")
def index():
    # Generate more subtle pastel-ish colors for cards
    def pastel_color(i):
        r = (100 + (i * 40)) % 256
        g = (150 + (i * 60)) % 256
        b = (200 + (i * 80)) % 256
        return f"{r}, {g}, {b}"

    links_html = "".join(
        f"""
        <div class='card' style='background-color: rgba({pastel_color(i)}, 0.85);'>
            <a href='/{name}' target='_blank' rel='noopener noreferrer'>{name}</a>
        </div>
        """ for i, name in enumerate(RADIO_STATIONS)
    )

    html = f"""
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Available Radio Streams</title>
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet" />
        <style>
            body {{
                font-family: 'Roboto', sans-serif;
                padding: 30px 20px;
                background: linear-gradient(135deg, #1e1e2f, #27293d);
                color: #eee;
                margin: 0;
                min-height: 100vh;
                display: flex;
                flex-direction: column;
            }}
            h1 {{
                text-align: center;
                font-weight: 700;
                font-size: 2.4rem;
                margin-bottom: 1rem;
                user-select: none;
            }}
            .grid {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 20px;
                max-width: 960px;
                margin: 0 auto;
                flex-grow: 1;
            }}
            @media (min-width: 600px) {{
                .grid {{
                    grid-template-columns: repeat(2, 1fr);
                }}
            }}
            @media (min-width: 900px) {{
                .grid {{
                    grid-template-columns: repeat(3, 1fr);
                }}
            }}
            .card {{
                padding: 25px;
                border-radius: 12px;
                text-align: center;
                font-weight: 700;
                font-size: 1.2rem;
                box-shadow: 0 6px 12px rgba(0,0,0,0.4);
                transition: transform 0.25s ease, box-shadow 0.25s ease;
                cursor: pointer;
                user-select: none;
            }}
            .card a {{
                color: #fff;
                text-decoration: none;
                display: block;
                outline-offset: 4px;
                outline-color: transparent;
                transition: outline-color 0.3s ease;
            }}
            .card:hover, .card:focus-within {{
                transform: scale(1.05);
                box-shadow: 0 10px 20px rgba(0,0,0,0.6);
            }}
            .card a:hover, .card a:focus {{
                outline-color: #fff;
                text-decoration: underline;
            }}
            footer {{
                text-align: center;
                font-size: 0.9rem;
                color: #aaa;
                padding: 15px 10px 0;
                user-select: none;
            }}
        </style>
    </head>
    <body>
        <h1>🎧 Available Radio Streams</h1>
        <div class="grid">
            {links_html}
        </div>
        <footer>© 2025 Your Radio App</footer>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
