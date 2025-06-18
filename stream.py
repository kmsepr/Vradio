import subprocess
import time
from flask import Flask, Response, redirect, request
import os
import json
from pathlib import Path

app = Flask(__name__)

# 📡 Persistent radio stations storage
STATIONS_FILE = "radio_stations.json"

# Initialize with default stations
DEFAULT_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL",
    # ... (include all your other default stations here) ...
}

def load_stations():
    """Load stations from file or use defaults"""
    try:
        if Path(STATIONS_FILE).exists():
            with open(STATIONS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Error loading stations: {e}")
    return DEFAULT_STATIONS

def save_stations(stations):
    """Save stations to file"""
    try:
        with open(STATIONS_FILE, 'w') as f:
            json.dump(stations, f)
    except Exception as e:
        print(f"⚠️ Error saving stations: {e}")

# Load stations at startup
RADIO_STATIONS = load_stations()

# 🔁 FFmpeg stream generator (unchanged)
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

# 🎧 Stream endpoint (unchanged)
@app.route("/<station_name>")
def stream(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

# ➕ Add new station (with persistence)
@app.route("/add", methods=["POST"])
def add_station():
    name = request.form.get("name", "").strip().lower().replace(" ", "_")
    url = request.form.get("url", "").strip()
    if name and url:
        RADIO_STATIONS[name] = url
        save_stations(RADIO_STATIONS)
    return redirect("/")

# 🗑️ Delete station endpoint
@app.route("/delete/<station_name>", methods=["POST"])
def delete_station(station_name):
    if station_name in RADIO_STATIONS:
        del RADIO_STATIONS[station_name]
        save_stations(RADIO_STATIONS)
    return redirect("/")

# 🏠 Homepage UI with delete buttons
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
            <a href='/{name}' target='_blank' rel='noopener noreferrer'>{name}</a>
            <div class='card-buttons'>
                <button class="fav-btn" onclick="toggleFavourite('{name}')">⭐</button>
                <form method='POST' action='/delete/{name}' style='display:inline;'>
                    <button type='submit' class='delete-btn'>🗑️</button>
                </form>
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
                position: relative;
            }}
            .card a {{
                color: white;
                text-decoration: none;
                display: block;
                margin-bottom: 10px;
            }}
            .card-buttons {{
                display: flex;
                justify-content: center;
                gap: 5px;
            }}
            .fav-btn, .delete-btn {{
                background: none;
                border: none;
                font-size: 1.2rem;
                cursor: pointer;
                padding: 0 5px;
            }}
            .fav-btn {{
                color: gold;
            }}
            .delete-btn {{
                color: #ff6b6b;
            }}
            .tab-content {{
                display: none;
            }}
            .tab-content.active {{
                display: block;
            }}
            .add-form {{
                max-width: 400px;
                margin: 20px auto;
                display: flex;
                flex-direction: column;
                gap: 10px;
                background: #2a2a3a;
                padding: 15px;
                border-radius: 8px;
            }}
            .add-form input {{
                padding: 10px;
                font-size: 1rem;
                border-radius: 5px;
                border: 1px solid #666;
                background: #1e1e2f;
                color: white;
            }}
            .add-form input[type=submit] {{
                background: #007acc;
                cursor: pointer;
                border: none;
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
            <h1>⭐ Favourite Radios</h1>
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
            <form class="add-form" method="POST" action="/add">
                <input type="text" name="name" placeholder="Station name (no space)" required />
                <input type="text" name="url" placeholder="Stream URL" required />
                <input type="submit" value="Add Station" />
            </form>
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
            }};
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    # Create storage file if it doesn't exist
    if not Path(STATIONS_FILE).exists():
        save_stations(DEFAULT_STATIONS)
    
    app.run(host="0.0.0.0", port=8000)