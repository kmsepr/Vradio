import subprocess
import time
from flask import Flask, Response, redirect, request, send_from_directory
import os
import json
from pathlib import Path
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
STATIONS_FILE = "radio_stations.json"
THUMBNAILS_FILE = "station_thumbnails.json"
UPLOAD_FOLDER = 'static/logos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 📡 List of radio stations
DEFAULT_STATIONS = {
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

DEFAULT_THUMBNAILS = {
    "muthnabi_radio": "/static/default-radio.png",
    "radio_keralam": "/static/default-radio.png",
    # ... (add default thumbnails for other stations) ...
}

def load_data(filename, default_data):
    """Load data from file or use defaults"""
    try:
        if Path(filename).exists():
            with open(filename, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading {filename}: {e}")
    return default_data

def save_data(filename, data):
    """Save data to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"⚠️ Error saving {filename}: {e}")

# Load data at startup
RADIO_STATIONS = load_data(STATIONS_FILE, DEFAULT_STATIONS)
STATION_THUMBNAILS = load_data(THUMBNAILS_FILE, DEFAULT_THUMBNAILS)

# 🔁 FFmpeg stream generator
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

# 🎧 Stream endpoint
@app.route("/<station_name>")
def stream(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

# ➕ Add new station
@app.route("/add", methods=["POST"])
def add_station():
    name = request.form.get("name", "").strip().lower().replace(" ", "_")
    url = request.form.get("url", "").strip()
    
    # Handle logo upload
    logo_url = STATION_THUMBNAILS.get(name, "/static/default-radio.png")
    logo = request.files.get("logo")
    if logo and logo.filename:
        filename = secure_filename(f"{name}_{logo.filename}")
        logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        logo_url = f"/static/logos/{filename}"
    
    if name and url:
        RADIO_STATIONS[name] = url
        STATION_THUMBNAILS[name] = logo_url
        save_data(STATIONS_FILE, RADIO_STATIONS)
        save_data(THUMBNAILS_FILE, STATION_THUMBNAILS)
    return redirect("/")

# ✏️ Edit station
@app.route("/edit/<old_name>", methods=["POST"])
def edit_station(old_name):
    new_name = request.form.get("name", "").strip().lower().replace(" ", "_")
    new_url = request.form.get("url", "").strip()
    
    if not new_name or not new_url:
        return redirect("/")
    
    # Handle logo update
    logo = request.files.get("logo")
    logo_url = STATION_THUMBNAILS.get(old_name, "/static/default-radio.png")
    if logo and logo.filename:
        filename = secure_filename(f"{new_name}_{logo.filename}")
        logo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        logo_url = f"/static/logos/{filename}"
    
    # Update station data
    if old_name in RADIO_STATIONS:
        # Preserve the stream if name didn't change
        if old_name != new_name:
            RADIO_STATIONS[new_name] = RADIO_STATIONS.pop(old_name)
        else:
            RADIO_STATIONS[new_name] = new_url
        
        # Update thumbnail
        STATION_THUMBNAILS[new_name] = logo_url
        if old_name != new_name and old_name in STATION_THUMBNAILS:
            del STATION_THUMBNAILS[old_name]
        
        save_data(STATIONS_FILE, RADIO_STATIONS)
        save_data(THUMBNAILS_FILE, STATION_THUMBNAILS)
    
    return redirect("/")

# 🗑️ Delete station
@app.route("/delete/<station_name>", methods=["POST"])
def delete_station(station_name):
    if station_name in RADIO_STATIONS:
        del RADIO_STATIONS[station_name]
        if station_name in STATION_THUMBNAILS:
            del STATION_THUMBNAILS[station_name]
        save_data(STATIONS_FILE, RADIO_STATIONS)
        save_data(THUMBNAILS_FILE, STATION_THUMBNAILS)
    return redirect("/")

# 🏠 Homepage UI
@app.route("/")
def index():
    def pastel_color(i):
        r = (100 + (i * 40)) % 256
        g = (150 + (i * 60)) % 256
        b = (200 + (i * 80)) % 256
        return f"{r}, {g}, {b}"

    links_html = "".join(
        f"""
        <div class='card' data-name='{name}' style='background-color: rgba({pastel_color(i)}, 0.85);'>
            <img src='{STATION_THUMBNAILS.get(name, "/static/default-radio.png")}' class='station-thumbnail'>
            <div class='station-info'>
                <a href='/{name}' target='_blank' rel='noopener noreferrer'>{name.replace('_', ' ').title()}</a>
                <div class='card-buttons'>
                    <button class="edit-btn" onclick="openEditModal('{name}', '{RADIO_STATIONS[name]}')">✏️</button>
                    <button class="fav-btn" onclick="toggleFavourite('{name}')">⭐</button>
                    <form method='POST' action='/delete/{name}' style='display:inline;'>
                        <button type='submit' class='delete-btn'>🗑️</button>
                    </form>
                </div>
            </div>
        </div>
        """ for i, name in enumerate(reversed(list(RADIO_STATIONS)))
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Radio Favourites</title>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            body {{
                font-family: sans-serif;
                background: #1e1e2f;
                color: white;
                margin: 0;
                padding: 0;
            }}
            .header {{
                display: flex;
                align-items: center;
                background: #2b2b3c;
                padding: 10px;
                position: sticky;
                top: 0;
                z-index: 100;
            }}
            .menu-icon {{
                font-size: 1.5rem;
                cursor: pointer;
                margin-right: 10px;
            }}
            .side-menu {{
                position: fixed;
                top: 0;
                left: -220px;
                width: 200px;
                height: 100%;
                background: #2b2b3c;
                padding-top: 60px;
                transition: left 0.3s;
                z-index: 999;
            }}
            .side-menu a {{
                display: block;
                padding: 12px 20px;
                color: white;
                text-decoration: none;
                border-bottom: 1px solid #444;
            }}
            .side-menu a:hover {{
                background-color: #444;
            }}
            h1 {{
                font-size: 1.2rem;
                margin: 0;
            }}
            .scroll-container {{
                max-height: 70vh;
                overflow-y: auto;
                padding: 10px;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
                gap: 12px;
            }}
            .card {{
                padding: 12px;
                border-radius: 10px;
                text-align: center;
            }}
            .station-thumbnail {{
                width: 60px;
                height: 60px;
                border-radius: 50%;
                object-fit: cover;
                border: 2px solid white;
                margin-bottom: 8px;
            }}
            .station-info {{
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            .card a {{
                color: white;
                text-decoration: none;
                word-break: break-word;
            }}
            .card-buttons {{
                display: flex;
                justify-content: center;
                gap: 5px;
            }}
            .fav-btn, .delete-btn, .edit-btn {{
                background: none;
                border: none;
                font-size: 1.2rem;
                cursor: pointer;
                padding: 0 5px;
            }}
            .fav-btn {{ color: gold; }}
            .delete-btn {{ color: #ff6b6b; }}
            .edit-btn {{ color: #4a90e2; }}
            .tab-content {{
                display: none;
            }}
            .tab-content.active {{
                display: block;
            }}
            .add-form, .edit-form {{
                max-width: 400px;
                margin: 20px auto;
                display: flex;
                flex-direction: column;
                gap: 10px;
                background: #2a2a3a;
                padding: 15px;
                border-radius: 8px;
            }}
            .add-form input, .edit-form input {{
                padding: 10px;
                font-size: 1rem;
                border-radius: 5px;
                border: 1px solid #666;
                background: #1e1e2f;
                color: white;
            }}
            .add-form input[type=submit], .edit-form input[type=submit] {{
                background: #007acc;
                cursor: pointer;
                border: none;
            }}
            .modal {{
                display: none;
                position: fixed;
                z-index: 1000;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.7);
            }}
            .modal-content {{
                background-color: #2a2a3a;
                margin: 15% auto;
                padding: 20px;
                border-radius: 8px;
                width: 80%;
                max-width: 500px;
            }}
            .close {{
                color: #aaa;
                float: right;
                font-size: 28px;
                cursor: pointer;
            }}
            @media (max-width: 600px) {{
                .grid {{
                    grid-template-columns: 1fr;
                }}
                .card {{
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <span class="menu-icon" onclick="toggleMenu()">☰</span>
            <h1><i class="fas fa-radio"></i> Radio Favourites</h1>
        </div>

        <div class="side-menu" id="sideMenu">
            <a href="#" onclick="showTab('all'); toggleMenu();">📻 All Stations</a>
            <a href="#" onclick="showTab('fav'); toggleMenu();">❤️ Favorites</a>
            <a href="#" onclick="showTab('add'); toggleMenu();">➕ Add Station</a>
        </div>

        <div id="favTab" class="tab-content">
            <div class="scroll-container">
                <div class="grid" id="favGrid"></div>
            </div>
        </div>

        <div id="allTab" class="tab-content active">
            <div class="scroll-container">
                <div class="grid" id="stationGrid">{links_html}</div>
            </div>
        </div>

        <div id="addTab" class="tab-content">
            <form class="add-form" method="POST" action="/add" enctype="multipart/form-data">
                <input type="text" name="name" placeholder="Station name" required>
                <input type="text" name="url" placeholder="Stream URL" required>
                <input type="file" name="logo" accept="image/*">
                <input type="submit" value="Add Station">
            </form>
        </div>

        <!-- Edit Modal -->
        <div id="editModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal()">&times;</span>
                <form class="edit-form" method="POST" enctype="multipart/form-data" id="editForm">
                    <input type="hidden" name="old_name" id="editOldName">
                    <input type="text" name="name" id="editName" placeholder="Station name" required>
                    <input type="text" name="url" id="editUrl" placeholder="Stream URL" required>
                    <input type="file" name="logo" accept="image/*">
                    <input type="submit" value="Save Changes">
                </form>
            </div>
        </div>

        <script>
            let activeTab = "all";

            function toggleFavourite(name) {{
                let favs = JSON.parse(localStorage.getItem("favourites") || "[]");
                if (favs.includes(name)) {{
                    favs = favs.filter(n => n !== name);
                }} else {{
                    favs.push(name);
                }}
                localStorage.setItem("favourites", JSON.stringify(favs));
                updateDisplay();
            }}

            function updateDisplay() {{
                const favs = JSON.parse(localStorage.getItem("favourites") || "[]");
                
                // Update favorite buttons
                document.querySelectorAll(".fav-btn").forEach(btn => {{
                    const card = btn.closest(".card");
                    const name = card.getAttribute("data-name");
                    btn.textContent = favs.includes(name) ? "★" : "⭐";
                }});
                
                // Update favorites tab
                const favGrid = document.getElementById("favGrid");
                if (favGrid) {{
                    favGrid.innerHTML = "";
                    favs.forEach(name => {{
                        const originalCard = document.querySelector(`.card[data-name='${{name}}']`);
                        if (originalCard) {{
                            const clone = originalCard.cloneNode(true);
                            favGrid.appendChild(clone);
                        }}
                    }});
                }}
            }}

            function showTab(tab) {{
                activeTab = tab;
                document.querySelectorAll(".tab-content").forEach(div => {{
                    div.classList.remove("active");
                }});
                document.getElementById(tab + "Tab").classList.add("active");
                updateDisplay();
            }}

            function toggleMenu() {{
                const menu = document.getElementById("sideMenu");
                menu.style.left = (menu.style.left === "0px") ? "-220px" : "0px";
            }}

            function openEditModal(name, url) {{
                document.getElementById('editModal').style.display = 'block';
                document.getElementById('editOldName').value = name;
                document.getElementById('editName').value = name.replace(/_/g, ' ');
                document.getElementById('editUrl').value = url;
                document.getElementById('editForm').action = `/edit/${{name}}`;
            }}

            function closeModal() {{
                document.getElementById('editModal').style.display = 'none';
            }}

            // Initialize
            window.onload = function() {{
                updateDisplay();
                // Close menu when clicking outside
                document.addEventListener('click', function(e) {{
                    const menu = document.getElementById("sideMenu");
                    if (!e.target.closest('.side-menu') && !e.target.closest('.menu-icon')) {{
                        menu.style.left = "-220px";
                    }}
                }});
                
                // Close modal when clicking outside
                window.onclick = function(event) {{
                    const modal = document.getElementById('editModal');
                    if (event.target == modal) {{
                        closeModal();
                    }}
                }};
            }};
        </script>
    </body>
    </html>
    """

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == "__main__":
    # Create storage files if they don't exist
    if not Path(STATIONS_FILE).exists():
        save_data(STATIONS_FILE, DEFAULT_STATIONS)
    if not Path(THUMBNAILS_FILE).exists():
        save_data(THUMBNAILS_FILE, DEFAULT_THUMBNAILS)
    
    # Create default radio image if missing
    default_logo_path = Path('static/default-radio.png')
    if not default_logo_path.exists():
        os.makedirs('static', exist_ok=True)
        # You should add a real default image here
    
    app.run(host="0.0.0.0", port=8000)