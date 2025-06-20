import subprocess
import time
import json
import os
from flask import Flask, Response, request, redirect

app = Flask(__name__)

# 📁 Persistent bookmarks file inside volume
BOOKMARKS_FILE = os.path.join("/mnt/data", "bookmarks.json")

# 🔖 Load bookmarks
try:
    with open(BOOKMARKS_FILE, "r") as f:
        BOOKMARKS = json.load(f)
except:
    BOOKMARKS = [{"name": "Add", "url": "/add"}]

# 📡 Radio stations
RADIO_STATIONS = {
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL",
    "malayalam_1": "http://167.114.131.90:5412/stream",
    "radio_digital_malayali": "https://radio.digitalmalayali.in/listen/stream/radio.mp3",
    # (add more as needed)
}

# 🔁 FFmpeg stream proxy
def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()
        process = subprocess.Popen(
            ["ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
             "-reconnect_delay_max", "10", "-fflags", "nobuffer", "-flags", "low_delay",
             "-i", url, "-vn", "-ac", "1", "-b:a", "40k", "-buffer_size", "1024k", "-f", "mp3", "-"],
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
        print("🔄 Restarting stream...")
        time.sleep(5)

# 🎧 Stream route
@app.route("/<station_name>")
def stream(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

# ➕ Add bookmark/station
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        url = request.form.get("url", "").strip()
        if name and url:
            if url.startswith("http") and "stream" in url:
                key = name.lower().replace(" ", "_")
                RADIO_STATIONS[key] = url
            else:
                BOOKMARKS.append({"name": name, "url": url})
                with open(BOOKMARKS_FILE, "w") as f:
                    json.dump(BOOKMARKS, f)
        return redirect("/")
    return """
    <html><body style='background:#111;color:white;padding:20px;font-family:sans-serif;'>
    <h2>Add Bookmark or Station</h2>
    <form method='post'>
        <input name='name' placeholder='Name' required style='width:100%;padding:10px;background:#333;color:white;border:none;margin:10px 0;' />
        <input name='url' placeholder='URL (bookmark or stream)' required style='width:100%;padding:10px;background:#333;color:white;border:none;margin:10px 0;' />
        <button type='submit' style='padding:10px;background:green;color:white;border:none;width:100%'>Add</button>
    </form>
    </body></html>
    """

# ❌ Delete bookmark
@app.route("/delete_bookmark", methods=["POST"])
def delete_bookmark():
    name = request.form.get("name", "")
    global BOOKMARKS
    BOOKMARKS = [b for b in BOOKMARKS if b["name"] != name]
    with open(BOOKMARKS_FILE, "w") as f:
        json.dump(BOOKMARKS, f)
    return redirect("/")

# 🏠 Homepage
@app.route("/")
def index():
    def pastel_color(i):
        r = (100 + (i * 40)) % 256
        g = (150 + (i * 60)) % 256
        b = (200 + (i * 80)) % 256
        return f"{r}, {g}, {b}"

    links_html = "".join(
        f"<div class='card' data-name='{name}' style='background-color: rgba({pastel_color(i)}, 0.85);'><a href='/{name}' target='_blank'>{name}</a></div>"
        for i, name in enumerate(reversed(list(RADIO_STATIONS)))
    )

    bookmarks_html = ""
    for b in BOOKMARKS:
        if b["name"].lower() == "add":
            bookmarks_html += f"<a href='{b['url']}' style='color:white;text-decoration:none;border-bottom:1px solid #333;padding:8px 0;display:block;'>➕ {b['name']}</a>"
        else:
            bookmarks_html += f"""
            <div style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #333;">
                <a href="{b['url']}" style="flex:1;color:white;text-decoration:none;padding:8px 0;">{b['name']}</a>
                <form method="post" action="/delete_bookmark" style="margin:0;padding:0;">
                    <input type="hidden" name="name" value="{b['name']}">
                    <button style="background:none;border:none;color:#f44;font-size:1rem;cursor:pointer;">🗑️</button>
                </form>
            </div>
            """

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Radio</title>
        <style>
            body {{
                font-family: sans-serif;
                margin: 0;
                background: #111;
                color: white;
            }}
            h1 {{
                font-size: 1.2rem;
                text-align: center;
                padding: 10px;
                background: #222;
                margin: 0;
            }}
            .menu-icon {{
                position: absolute;
                top: 10px;
                left: 10px;
                font-size: 1.5rem;
                cursor: pointer;
                z-index: 1001;
            }}
            .sidebar {{
                position: fixed;
                left: -250px;
                top: 0;
                width: 220px;
                height: 100%;
                background: #222;
                padding: 15px;
                overflow-y: auto;
                transition: left 0.3s;
                z-index: 1000;
            }}
            .sidebar.open {{
                left: 0;
            }}
            .grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 10px;
                padding: 10px;
                margin-top: 50px;
            }}
            .card {{
                padding: 10px;
                border-radius: 8px;
                text-align: center;
                background: #333;
            }}
            .card a {{
                text-decoration: none;
                color: white;
                font-size: 0.95rem;
                display: block;
            }}
        </style>
        <script>
            function toggleSidebar() {{
                document.getElementById('sidebar').classList.toggle('open');
            }}
            document.addEventListener('keydown', function(e) {{
                if (e.key === '1') {{
                    toggleSidebar();
                }}
            }});
        </script>
    </head>
    <body>
        <div class="menu-icon" onclick="toggleSidebar()">☰</div>
        <div class="sidebar" id="sidebar">
            {bookmarks_html}
        </div>
        <h1>📻 Radio Stations</h1>
        <div class="grid">{links_html}</div>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)