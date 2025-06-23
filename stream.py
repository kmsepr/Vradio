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
    while True:
        process = subprocess.Popen([
            "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
            "-reconnect_delay_max", "10", "-fflags", "nobuffer",
            "-flags", "low_delay", "-i", url, "-vn", "-ac", "1",
            "-b:a", "40k", "-buffer_size", "1024k", "-f", "mp3", "-"
        ], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            process.kill()
            break
        except Exception:
            process.kill()
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
    body {
        background: #111; color: white; font-family: sans-serif; margin: 0;
    }
    h1 {
        text-align: center; padding: 1rem; font-size: 1.5rem;
        background: linear-gradient(to right, #1a2a6c, #b21f1f, #fdbb2d);
    }
    .grid {
        display: grid; gap: 1rem; padding: 1rem;
        grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    }
    .card {
        background: #333; border-radius: 8px; padding: 1rem;
        text-align: center; cursor: pointer; transition: 0.2s;
    }
    .card:hover, .card:focus {
        background: #555;
        outline: none;
    }
    audio {
        width: 100%; margin: 1rem 0;
    }
    .controls {
        display: flex; justify-content: center; gap: 1rem; flex-wrap: wrap;
    }
    .controls button {
        padding: 1rem; font-size: 1.5rem; border: none;
        border-radius: 50%; background: #4caf50; color: white;
    }
    .label, #volText {
        text-align: center; margin: 0.5rem 0;
    }
  </style>
</head>
<body>
  <h1>📻 Malayalam Radio Stations</h1>
  <div class="grid">
    {% for id, name in display_names.items() %}
    <div class="card" tabindex="0" onclick="playStation('{{ loop.index0 }}')">
      {{ name }}
    </div>
    {% endfor %}
  </div>

  <div class="label" id="nowPlaying">Now Playing: Loading…</div>
  <audio id="modalAudio" controls autoplay></audio>

  <div class="controls">
    <button onclick="prev()">⏮</button>
    <button onclick="togglePlay()" id="playBtn">⏯</button>
    <button onclick="next()">⏭</button>
  </div>

  <div class="controls">
    <button onclick="volumeDown()">−</button>
    <button onclick="volumeUp()">+</button>
  </div>
  <div id="volText">Volume: 70%</div>
 <div style="text-align:center; font-size: 0.9rem; color: #aaa; margin-top: 1rem;">
  HMD D-Pad: 4⏮ | 5⏯ | 6⏭ | ↑↓ Scroll
</div>

<script>
const stations = {{ station_names|tojson }};
const displayNames = {{ display_names|tojson }};
let current = stations.indexOf("muthnabi_radio");
const audio = document.getElementById("modalAudio");
const nowPlaying = document.getElementById("nowPlaying");
const playBtn = document.getElementById("playBtn");
const volText = document.getElementById("volText");

function togglePlay() {
    if (audio.paused) {
        audio.play();
        playBtn.innerHTML = "⏸";
    } else {
        audio.pause();
        playBtn.innerHTML = "▶";
    }
}
function prev() {
    current = (current > 0) ? current - 1 : stations.length - 1;
    playStation(current);
}
function next() {
    current = (current + 1) % stations.length;
    playStation(current);
}
function playStation(index) {
    current = index;
    const id = stations[current];
    const name = displayNames[id] || id;
    audio.src = "/" + id;
    nowPlaying.innerText = "Now Playing: " + name;
    playBtn.innerHTML = "⏸";

    // Highlight current card (optional)
    const cards = document.querySelectorAll(".card");
    cards.forEach((el, i) => {
        el.style.background = (i === current) ? "#4caf50" : "#333";
    });
}

document.addEventListener("keydown", function(e) {
    const key = e.key;
    const active = document.activeElement;
    const cards = document.querySelectorAll(".card");
    const index = Array.from(cards).indexOf(active);
    const cols = Math.floor(document.querySelector(".grid").offsetWidth / 160);

    switch (key) {
        case "4":
        case "ArrowLeft":
            prev();
            break;
        case "6":
        case "ArrowRight":
            next();
            break;
        case "5":
        case "Enter":
            togglePlay();
            break;
        case "ArrowUp":
            if (index >= cols) cards[index - cols].focus();
            break;
        case "ArrowDown":
            if (index < cards.length - cols) cards[index + cols].focus();
            break;
    }

    if (["4", "5", "6", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight", "Enter"].includes(key)) {
        e.preventDefault();
    }
});

window.onload = function () {
    audio.volume = 0.7;
    volText.innerText = "Volume: 70%";
    playStation(current);

    // Auto-focus first card on load
    const firstCard = document.querySelector(".card");
    if (firstCard) firstCard.focus();
};
</script>
</body>
</html>
""", station_names=station_names, display_names=display_names)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)