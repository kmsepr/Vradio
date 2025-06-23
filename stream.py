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
        body { 
            background: #111; 
            color: white; 
            font-family: sans-serif; 
            margin: 0;
            -webkit-tap-highlight-color: transparent;
        }
        h1 { 
            text-align: center; 
            font-size: 1.5rem; 
            padding: 15px; 
            background: #222; 
            margin: 0; 
        }
        .grid { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
            gap: 15px; 
            padding: 15px; 
        }
        .card { 
            padding: 20px 10px; 
            border-radius: 8px; 
            text-align: center; 
            background: #333; 
            cursor: pointer;
            font-size: 1.1rem;
            transition: all 0.2s;
            border: 2px solid transparent;
        }
        .card:hover, .card:focus { 
            background: #555; 
            transform: scale(1.03);
        }
        .card:focus {
            outline: none;
            border-color: #4CAF50;
            box-shadow: 0 0 10px #4CAF50;
        }
        #miniPlayer {
            position: fixed; 
            top: 0; 
            left: 0; 
            width: 100%;
            background: #222; 
            color: white; 
            padding: 12px;
            text-align: center; 
            display: none; 
            z-index: 1000;
            font-size: 1.2rem;
        }
        #playerModal {
            display: none; 
            position: fixed; 
            top: 60px; 
            left: 0;
            width: 100%; 
            height: calc(100% - 60px); 
            background: #000;
            z-index: 999; 
            text-align: center;
            padding: 20px; 
            box-sizing: border-box;
        }
        button {
            background: #444; 
            border: none; 
            color: white;
            padding: 15px 20px; 
            font-size: 1.5rem;
            margin: 10px; 
            border-radius: 50%;
            min-width: 60px;
            cursor: pointer;
            transition: all 0.2s;
        }
        button:active, button:focus { 
            background: #666; 
            outline: none;
            transform: scale(1.1);
        }
        #volText {
            font-size: 1.2rem;
            margin: 15px 0;
        }
        .now-playing {
            font-size: 1.3rem;
            margin: 20px 0;
            color: #4CAF50;
        }
    </style>
</head>
<body>
    <h1>📻 Malayalam Radio Stations</h1>
    <div class="grid">
        {% for name in station_names %}
        <div class="card" tabindex="0" 
             onclick="playStation('{{ loop.index0 }}')" 
             onkeydown="handleCardKey(event, '{{ loop.index0 }}')">
            {{ name }}
        </div>
        {% endfor %}
    </div>

    <div id="miniPlayer" onclick="togglePlayer()">
        <span id="miniTitle">Select a station</span>
    </div>

    <div id="playerModal">
        <h2 id="playerTitle">Radio Player</h2>
        <div class="now-playing" id="nowPlaying"></div>
        <audio id="modalAudio" controls style="width:100%; margin:20px 0;"></audio>
        <div class="controls">
            <button onclick="prev()" aria-label="Previous">⏮️</button>
            <button onclick="togglePlay()" aria-label="Play/Pause" id="playBtn">⏯️</button>
            <button onclick="next()" aria-label="Next">⏭️</button>
        </div>
        <div>
            <button onclick="volumeDown()" aria-label="Volume Down">🔉</button>
            <button onclick="volumeUp()" aria-label="Volume Up">🔊</button>
            <div id="volText">Volume: 100%</div>
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
    const nowPlaying = document.getElementById("nowPlaying");
    const playBtn = document.getElementById("playBtn");

    function handleCardKey(event, index) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            playStation(index);
        }
    }

    function playStation(index) {
        current = parseInt(index);
        const name = stations[current];
        audio.src = '/' + name;
        audio.play().catch(e => console.log("Play error:", e));
        document.getElementById("playerTitle").innerText = 'Now Playing';
        nowPlaying.innerText = name;
        document.getElementById("miniTitle").innerText = name;
        miniPlayer.style.display = 'block';
        openPlayer();
        localStorage.setItem('lastStationIndex', current);
        playBtn.focus();
    }

    function togglePlay() {
        if (!audio.src) {
            const saved = localStorage.getItem('lastStationIndex');
            if (saved) playStation(saved);
        } else {
            if (audio.paused) {
                audio.play();
                playBtn.innerHTML = '⏸️';
            } else {
                audio.pause();
                playBtn.innerHTML = '▶️';
            }
        }
    }

    function prev() {
        if (current > 0) playStation(current - 1);
        else playStation(stations.length - 1); // wrap to end
    }

    function next() {
        if (current < stations.length - 1) playStation(current + 1);
        else playStation(0); // wrap to start
    }

    function openPlayer() {
        playerModal.style.display = 'block';
        isOpen = true;
    }

    function closePlayer() {
        playerModal.style.display = 'none';
        isOpen = false;
        if (current >= 0) {
            document.querySelectorAll('.card')[current].focus();
        }
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
        volText.innerText = `Volume: ${(audio.volume * 100).toFixed(0)}%`;
    }

    // D-pad and keyboard controls
    document.addEventListener('keydown', function(e) {
        const activeElement = document.activeElement;
        
        // Navigation in station grid
        if (activeElement.classList.contains('card')) {
            const cards = document.querySelectorAll('.card');
            const currentIndex = Array.from(cards).indexOf(activeElement);
            const cols = Math.floor(document.querySelector('.grid').offsetWidth / 150);
            
            switch(e.key) {
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
        
        // Player controls
        switch(e.key) {
            case 'ArrowUp': 
                volumeUp();
                e.preventDefault();
                break;
            case 'ArrowDown':
                volumeDown();
                e.preventDefault();
                break;
            case 'ArrowLeft': 
                prev();
                e.preventDefault();
                break;
            case 'ArrowRight': 
                next();
                e.preventDefault();
                break;
            case 'Enter':
            case ' ':
                if (activeElement.tagName === 'BUTTON') return;
                togglePlay();
                e.preventDefault();
                break;
            case 'Backspace':
                closePlayer();
                e.preventDefault();
                break;
            case 'Escape':
                closePlayer();
                e.preventDefault();
                break;
        }
    });

    // Initialize
    window.onload = function() {
        const savedIndex = parseInt(localStorage.getItem('lastStationIndex'));
        const savedVolume = parseFloat(localStorage.getItem('volume'));
        
        if (!isNaN(savedVolume)) {
            audio.volume = savedVolume;
        } else {
            audio.volume = 0.7; // default volume
        }
        
        if (!isNaN(savedIndex) && savedIndex >= 0 && savedIndex < stations.length) {
            playStation(savedIndex);
        }
        
        showVolume();
        
        // Update play/pause button when audio state changes
        audio.addEventListener('play', () => playBtn.innerHTML = '⏸️');
        audio.addEventListener('pause', () => playBtn.innerHTML = '▶️');
    }
</script>
</body>
</html>
""", station_names=station_names)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)