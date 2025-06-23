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

DISPLAY_NAMES = {
    "air_calicut": "AIR Kozhikode",
    "radio_nellikka": "Radio Nellikka",
    "muthnabi_radio": "Muthnabi Radio",
    "malayalam_1": "Malayalam Radio 1",
    "radio_digital_malayali": "Digital Malayali",
    "malayalam_90s": "Malayalam 90s Hits"
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
  <title>Muthnabi Radio</title>
  <style>
    body {
      background: #111;
      color: white;
      font-family: Arial, sans-serif;
      margin: 0;
      -webkit-tap-highlight-color: transparent;
    }
    h1 {
      text-align: center;
      font-size: 1.5rem;
      background: linear-gradient(to right, #1a2a6c, #b21f1f, #fdbb2d);
      margin: 0;
      padding: 15px;
    }
    #playerModal {
      position: fixed;
      top: 0; left: 0;
      width: 100%; height: 100%;
      background: rgba(0,0,0,0.95);
      z-index: 999;
      text-align: center;
      padding: 20px;
      box-sizing: border-box;
    }
    .player-content {
      max-width: 500px;
      margin: 0 auto;
      padding-top: 30px;
    }
    audio {
      width: 100%;
      margin: 20px 0;
    }
    button {
      background: #4CAF50;
      border: none;
      color: white;
      padding: 15px;
      font-size: 1.6rem;
      margin: 10px;
      border-radius: 50%;
      cursor: pointer;
      box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    button:focus {
      outline: 2px solid yellow;
      box-shadow: 0 0 8px yellow;
    }
    #volText {
      margin: 10px 0;
      font-size: 1.2rem;
    }
    .label {
      font-size: 1.5rem;
      margin-bottom: 10px;
      color: #4CAF50;
    }
  </style>
</head>
<body>
  <h1>📻 Malayalam Radio</h1>
  <div id="playerModal">
    <div class="player-content">
      <div class="label" id="nowPlaying">Now Playing: Muthnabi Radio</div>
      <audio id="modalAudio" controls></audio>
      <div>
        <button onclick="prev()" tabindex="0">⏮</button>
        <button onclick="togglePlay()" id="playBtn" tabindex="0">⏯</button>
        <button onclick="next()" tabindex="0">⏭</button>
      </div>
      <div>
        <button onclick="volumeDown()" tabindex="0">−</button>
        <button onclick="volumeUp()" tabindex="0">+</button>
        <div id="volText">Volume: 70%</div>
      </div>
      <div style="margin-top:20px; font-size:0.9rem; color:#aaa;">
        Keys: 2↑ 8↓ 4← 6→ 5⏯
      </div>
    </div>
  </div>

<script>
const stations = {{ station_names|tojson }};
const displayNames = {{ display_names|tojson }};
let current = stations.indexOf('muthnabi_radio');
const audio = document.getElementById("modalAudio");
const volText = document.getElementById("volText");
const playBtn = document.getElementById("playBtn");
const nowPlaying = document.getElementById("nowPlaying");

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
    } else {
        audio.pause();
        playBtn.innerHTML = '▶';
    }
}
function prev() {
    current = (current > 0) ? current - 1 : stations.length - 1;
    playStation(current);
}
function next() {
    current = (current < stations.length - 1) ? current + 1 : 0;
    playStation(current);
}
function playStation(index) {
    current = index;
    const id = stations[current];
    const name = displayNames[id] || id;
    audio.src = '/' + id;
    audio.play();
    playBtn.innerHTML = '⏸';
    nowPlaying.innerText = "Now Playing: " + name;
}

document.addEventListener('keydown', function(e) {
    const code = e.keyCode || e.which;

    switch (code) {
        case 50: volumeUp(); e.preventDefault(); break;       // 2
        case 56: volumeDown(); e.preventDefault(); break;     // 8
        case 52: prev(); e.preventDefault(); break;           // 4
        case 54: next(); e.preventDefault(); break;           // 6
        case 53: togglePlay(); e.preventDefault(); break;     // 5
        case 13:
            if (document.activeElement && document.activeElement.tagName === 'BUTTON') {
                document.activeElement.click();
            }
            break;
    }
});

window.onload = function() {
    const savedVolume = localStorage.getItem('volume');
    if (savedVolume) {
        audio.volume = parseFloat(savedVolume);
        volText.innerText = `Volume: ${(audio.volume * 100).toFixed(0)}%`;
    }
    playStation(current);
};
</script>
</body>
</html>
""", station_names=station_names, display_names=DISPLAY_NAMES)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)