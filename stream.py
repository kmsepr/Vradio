import subprocess
import time
from flask import Flask, Response, render_template_string

app = Flask(__name__)

RADIO_STATIONS = {
    "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL",
    "radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",
    # Add more stations here...
}

def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()
        process = subprocess.Popen([
            "ffmpeg",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_delay_max", "10",
            "-fflags", "nobuffer",
            "-flags", "low_delay",
            "-i", url,
            "-vn",
            "-ac", "1",
            "-b:a", "40k",
            "-buffer_size", "1024k",
            "-f", "mp3",
            "-"
        ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192)
        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            process.kill()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")
            time.sleep(5)

@app.route("/<station_name>")
def stream(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

@app.route("/")
def index():
    station_names = list(RADIO_STATIONS.keys())

    def pastel_color(i):
        r = (100 + (i * 40)) % 256
        g = (150 + (i * 60)) % 256
        b = (200 + (i * 80)) % 256
        return f"{r}, {g}, {b}"

    links_html = "".join(
        f"<div class='card' style='background-color: rgba({pastel_color(i)}, 0.85);' onclick='playStation({i})'>"
        f"{name} <span style='float:right;' onclick=\"toggleFav(event, '{name}')\">❤️</span></div>"
        for i, name in enumerate(station_names)
    )

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1' />
    <title>Radio</title>
    <style>
        body { background: #111; color: white; font-family: sans-serif; margin: 0; }
        .menu-icon { position: absolute; top: 10px; left: 10px; font-size: 1.5rem; cursor: pointer; z-index: 10; }
        .sidebar { position: fixed; left: -250px; top: 0; width: 220px; height: 100%; background: #222; padding: 15px; overflow-y: auto; transition: left 0.3s; z-index: 10; }
        .sidebar.open { left: 0; }
        h1 { font-size: 1.2rem; text-align: center; padding: 10px; background: #222; margin: 0; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; padding: 10px; margin-top: 50px; }
        .card { padding: 10px; border-radius: 8px; text-align: center; cursor: pointer; }
        .card:hover { opacity: 0.8; }

        #playerModal {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: #000;
            color: white;
            z-index: 999;
            padding: 20px;
            text-align: center;
        }

        #playerModal h2 { margin-top: 40px; font-size: 1.2rem; }
        #playerModal .close-btn {
            position: absolute;
            top: 10px;
            right: 20px;
            font-size: 1.5rem;
            cursor: pointer;
        }
        .controls {
            font-size: 2rem;
            margin: 20px;
        }
    </style>
</head>
<body>
    <div class='menu-icon' onclick='toggleSidebar()'>☰</div>
    <div class='sidebar' id='sidebar'>
        <div style='margin-bottom:10px;'>📚 <b>Favourites</b></div>
        <div id="favList"></div>
    </div>
    <h1>📻 Radio Stations</h1>
    <div class='grid'>
        {% for i, name in station_names|enumerate %}
        <div class='card' style='background-color: rgba({{ 100 + (i * 40) % 256 }}, {{ 150 + (i * 60) % 256 }}, {{ 200 + (i * 80) % 256 }}, 0.85);' onclick='playStation({{ i }})'>
            {{ name }} <span style='float:right;' onclick="toggleFav(event, '{{ name }}')">❤️</span>
        </div>
        {% endfor %}
    </div>

    <div id="playerModal">
        <div class="close-btn" onclick="closePlayer()">❌</div>
        <h2 id="playerTitle">🎶 Now Playing</h2>
        <div class="controls">
            <span onclick="prev()">⏮️</span>
            <span onclick="togglePlay()">⏯️</span>
            <span onclick="next()">⏭️</span>
        </div>
        <audio id="modalAudio" controls style="width:100%; margin-top:20px;"></audio>
        <div style="margin-top:10px;">
            <button onclick="volumeDown()">🔉</button>
            <button onclick="volumeUp()">🔊</button>
            <div id="volText" style="margin-top:5px;"></div>
        </div>
    </div>

<script>
    const stations = {{ station_names|tojson }};
    let current = -1;
    const audio = document.getElementById('modalAudio');
    const volText = document.getElementById('volText');

    function toggleSidebar() {
        document.getElementById('sidebar').classList.toggle('open');
    }

    function playStation(index) {
        current = index;
        const name = stations[current];
        audio.src = '/' + name;
        audio.play();
        document.getElementById("playerTitle").innerText = '🎶 Playing: ' + name;
        document.getElementById("playerModal").style.display = 'block';
        localStorage.setItem('lastStationIndex', current);
    }

    function togglePlay() {
        if (!audio.src) {
            const saved = localStorage.getItem('lastStationIndex');
            playStation(saved ? parseInt(saved) : 0);
        } else {
            if (audio.paused) audio.play();
            else audio.pause();
        }
    }

    function closePlayer() {
        document.getElementById("playerModal").style.display = 'none';
        audio.pause();
    }

    function prev() {
        if (current > 0) playStation(current - 1);
    }

    function next() {
        if (current < stations.length - 1) playStation(current + 1);
    }

    function getFavourites() {
        return JSON.parse(localStorage.getItem("favourites") || "[]");
    }

    function saveFavourites(favs) {
        localStorage.setItem("favourites", JSON.stringify(favs));
    }

    function toggleFav(e, name) {
        e.stopPropagation();
        let favs = getFavourites();
        if (favs.includes(name)) {
            favs = favs.filter(f => f !== name);
        } else {
            favs.push(name);
        }
        saveFavourites(favs);
        updateFavList();
    }

    function updateFavList() {
        const favs = getFavourites();
        const list = document.getElementById("favList");
        list.innerHTML = "";
        favs.forEach(name => {
            const div = document.createElement("div");
            div.innerHTML = "🎧 " + name;
            div.style = "padding:6px 0;cursor:pointer;border-bottom:1px solid #333;";
            div.onclick = () => playStation(stations.indexOf(name));
            list.appendChild(div);
        });
    }

    function volumeUp() {
        audio.volume = Math.min(1, audio.volume + 0.1);
        localStorage.setItem('volume', audio.volume.toFixed(2));
        showVolume();
    }

    function volumeDown() {
        audio.volume = Math.max(0, audio.volume - 0.1);
        localStorage.setItem('volume', audio.volume.toFixed(2));
        showVolume();
    }

    function showVolume() {
        volText.innerText = `🔊 Volume: ${(audio.volume * 100).toFixed(0)}%`;
    }

    document.addEventListener('keydown', function(e) {
        if (document.activeElement !== document.body) return;

        if (e.key === 'ArrowUp' || e.key === 'ArrowDown') e.preventDefault();

        switch (e.key) {
            case 'ArrowLeft': prev(); break;
            case 'ArrowRight': next(); break;
            case 'Enter': togglePlay(); break;
            case 'ArrowUp': volumeUp(); break;
            case 'ArrowDown': volumeDown(); break;
            case '1': toggleSidebar(); break;
        }
    });

    window.onload = function() {
        const savedIndex = parseInt(localStorage.getItem('lastStationIndex'));
        const savedVolume = parseFloat(localStorage.getItem('volume'));
        if (!isNaN(savedVolume)) audio.volume = savedVolume;
        if (!isNaN(savedIndex) && savedIndex >= 0 && savedIndex < stations.length) {
            playStation(savedIndex);
        } else if (stations.length > 0) {
            playStation(0);
        }
        updateFavList();
        showVolume();
    };
</script>
</body>
</html>
""", station_names=station_names) 

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)