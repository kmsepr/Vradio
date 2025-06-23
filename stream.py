from flask import Flask, Response, render_template_string
import subprocess
import time

app = Flask(__name__)

RADIO_STATIONS = {
    "radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "malayalam_1": "http://167.114.131.90:5412/stream",
    "radio_digital_malayali": "https://radio.digitalmalayali.in/listen/stream/radio.mp3",
    "malayalam_90s": "https://stream-159.zeno.fm/gm3g9amzm0hvv?zs-x-7jq8ksTOav9ZhlYHi9xw",
}

def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()
        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10", "-fflags", "nobuffer",
                "-flags", "low_delay", "-i", url, "-vn", "-ac", "1",
                "-b:a", "40k", "-buffer_size", "1024k", "-f", "mp3", "-"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=8192
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

@app.route("/<station_name>")
def stream(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "Station not found", 404
    return Response(generate_stream(url), mimetype="audio/mpeg")

@app.route("/")
def index():
    station_names = list(RADIO_STATIONS.keys())
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>Radio</title>
    <style>
        body { background: #111; color: white; font-family: sans-serif; margin: 0; }
        h1 { text-align: center; font-size: 1.2rem; padding: 10px; background: #222; margin: 0; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; padding: 10px; }
        .card { padding: 10px; border-radius: 8px; text-align: center; background: #333; cursor: pointer; }
        .card:hover { background: #555; }
        #miniPlayer {
            position: fixed; top: 0; left: 0; width: 100%;
            background: #222; color: white; padding: 8px;
            text-align: center; display: none; z-index: 1000;
        }
        #playerModal {
            display: none; position: fixed; top: 40px; left: 0;
            width: 100%; height: calc(100% - 40px); background: #000;
            z-index: 999; text-align: center;
            padding: 15px; box-sizing: border-box;
        }
        button {
            background: #444; border: none; color: white;
            padding: 10px 14px; font-size: 1.2rem;
            margin: 4px; border-radius: 8px;
        }
        button:active { background: #666; }
    </style>
</head>
<body>
    <h1>📻 Radio Stations</h1>
    <div class="grid">
        {% for name in station_names %}
        <div class="card" onclick="playStation('{{ loop.index0 }}')">{{ name }}</div>
        {% endfor %}
    </div>

    <div id="miniPlayer" onclick="togglePlayer()">
        🎶 <span id="miniTitle">Now Playing</span> ⬇️
    </div>

    <div id="playerModal">
        <h2 id="playerTitle">🎶 Now Playing</h2>
        <audio id="modalAudio" controls style="width:100%; margin-top:20px;"></audio>
        <div class="controls">
            <button onclick="prev()">⏮️</button>
            <button onclick="togglePlay()">⏯️</button>
            <button onclick="next()">⏭️</button>
        </div>
        <div>
            <button onclick="volumeDown()">🔉</button>
            <button onclick="volumeUp()">🔊</button>
            <div id="volText"></div>
        </div>
    </div>

<script>
    const stations = {{ station_names|tojson }};
    let current = -1;
    let isOpen = false;
    const audio = document.getElementById('modalAudio');
    const volText = document.getElementById('volText');
    const miniPlayer = document.getElementById("miniPlayer");
    const playerModal = document.getElementById("playerModal");

    function playStation(index) {
        current = parseInt(index);
        const name = stations[current];
        audio.src = '/' + name;
        audio.play();
        document.getElementById("playerTitle").innerText = '🎶 Playing: ' + name;
        document.getElementById("miniTitle").innerText = name;
        miniPlayer.style.display = 'block';
        openPlayer();
        localStorage.setItem('lastStationIndex', current);
    }

    function togglePlay() {
        if (!audio.src) {
            const saved = localStorage.getItem('lastStationIndex');
            if (saved) playStation(saved);
        } else {
            if (audio.paused) audio.play(); else audio.pause();
        }
    }

    function prev() {
        if (current > 0) playStation(current - 1);
    }

    function next() {
        if (current < stations.length - 1) playStation(current + 1);
    }

    function openPlayer() {
        playerModal.style.display = 'block';
        isOpen = true;
    }

    function closePlayer() {
        playerModal.style.display = 'none';
        isOpen = false;
    }

    function togglePlayer() {
        isOpen ? closePlayer() : openPlayer();
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

    // Keypad mapping
    document.addEventListener('keydown', function(e) {
        switch (e.key) {
            case '1': togglePlayer(); break;      // Mini player toggle
            case '2': volumeUp(); break;          // Volume up
            case '8': volumeDown(); break;        // Volume down
            case '4': prev(); break;              // Previous
            case '6': next(); break;              // Next
            case '5': togglePlay(); break;        // Play/Pause
        }
    });

    window.onload = function() {
        const savedIndex = parseInt(localStorage.getItem('lastStationIndex'));
        const savedVolume = parseFloat(localStorage.getItem('volume'));
        if (!isNaN(savedVolume)) audio.volume = savedVolume;
        if (!isNaN(savedIndex)) playStation(savedIndex);
        showVolume();
    }
</script>
</body>
</html>
""", station_names=station_names)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)