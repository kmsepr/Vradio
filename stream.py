import subprocess
import time
from flask import Flask, Response, redirect, request
import json
from pathlib import Path

app = Flask(__name__)

STATIONS_FILE = "radio_stations.json"

# Default stations grouped by category
DEFAULT_STATIONS = {
    "News": {
        "al_jazeera": "http://live-hls-audio-web-aja.getaj.net/VOICE-AJA/index.m3u8",
        "asianet_news": "https://vidcdn.vidgyor.com/asianet-origin/audioonly/chunks.m3u8",
        "vom_news": "https://psmnews.mv/stream/radio-dhivehi-raajjeyge-adu",
        "manorama_news": "http://103.199.161.254/Content/manoramanews/Live/Channel(ManoramaNews)/index.m3u8",
        "aaj_tak": "https://feeds.intoday.in/aajtak/api/aajtakhd/master.m3u8",
        "bloomberg_tv": "https://bloomberg-bloomberg-3-br.samsung.wurl.tv/manifest/playlist.m3u8",
        "france_24": "https://live.france24.com/hls/live/2037218/F24_EN_HI_HLS/master_500.m3u8",
        "n1_news": "https://best-str.umn.cdn.united.cloud/stream?stream=sp1400&sp=n1info&channel=n1bos&u=n1info&p=n1Sh4redSecre7iNf0&player=m3u8",
        "vom_radio": "https://radio.psm.mv/draair"
    },
    "Islamic": {
        "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
        "deenagers_radio": "http://104.7.66.64:8003/",
        "hajj_channel": "http://104.7.66.64:8005",
        "abc_islam": "http://s10.voscast.com:9276/stream",
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
        "rubat_ataq": "http://stream.zeno.fm/5tpfc8d7xqruv"
    },
    "Malayalam": {
        "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL",
        "malayalam_1": "http://167.114.131.90:5412/stream",
        "malayalam_90s": "https://stream-159.zeno.fm/gm3g9amzm0hvv?zs-x-7jq8ksTOav9ZhlYHi9xw",
        "radio_malayalam": "https://radiomalayalamfm.com/radio/8000/radio.mp3",
        "swaranjali": "https://stream-161.zeno.fm/x7mve2vt01zuv?zs-D4nK05-7SSK2FZAsvumh2w",
        "radio_beat_malayalam": "http://live.exertion.in:8050/radio.mp3",
        "shahul_radio": "https://stream-150.zeno.fm/cynbm5ngx38uv?zs=Ktca5StNRWm-sdIR7GloVg",
        "raja_radio": "http://159.203.111.241:8026/stream",
        "air_kavarati": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio189/chunklist.m3u8",
        "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
        "manjeri_fm": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio101/chunklist.m3u8",
        "real_fm": "http://air.pc.cdn.bitgravity.com/air/live/pbaudio083/playlist.m3u8",
        "dd_malayalam": "https://d3eyhgoylams0m.cloudfront.net/v1/manifest/93ce20f0f52760bf38be911ff4c91ed02aa2fd92/ed7bd2c7-8d10-4051-b397-2f6b90f99acb/562ee8f9-9950-48a0-ba1d-effa00cf0478/2.m3u8"
    },
    "Hindi": {
        "nonstop_hindi": "http://s5.voscast.com:8216/stream",
        "motivational_series": "http://104.7.66.64:8010"
    },
    "English": {
        # Currently none uniquely tagged as English only (bloomberg/france_24 are also in News)
    },
    "TV Channels": {
        "safari_tv": "https://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/chunks.m3u8",
        "victers_tv": "https://932y4x26ljv8-hls-live.5centscdn.com/victers/tv.stream/victers/tv1/chunks.m3u8",
        "kairali_we": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/wetv_nim_https/050522/wetv/playlist.m3u8",
        "flowers_tv": "http://103.199.161.254/Content/flowers/Live/Channel(Flowers)/index.m3u8",
        "amrita_tv": "https://dr1zhpsuem5f4.cloudfront.net/master.m3u8",
        "24_news": "https://segment.yuppcdn.net/110322/channel24/playlist.m3u8",
        "mazhavil_manorama": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/mazhavilmanorama_nim_https/050522/mazhavilmanorama/playlist.m3u8"
    },
    "Others": {
        "radio_digital_malayali": "https://radio.digitalmalayali.in/listen/stream/radio.mp3",
        "aural_oldies": "https://stream-162.zeno.fm/tksfwb1mgzzuv?zs=SxeQj1-7R0alsZSWJie5eQ",
        "fm_gold": "https://airhlspush.pc.cdn.bitgravity.com/httppush/hispbaudio005/hispbaudio00564kbps.m3u8",
        "eram_fm": "http://icecast2.edisimo.com:8000/eramfm.mp3"
    }
}

