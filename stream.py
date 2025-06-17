import subprocess
import time
from flask import Flask, Response, send_from_directory
from flask import request, redirect
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

@app.route("/add", methods=["POST"])
def add_station():
    name = request.form.get("name", "").strip().lower().replace(" ", "_")
    url = request.form.get("url", "").strip()
    if name and url:
        RADIO_STATIONS[name] = url
    return redirect("/")

def pastel_color(i):
    r = (100 + (i * 40)) % 256
    g = (150 + (i * 60)) % 256
    b = (200 + (i * 80)) % 256
    return f"{r}, {g}, {b}"

def generate_station_cards(stations):
    return "".join(
        f"""
        <div class='card' data-name='{name}' style='background-color: rgba({pastel_color(i)}, 0.85);'>
            <a href='/{name}' target='_blank' rel='noopener noreferrer'>{name}</a>
            <button class="fav-btn" onclick="toggleFavourite('{name}')">⭐</button>
        </div>
        """ for i, name in enumerate(stations)
    )

# 🏠 Homepage with tabs
@app.route("/", methods=["GET"])
def index():
    all_stations_html = generate_station_cards(RADIO_STATIONS.keys())
    
    return f"""
    <html>
    <head>
        <title>Radio Streams</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <style>
            body {{
                font-family: sans-serif;
                background: #1e1e2f;
                color: white;
                padding: 10px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                gap: 10px;
            }}
            .card {{
                padding: 12px;
                border-radius: 12px;
                text-align: center;
                background: #333;
                position: relative;
            }}
            .card a {{
                color: white;
                text-decoration: none;
            }}
            .fav-btn {{
                position: absolute;
                top: 5px;
                right: 10px;
                background: none;
                border: none;
                color: gold;
                font-size: 1.2rem;
                cursor: pointer;
            }}
            .tab-content {{
                display: none;
            }}
            .tab-content.active {{
                display: block;
            }}
            .tabs {{
                display: flex;
                margin-bottom: 15px;
                border-bottom: 1px solid #444;
            }}
            .tab {{
                padding: 10px 20px;
                cursor: pointer;
                background: #2a2a3a;
                margin-right: 5px;
                border-radius: 5px 5px 0 0;
            }}
            .tab.active {{
                background: #007acc;
            }}
            .add-station-form {{
                display: none;
                margin: 15px 0;
                flex-direction: column;
                gap: 5px;
                background: #2a2a3a;
                padding: 15px;
                border-radius: 5px;
            }}
            .add-station-form.active {{
                display: flex;
            }}
            input[type=text] {{
                padding: 8px;
                font-size: 1rem;
                border-radius: 5px;
                border: 1px solid #888;
                background: #333;
                color: white;
            }}
            input[type=submit] {{
                padding: 8px;
                background: #007acc;
                color: white;
                border: none;
                font-size: 1rem;
                border-radius: 5px;
                cursor: pointer;
            }}
            .add-icon {{
                position: fixed;
                bottom: 20px;
                right: 20px;
                background: #007acc;
                color: white;
                width: 50px;
                height: 50px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.5rem;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
            }}
        </style>
    </head>
    <body>
        <h1>📻 Radio Streams</h1>

        <div class="tabs">
            <div class="tab active" onclick="switchTab('all')">All Stations</div>
            <div class="tab" onclick="switchTab('favorites')">Favorites</div>
        </div>

        <div class="add-station-form" id="addForm">
            <h3>Add New Station</h3>
            <form method="POST" action="/add">
                <input type="text" name="name" placeholder="Station name (no space)" required />
                <input type="text" name="url" placeholder="Stream URL" required />
                <input type="submit" value="Add Station" />
            </form>
        </div>

        <div class="tab-content active" id="allStations">
            <div class="grid">{all_stations_html}</div>
        </div>

        <div class="tab-content" id="favorites">
            <div class="grid" id="favoritesGrid"></div>
        </div>

        <div class="add-icon" onclick="toggleAddForm()">+</div>

        <script>
            let currentTab = 'all';
            
            // Initialize favorites from localStorage
            let favorites = JSON.parse(localStorage.getItem("favorites")) || [];
            
            function switchTab(tab) {{
                document.querySelectorAll('.tab-content').forEach(content => {{
                    content.classList.remove('active');
                }});
                document.querySelectorAll('.tab').forEach(tabEl => {{
                    tabEl.classList.remove('active');
                }});
                
                document.getElementById(tab + 'Stations').classList.add('active');
                document.querySelector(`.tab[onclick="switchTab('${{tab}}')"]`).classList.add('active');
                currentTab = tab;
                
                if (tab === 'favorites') {{
                    updateFavoritesDisplay();
                }}
            }}
            
            function toggleFavourite(name) {{
                const index = favorites.indexOf(name);
                if (index === -1) {{
                    favorites.push(name);
                }} else {{
                    favorites.splice(index, 1);
                }}
                localStorage.setItem("favorites", JSON.stringify(favorites));
                updateDisplay();
                
                if (currentTab === 'favorites') {{
                    updateFavoritesDisplay();
                }}
            }}

            function updateDisplay() {{
                document.querySelectorAll(".card").forEach(card => {{
                    const name = card.getAttribute("data-name");
                    const btn = card.querySelector(".fav-btn");
                    if (favorites.includes(name)) {{
                        btn.textContent = "★";
                        btn.style.color = "gold";
                    }} else {{
                        btn.textContent = "⭐";
                        btn.style.color = "gold";
                    }}
                }});
            }}
            
            function updateFavoritesDisplay() {{
                const favoritesGrid = document.getElementById("favoritesGrid");
                favoritesGrid.innerHTML = "";
                
                favorites.forEach((name, i) => {{
                    const card = document.createElement("div");
                    card.className = "card";
                    card.setAttribute("data-name", name);
                    card.style.backgroundColor = `rgba(${{getPastelColor(i)}}, 0.85)`;
                    card.innerHTML = `
                        <a href="/${{name}}" target="_blank" rel="noopener noreferrer">${{name}}</a>
                        <button class="fav-btn" onclick="toggleFavourite('${{name}}')">★</button>
                    `;
                    favoritesGrid.appendChild(card);
                }});
            }}
            
            function getPastelColor(i) {{
                const r = (100 + (i * 40)) % 256;
                const g = (150 + (i * 60)) % 256;
                const b = (200 + (i * 80)) % 256;
                return `${{r}}, ${{g}}, ${{b}}`;
            }}
            
            function toggleAddForm() {{
                const form = document.getElementById("addForm");
                form.classList.toggle("active");
            }}

            window.onload = function() {{
                updateDisplay();
                // Force refresh to show newly added stations
                if (performance.navigation.type === 1) {{
                    updateFavoritesDisplay();
                }}
            }};
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)