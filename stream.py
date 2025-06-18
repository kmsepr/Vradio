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

# Initialize with default stations
DEFAULT_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL",
    # ... (include all your other default stations here) ...
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