def load_data(filename, default_data):
    try:
        if Path(filename).exists():
            with open(filename, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return default_data

def save_data(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {filename}: {e}")

# Load stations from file or use default
RADIO_STATIONS = load_data(STATIONS_FILE, DEFAULT_STATIONS)

# Flatten station list for direct routing
FLAT_STATION_MAP = {
    station_id: url
    for category in RADIO_STATIONS.values()
    for station_id, url in category.items()
}

# FFmpeg stream generator
def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()
        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10", "-fflags", "nobuffer", "-flags", "low_delay",
                "-i", url, "-vn", "-ac", "1", "-b:a", "64k", "-f", "mp3", "-"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )
        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            process.kill()
            break
        except Exception as e:
            print(f"Stream error: {e}")
            time.sleep(5)

# Direct route like /al_jazeera
@app.route("/<station_id>")
def direct_stream(station_id):
    if station_id in FLAT_STATION_MAP:
        return Response(generate_stream(FLAT_STATION_MAP[station_id]), mimetype="audio/mpeg")
    return "Station not found", 404

# Delete station
@app.route("/delete/<category>/<station_name>", methods=["POST"])
def delete_station(category, station_name):
    if category in RADIO_STATIONS and station_name in RADIO_STATIONS[category]:
        del RADIO_STATIONS[category][station_name]
        if not RADIO_STATIONS[category]:
            del RADIO_STATIONS[category]
        save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

# Add station
@app.route("/add", methods=["POST"])
def add_station():
    category = request.form.get("category", "").strip()
    name = request.form.get("name", "").strip()
    url = request.form.get("url", "").strip()

    if not category or not name or not url:
        return "Missing fields", 400

    if category not in RADIO_STATIONS:
        RADIO_STATIONS[category] = {}
    RADIO_STATIONS[category][name] = url
    save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

# Home page
@app.route("/")
def index():
    categories_html = "".join(
        f"""
        <div class='category-card' onclick="showStations('{category}')">
            <h3>{category}</h3>
            <p>{len(stations)} stations</p>
        </div>
        """ for category, stations in RADIO_STATIONS.items()
    )

    stations_html = "".join(
        f"""
        <div class='station-card' data-category='{category}'>
            <div class='station-header'>
                <span class='station-name' onclick="playStream('/{name}')">{name.replace('_', ' ').title()}</span>
                <form method='POST' action='/delete/{category}/{name}' style='display:inline;'>
                    <button type='submit'>🗑️</button>
                </form>
            </div>
        </div>
        """ for category, stations in RADIO_STATIONS.items()
        for name in stations
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Radio</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                background: #111;
                color: #fff;
                font-family: sans-serif;
                padding: 20px;
            }}
            .categories {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 10px;
                margin-bottom: 20px;
            }}
            .category-card {{
                background: #222;
                padding: 15px;
                border-radius: 8px;
                cursor: pointer;
            }}
            .station-card {{
                background: #222;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 6px;
            }}
            .station-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            .station-name {{
                color: #4CAF50;
                font-weight: bold;
                cursor: pointer;
            }}
            button {{
                background: none;
                border: 1px solid #555;
                color: white;
                padding: 4px 8px;
                border-radius: 4px;
                cursor: pointer;
            }}
            input {{
                width: 100%;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 4px;
                border: none;
            }}
            .submit-btn {{
                background: #4CAF50;
                border: none;
                padding: 10px;
                color: white;
                border-radius: 4px;
                cursor: pointer;
                width: 100%;
            }}
            .back-button {{
                color: #4CAF50;
                margin-bottom: 10px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <h1>📻 Radio Stations</h1>
        <div id="categories" class="categories">{categories_html}</div>

        <div id="stations-container" style="display:none;">
            <div class="back-button" onclick="showCategories()">← Back</div>
            <div id="stations"></div>
        </div>

        <div id="add-form">
            <h2>Add New Station</h2>
            <form method="POST" action="/add">
                <input name="category" placeholder="Category (e.g. News)" required>
                <input name="name" placeholder="Station ID (e.g. al_jazeera)" required>
                <input name="url" placeholder="Stream URL (http://...)" required>
                <button class="submit-btn" type="submit">Add Station</button>
            </form>
        </div>

        <script>
            const allHTML = `{stations_html}`

            function showStations(category) {{
                document.getElementById('categories').style.display = 'none';
                document.getElementById('stations-container').style.display = 'block';
                document.getElementById('add-form').style.display = 'none'; // Hide add form
                const container = document.getElementById('stations');
                container.innerHTML = '';
                const temp = document.createElement('div');
                temp.innerHTML = allHTML;
                temp.querySelectorAll(`[data-category="${{category}}"]`).forEach(el => container.appendChild(el));
            }}

            function showCategories() {{
                document.getElementById('categories').style.display = 'grid';
                document.getElementById('stations-container').style.display = 'none';
                document.getElementById('add-form').style.display = 'block'; // Show add form
            }}

            function playStream(url) {{
                window.open(url, '_blank');
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    if not Path(STATIONS_FILE).exists():
        save_data(STATIONS_FILE, DEFAULT_STATIONS)
    app.run(host="0.0.0.0", port=8000, threaded=True)