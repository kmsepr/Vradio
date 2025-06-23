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
    const stations = {{ station_names|tojson }};
    const displayNames = {{ display_names|tojson }};
    const stationInfo = {
        "air_calicut": "All India Radio - Calicut Station (684 AM)",
        "radio_nellikka": "Popular Malayalam Radio",
        "muthnabi_radio": "Traditional Malayalam Songs",
        "malayalam_1": "Contemporary Malayalam Music",
        "radio_digital_malayali": "Digital Malayali Community Radio",
        "malayalam_90s": "Classic 90s Malayalam Hits"
    };
    
    let current = -1;
    let isOpen = false;
    const audio = document.getElementById('modalAudio');
    const volText = document.getElementById('volText');
    const miniPlayer = document.getElementById("miniPlayer");
    const playerModal = document.getElementById("playerModal");
    const nowPlaying = document.getElementById("nowPlaying");
    const stationInfoEl = document.getElementById("stationInfo");
    const playBtn = document.getElementById("playBtn");
    const miniStatus = document.getElementById("miniStatus");

    function handleCardKey(event, id) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            playStation(stations.indexOf(id));
        }
    }

    function playStation(index) {
        current = parseInt(index);
        const id = stations[current];
        const name = displayNames[id];
        audio.src = '/' + id;
        audio.play().catch(e => console.log("Play error:", e));
        nowPlaying.innerText = name;
        stationInfoEl.innerText = stationInfo[id] || "";
        document.getElementById("miniTitle").innerText = name;
        miniPlayer.style.display = 'flex';
        miniStatus.textContent = "▶";
        openPlayer();
        localStorage.setItem('lastStationIndex', current);
        playBtn.focus();
        
        // Update media session for mobile/lock screen controls
        if ('mediaSession' in navigator) {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: name,
                artist: stationInfo[id] || "Malayalam Radio",
            });
        }
    }

    function togglePlay() {
        if (!audio.src) {
            const saved = localStorage.getItem('lastStationIndex');
            if (saved) playStation(saved);
        } else {
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
    }

    function prev() {
        if (current > 0) playStation(current - 1);
        else playStation(stations.length - 1);
        nowPlaying.style.animation = 'pulse 0.5s';
    }

    function next() {
        if (current < stations.length - 1) playStation(current + 1);
        else playStation(0);
        nowPlaying.style.animation = 'pulse 0.5s';
    }

    function openPlayer() {
        playerModal.style.display = 'block';
        isOpen = true;
        document.body.style.overflow = 'hidden';
    }

    function closePlayer() {
        playerModal.style.display = 'none';
        isOpen = false;
        document.body.style.overflow = 'auto';
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
        volText.style.transform = 'scale(1.2)';
        setTimeout(() => volText.style.transform = 'scale(1)', 200);
    }

    // D-pad and keyboard controls
    document.addEventListener('keydown', function(e) {
        const activeElement = document.activeElement;
        
        // Navigation in station grid
        if (activeElement.classList.contains('card')) {
            const cards = document.querySelectorAll('.card');
            const currentIndex = Array.from(cards).indexOf(activeElement);
            const cols = Math.floor(document.querySelector('.grid').offsetWidth / 200);
            
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
        
        // Player controls - Updated to match requested layout
        switch(e.key) {
            case 'ArrowLeft': 
                volumeDown();
                e.preventDefault();
                break;
            case 'ArrowRight':
                volumeUp();
                e.preventDefault();
                break;
            case 'ArrowDown':
                next();
                e.preventDefault();
                break;
            case 'ArrowUp': 
                prev();
                e.preventDefault();
                break;
            case 'Enter':
            case ' ':
            case 'MediaPlayPause':
                if (activeElement.tagName === 'BUTTON') return;
                togglePlay();
                e.preventDefault();
                break;
            case 'Backspace':
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
            audio.volume = 0.7;
        }
        
        if (!isNaN(savedIndex) && savedIndex >= 0 && savedIndex < stations.length) {
            playStation(savedIndex);
        }
        
        showVolume();
        
        // Update play/pause button when audio state changes
        audio.addEventListener('play', () => {
            playBtn.innerHTML = '⏸';
            miniStatus.textContent = "▶";
        });
        audio.addEventListener('pause', () => {
            playBtn.innerHTML = '▶';
            miniStatus.textContent = "⏸";
        });
        
        // Support for hardware media keys
        if ('mediaSession' in navigator) {
            navigator.mediaSession.setActionHandler('play', togglePlay);
            navigator.mediaSession.setActionHandler('pause', togglePlay);
            navigator.mediaSession.setActionHandler('previoustrack', prev);
            navigator.mediaSession.setActionHandler('nexttrack', next);
        }
    }
</script>
</body>
</html>
""", station_names=station_names, display_names=display_names)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)