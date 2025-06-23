from flask import Flask, Response, render_template_string
import subprocess
import time

app = Flask(__name__)

RADIO_STATIONS = {
    "air_calicut": "http://air.pc.cdn.bitgravity.com/air/live/pbaudio044/playlist.m3u8",
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
    display_names = {
        "air_calicut": "AIR Calicut 684 AM",
        "radio_nellikka": "Radio Nellikka",
        "muthnabi_radio": "Muthnabi Radio",
        "malayalam_1": "Malayalam Radio 1",
        "radio_digital_malayali": "Digital Malayali",
        "malayalam_90s": "Malayalam 90s Hits"
    }
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
    <meta name='viewport' content='width=device-width, initial-scale=1'>
    <title>Malayalam Radio</title>
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }
        body { 
            background: #111; 
            color: white; 
            font-family: Arial, sans-serif; 
            margin: 0;
            -webkit-tap-highlight-color: transparent;
        }
        h1 { 
            text-align: center; 
            font-size: 1.8rem; 
            padding: 20px; 
            background: linear-gradient(to right, #1a2a6c, #b21f1f, #fdbb2d);
            margin: 0; 
            color: white;
            text-shadow: 1px 1px 3px rgba(0,0,0,0.5);
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 20px; 
            padding: 20px; 
        }
        .card { 
            padding: 25px 15px; 
            border-radius: 12px; 
            text-align: center; 
            background: linear-gradient(135deg, #2c3e50, #4ca1af);
            cursor: pointer;
            font-size: 1.2rem;
            transition: all 0.3s;
            border: none;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        .card:hover, .card:focus { 
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
        }
        .card:focus {
            outline: none;
            box-shadow: 0 0 0 3px #4CAF50, 0 8px 16px rgba(0,0,0,0.3);
        }
        #miniPlayer {
            position: fixed; 
            bottom: 0; 
            left: 0; 
            width: 100%;
            background: linear-gradient(to right, #1a2a6c, #b21f1f);
            color: white; 
            padding: 15px;
            text-align: center; 
            display: none; 
            z-index: 1000;
            font-size: 1.3rem;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.5);
        }
        #playerModal {
            display: none; 
            position: fixed; 
            top: 0; 
            left: 0;
            width: 100%; 
            height: 100%; 
            background: rgba(0,0,0,0.9);
            z-index: 999; 
            text-align: center;
            padding: 20px; 
            box-sizing: border-box;
        }
        .player-content {
            max-width: 500px;
            margin: 0 auto;
            padding-top: 50px;
        }
        button {
            background: #4CAF50; 
            border: none; 
            color: white;
            padding: 20px; 
            font-size: 1.8rem;
            margin: 15px; 
            border-radius: 50%;
            min-width: 80px;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        button:active, button:focus { 
            background: #45a049; 
            outline: none;
            transform: scale(1.1);
            box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        }
        #volText {
            font-size: 1.5rem;
            margin: 20px 0;
            transition: all 0.2s;
        }
        .now-playing {
            font-size: 1.8rem;
            margin: 30px 0;
            color: #4CAF50;
            font-weight: bold;
            animation: fadeIn 0.5s;
        }
        .station-info {
            font-size: 1.2rem;
            margin: 10px 0;
            color: #ccc;
        }
        .close-btn {
            position: absolute;
            top: 20px;
            right: 20px;
            background: #f44336;
            padding: 10px 15px;
            border-radius: 5px;
            font-size: 1rem;
        }
        .frequency {
            font-size: 1.5rem;
            color: #FFD700;
            margin-top: 10px;
        }
        .control-hint {
            margin-top: 30px;
            color: #aaa;
            font-size: 1rem;
        }
    </style>
</head>
<body>
    <h1>📻 Malayalam Radio Stations</h1>
    <div class="grid">
        {% for id, name in display_names.items() %}
        <div class="card" tabindex="0" 
             onclick="playStation('{{ id }}')" 
             onkeydown="handleCardKey(event, '{{ id }}')">
            {{ name }}
            {% if id == 'air_calicut' %}
                <div class="frequency">684 AM</div>
            {% endif %}
        </div>
        {% endfor %}
    </div>

    <div id="miniPlayer" onclick="togglePlayer()">
        <span id="miniTitle">Select a station</span>
        <span id="miniStatus">⏸</span>
    </div>

    <div id="playerModal">
        <button class="close-btn" onclick="closePlayer()" aria-label="Close">✕ Close</button>
        <div class="player-content">
            <h2 id="playerTitle">Radio Player</h2>
            <div class="now-playing" id="nowPlaying"></div>
            <div class="station-info" id="stationInfo"></div>
            <audio id="modalAudio" controls style="width:100%; margin:30px 0;"></audio>
            
            <div class="controls">
                <button onclick="prev()" aria-label="Previous">⏮</button>
                <button onclick="togglePlay()" aria-label="Play/Pause" id="playBtn">⏯</button>
                <button onclick="next()" aria-label="Next">⏭</button>
            </div>
            <div>
                <button onclick="volumeDown()" aria-label="Volume Down">−</button>
                <button onclick="volumeUp()" aria-label="Volume Up">+</button>
                <div id="volText">Volume: 70%</div>
            </div>
            <div class="control-hint">
                <p>Controls: ↑ Previous | ↓ Next | ← Vol- | → Vol+</p>
            </div>
        </div>
    </div>

<script>
// Full JavaScript keypad + D-pad support for HMD 110

const stations = {{ station_names|tojson }};
const displayNames = {{ display_names|tojson }};
let current = -1;
const audio = document.getElementById('modalAudio');
const volText = document.getElementById('volText');
const miniStatus = document.getElementById("miniStatus");
const miniTitle = document.getElementById("miniTitle");
const playBtn = document.getElementById("playBtn");

function volumeUp() {
    audio.volume = Math.min(1, audio.volume + 0.1);
    localStorage.setItem('volume', audio.volume.toFixed(2));
    volText.innerText = `Volume: ${(audio.volume * 100).toFixed(0)}%`;
}
function volumeDown() {
    audio.volume = Math.max(0, audio.volume - 0.1);
    localStorage.setItem('volume', audio.volume.toFixed(2));
    volText.innerText = `Volume: ${(audio.volume * 100).toFixed(0)}%`;
}
function togglePlay() {
    if (audio.paused) {
        audio.play();
        playBtn.innerHTML = '⏸';
        miniStatus.textContent = "▶";
    } else {
        audio.pause();
        playBtn.innerHTML = '▶';
        miniStatus.textContent = "⏸";
    }
}
function prev() {
    if (current > 0) playStation(current - 1);
    else playStation(stations.length - 1);
}
function next() {
    if (current < stations.length - 1) playStation(current + 1);
    else playStation(0);
}
function togglePlayer() {
    const modal = document.getElementById("playerModal");
    if (modal.style.display === "block") {
        modal.style.display = "none";
    } else {
        modal.style.display = "block";
    }
}
function playStation(index) {
    current = parseInt(index);
    const id = stations[current];
    const name = displayNames[id];
    audio.src = '/' + id;
    audio.play();
    miniTitle.textContent = name;
    miniStatus.textContent = '▶';
    document.getElementById("nowPlaying").innerText = name;
}

document.addEventListener('keydown', function(e) {
    const key = e.key;
    const code = e.keyCode || e.which;
    const activeElement = document.activeElement;

    switch (code) {
        case 50: volumeUp(); e.preventDefault(); break;       // 2
        case 56: volumeDown(); e.preventDefault(); break;     // 8
        case 52: prev(); e.preventDefault(); break;           // 4
        case 54: next(); e.preventDefault(); break;           // 6
        case 53: togglePlay(); e.preventDefault(); break;     // 5
        case 49: togglePlayer(); e.preventDefault(); break;   // 1
    }

    if (activeElement.classList.contains('card')) {
        const cards = document.querySelectorAll('.card');
        const currentIndex = Array.from(cards).indexOf(activeElement);
        const cols = Math.floor(document.querySelector('.grid').offsetWidth / 200);

        switch(key) {
            case 'ArrowUp':
                if (currentIndex >= cols) cards[currentIndex - cols].focus();
                e.preventDefault();
                break;
            case 'ArrowDown':
                if (currentIndex < cards.length - cols) cards[currentIndex + cols].focus();
                e.preventDefault();
                break;
            case 'ArrowLeft':
                if (currentIndex > 0) cards[currentIndex - 1].focus();
                e.preventDefault();
                break;
            case 'ArrowRight':
                if (currentIndex < cards.length - 1) cards[currentIndex + 1].focus();
                e.preventDefault();
                break;
        }
    }
});
</script>
</body>
</html>
""", station_names=station_names, display_names=display_names)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)