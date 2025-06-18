import subprocess
import time
from flask import Flask, Response, redirect, request, send_from_directory
import os
import json
from pathlib import Path

app = Flask(__name__)

# Configuration
STATIONS_FILE = "radio_stations.json"
UPLOAD_FOLDER = 'static/logos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Radio stations organized by category
DEFAULT_STATIONS = {
    "News": {
        "al_jazeera": "http://live-hls-audio-web-aja.getaj.net/VOICE-AJA/index.m3u8",
        "asianet_news": "https://vidcdn.vidgyor.com/asianet-origin/audioonly/chunks.m3u8",
        "24_news": "https://segment.yuppcdn.net/110322/channel24/playlist.m3u8"
    },
    "Islamic": {
        "deenagers_radio": "http://104.7.66.64:8003/",
        "hajj_channel": "http://104.7.66.64:8005",
        "abc_islam": "http://s10.voscast.com:9276/stream"
    },
    "Malayalam": {
        "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
        "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL",
        "malayalam_1": "http://167.114.131.90:5412/stream"
    }
}

def load_data(filename, default_data):
    """Load data from file or use defaults"""
    try:
        if Path(filename).exists():
            with open(filename, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return default_data

def save_data(filename, data):
    """Save data to file"""
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {filename}: {e}")

# Load data at startup
RADIO_STATIONS = load_data(STATIONS_FILE, DEFAULT_STATIONS)

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
            print(f"Stream error: {e}")
            time.sleep(5)

@app.route("/<category>/<station_name>")
def stream(category, station_name):
    if category in RADIO_STATIONS and station_name in RADIO_STATIONS[category]:
        url = RADIO_STATIONS[category][station_name]
        return Response(generate_stream(url), mimetype="audio/mpeg")
    return "Station not found", 404

@app.route("/add/<category>", methods=["POST"])
def add_station(category):
    name = request.form.get("name", "").strip().lower().replace(" ", "_")
    url = request.form.get("url", "").strip()

    if name and url:
        if category not in RADIO_STATIONS:
            RADIO_STATIONS[category] = {}
        RADIO_STATIONS[category][name] = url
        save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

@app.route("/edit/<category>/<old_name>", methods=["POST"])
def edit_station(category, old_name):
    new_name = request.form.get("name", "").strip().lower().replace(" ", "_")
    new_url = request.form.get("url", "").strip()
    new_category = request.form.get("category", category)

    if not new_name or not new_url:
        return redirect("/")

    if category in RADIO_STATIONS and old_name in RADIO_STATIONS[category]:
        # Remove from old category if category changed
        if new_category != category:
            RADIO_STATIONS[category].pop(old_name)
            if new_category not in RADIO_STATIONS:
                RADIO_STATIONS[new_category] = {}
            RADIO_STATIONS[new_category][new_name] = new_url
        else:
            # Just update within same category
            RADIO_STATIONS[category].pop(old_name)
            RADIO_STATIONS[category][new_name] = new_url

        save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

@app.route("/delete/<category>/<station_name>", methods=["POST"])
def delete_station(category, station_name):
    if category in RADIO_STATIONS and station_name in RADIO_STATIONS[category]:
        del RADIO_STATIONS[category][station_name]
        # Remove category if empty
        if not RADIO_STATIONS[category]:
            del RADIO_STATIONS[category]
        save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

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
            <div class='station-info'>
                <a href='/{category}/{name}' target='_blank'>{name.replace('_', ' ').title()}</a>
                <div class='station-actions'>
                    <button onclick="openEditModal('{category}', '{name}', '{url}')">✏️</button>
                    <form method='POST' action='/delete/{category}/{name}' style='display:inline;'>
                        <button type='submit'>🗑️</button>
                    </form>
                </div>
            </div>
        </div>
        """ for category, stations in RADIO_STATIONS.items() 
        for name, url in stations.items()
    )

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Radio Stations</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
            }}
            .categories {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }}
            .category-card {{
                background: #fff;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                cursor: pointer;
                transition: transform 0.2s;
            }}
            .category-card:hover {{
                transform: translateY(-3px);
            }}
            .category-card h3 {{
                margin: 0 0 5px 0;
                color: #333;
            }}
            .category-card p {{
                margin: 0;
                color: #666;
                font-size: 0.9em;
            }}
            .stations-container {{
                display: none;
            }}
            .stations {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                gap: 15px;
            }}
            .station-card {{
                background: #fff;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .station-info a {{
                color: #0066cc;
                text-decoration: none;
                font-weight: bold;
            }}
            .station-actions {{
                margin-top: 10px;
                display: flex;
                gap: 10px;
            }}
            .station-actions button {{
                background: none;
                border: 1px solid #ddd;
                padding: 5px 10px;
                border-radius: 4px;
                cursor: pointer;
            }}
            .add-station-form {{
                background: #fff;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                margin-top: 20px;
                max-width: 500px;
            }}
            .add-station-form input, .add-station-form select {{
                width: 100%;
                padding: 8px;
                margin-bottom: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .add-station-form button {{
                background: #4CAF50;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
            }}
            .modal {{
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 1000;
                justify-content: center;
                align-items: center;
            }}
            .modal-content {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                width: 80%;
                max-width: 500px;
            }}
            .close {{
                float: right;
                cursor: pointer;
                font-size: 1.5em;
            }}
            .back-button {{
                margin-bottom: 15px;
                cursor: pointer;
                color: #0066cc;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <h1>Radio Stations</h1>
        
        <div id="categories" class="categories">
            {categories_html}
        </div>
        
        <div id="stations-container" class="stations-container">
            <div class="back-button" onclick="showCategories()">← Back to Categories</div>
            <div id="stations" class="stations"></div>
        </div>
        
        <div class="add-station-form">
            <h3>Add New Station</h3>
            <form method="POST" action="/add/" id="addForm">
                <select name="category" required>
                    <option value="">Select Category</option>
                    {''.join(f'<option value="{category}">{category}</option>' for category in RADIO_STATIONS)}
                    <option value="new">New Category</option>
                </select>
                <input type="text" id="newCategory" name="new_category" placeholder="New Category Name" style="display: none;">
                <input type="text" name="name" placeholder="Station Name" required>
                <input type="text" name="url" placeholder="Stream URL" required>
                <button type="submit">Add Station</button>
            </form>
        </div>
        
        <div id="editModal" class="modal">
            <div class="modal-content">
                <span class="close" onclick="closeModal()">&times;</span>
                <h3>Edit Station</h3>
                <form method="POST" action="" id="editForm">
                    <input type="hidden" name="old_name" id="editOldName">
                    <input type="hidden" name="category" id="editCategory">
                    <select name="new_category" required>
                        {''.join(f'<option value="{category}">{category}</option>' for category in RADIO_STATIONS)}
                    </select>
                    <input type="text" name="name" id="editName" placeholder="Station Name" required>
                    <input type="text" name="url" id="editUrl" placeholder="Stream URL" required>
                    <button type="submit">Save Changes</button>
                </form>
            </div>
        </div>
        
        <script>
            // Store all stations HTML
            const allStationsHTML = `{stations_html}`;
            
            function showStations(category) {{
                document.getElementById('categories').style.display = 'none';
                document.getElementById('stations-container').style.display = 'block';
                
                const stationsContainer = document.getElementById('stations');
                stationsContainer.innerHTML = '';
                
                // Filter stations by category and add to container
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = allStationsHTML;
                
                const stationsInCategory = tempDiv.querySelectorAll(`.station-card[data-category='${{category}}']`);
                stationsInCategory.forEach(station => {{
                    stationsContainer.appendChild(station.cloneNode(true));
                }});
            }}
            
            function showCategories() {{
                document.getElementById('categories').style.display = 'grid';
                document.getElementById('stations-container').style.display = 'none';
            }}
            
            function openEditModal(category, name, url) {{
                document.getElementById('editModal').style.display = 'flex';
                document.getElementById('editOldName').value = name;
                document.getElementById('editName').value = name.replace(/_/g, ' ');
                document.getElementById('editUrl').value = url;
                document.getElementById('editCategory').value = category;
                document.getElementById('editForm').action = `/edit/${{category}}/${{name}}`;
                
                // Set the current category as selected
                const select = document.querySelector('#editForm select[name="new_category"]');
                for (let i = 0; i < select.options.length; i++) {{
                    if (select.options[i].value === category) {{
                        select.selectedIndex = i;
                        break;
                    }}
                }}
            }}
            
            function closeModal() {{
                document.getElementById('editModal').style.display = 'none';
            }}
            
            // Show/hide new category field based on selection
            document.querySelector('select[name="category"]').addEventListener('change', function() {{
                const newCategoryField = document.getElementById('newCategory');
                newCategoryField.style.display = this.value === 'new' ? 'block' : 'none';
                if (this.value !== 'new') {{
                    newCategoryField.value = '';
                }}
            }});
            
            // Update form action with selected category
            document.querySelector('#addForm').addEventListener('submit', function() {{
                const categorySelect = this.querySelector('select[name="category"]');
                let category = categorySelect.value;
                
                if (category === 'new') {{
                    category = this.querySelector('input[name="new_category"]').value.trim();
                }}
                
                this.action = `/add/${{encodeURIComponent(category)}}`;
            }});
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    if not Path(STATIONS_FILE).exists():
        save_data(STATIONS_FILE, DEFAULT_STATIONS)
    app.run(host="0.0.0.0", port=8000)