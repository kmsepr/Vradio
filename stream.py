import os
import json
import time
import subprocess
from flask import Flask, Response, request, render_template_string, send_file, redirect, url_for

app = Flask(__name__)

# -----------------------
# CONFIGURATION
# -----------------------
STATIONS_FILE = "stations.json"

# Default built-in stations
RADIO_STATIONS = {
    "quran_radio_nablus": "http://www.quran-radio.org:8002/",
    "oman_radio": "https://partwota.cdn.mgmlcdn.com/omanrdoorg/omanrdo.stream_aac/chunklist.m3u8",
    "radio_digital_malayali": "https://radio.digitalmalayali.in/listen/stream/radio.mp3",
}

# Load user-added stations
if os.path.exists(STATIONS_FILE):
    with open(STATIONS_FILE, "r") as f:
        RADIO_STATIONS.update(json.load(f))


# -----------------------
# STREAMING LOGIC (unchanged)
# -----------------------
def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()

        cmd = [
            "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
            "-reconnect_delay_max", "10", "-fflags", "nobuffer", "-flags", "low_delay",
            "-i", url, "-vn", "-ac", "1", "-b:a", "40k", "-buffer_size", "1024k", "-f", "mp3", "-"
        ]

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192)
        print(f"🎵 Streaming from: {url}")

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            if process.poll() is None:
                process.kill()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")
        time.sleep(5)


@app.route("/<station_name>")
def stream(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")


# -----------------------
# HOME PAGE (New)
# -----------------------
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name", "").strip().lower().replace(" ", "_")
        url = request.form.get("url", "").strip()
        quality = request.form.get("quality", "medium")

        if not name or not url:
            return "⚠️ Please fill in all fields.", 400

        # Quality options affect FFmpeg audio bitrate (but just stored here)
        RADIO_STATIONS[name] = url

        # Save to file persistently
        with open(STATIONS_FILE, "w") as f:
            json.dump({k: v for k, v in RADIO_STATIONS.items() if k not in ["quran_radio_nablus", "oman_radio", "radio_digital_malayali"]}, f, indent=2)

        return redirect(url_for("home"))

    # Generate list HTML
    station_list_html = ""
    for name, url in RADIO_STATIONS.items():
        display = name.replace("_", " ").title()
        station_list_html += f"""
        <li>
            <a href="/play/{name}" class="station-link">▶ {display}</a>
        </li>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>📻 Add & Play Radio</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: sans-serif;
                background: #f5f5f5;
                color: #333;
                padding: 20px;
                max-width: 600px;
                margin: auto;
            }}
            h1 {{ text-align: center; color: #007BFF; }}
            form {{
                background: white;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            }}
            input, select {{
                width: 100%;
                padding: 10px;
                margin: 8px 0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
            button {{
                background: #007BFF;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                cursor: pointer;
            }}
            button:hover {{ background: #0056b3; }}
            ul {{ list-style: none; padding: 0; }}
            li {{
                background: white;
                margin: 8px 0;
                padding: 10px;
                border-radius: 8px;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }}
            a.station-link {{
                text-decoration: none;
                color: #333;
                font-weight: bold;
            }}
            a.station-link:hover {{ color: #007BFF; }}
            .backup {{
                display: block;
                text-align: center;
                margin-top: 15px;
                background: #28a745;
                color: white;
                padding: 10px;
                border-radius: 8px;
                text-decoration: none;
            }}
            .backup:hover {{ background: #218838; }}
        </style>
    </head>
    <body>
        <h1>📻 My Radio Stations</h1>
        <form method="POST">
            <input type="text" name="name" placeholder="Station name" required>
            <input type="url" name="url" placeholder="Streaming URL (http...)" required>
            <select name="quality" required>
                <option value="small">Small (Low)</option>
                <option value="medium" selected>Medium</option>
                <option value="best">Best (High)</option>
            </select>
            <button type="submit">➕ Add Station</button>
        </form>

        <ul>{station_list_html}</ul>

        <a href="/backup" class="backup">⬇️ Backup Stations JSON</a>
    </body>
    </html>
    """
    return render_template_string(html)


# -----------------------
# PLAYER PAGE (New)
# -----------------------
@app.route("/play/<station_name>")
def play(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404

    display = station_name.replace("_", " ").title()
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>▶ {display}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: sans-serif;
                text-align: center;
                background: #fafafa;
                padding: 40px;
            }}
            h2 {{ color: #007BFF; }}
            audio {{
                width: 100%;
                margin: 20px 0;
            }}
            button {{
                background: #28a745;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 5px;
                cursor: pointer;
            }}
            button:hover {{ background: #218838; }}
            a {{
                display: block;
                margin-top: 20px;
                text-decoration: none;
                color: #007BFF;
            }}
        </style>
        <script>
            function copyURL() {{
                navigator.clipboard.writeText("{url}");
                alert("Copied URL: {url}");
            }}
        </script>
    </head>
    <body>
        <h2>🎧 Now Playing: {display}</h2>
        <audio controls autoplay>
            <source src="/{station_name}" type="audio/mpeg">
        </audio>
        <button onclick="copyURL()">📋 Copy Stream URL</button>
        <a href="/">⬅️ Back to List</a>
    </body>
    </html>
    """
    return render_template_string(html)


# -----------------------
# BACKUP JSON DOWNLOAD
# -----------------------
@app.route("/backup")
def backup():
    if not os.path.exists(STATIONS_FILE):
        with open(STATIONS_FILE, "w") as f:
            json.dump({}, f)
    return send_file(STATIONS_FILE, as_attachment=True)


# -----------------------
# RUN APP
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)