from flask import Flask, Response, render_template_string
import subprocess
import time

app = Flask(__name__)

RADIO_STATIONS = {
    
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL",
    "malayalam_1": "http://167.114.131.90:5412/stream",
    "radio_digital_malayali": "https://radio.digitalmalayali.in/listen/stream/radio.mp3",
    "malayalam_90s": "https://stream-159.zeno.fm/gm3g9amzm0hvv?zs-x-7jq8ksTOav9ZhlYHi9xw",
    "aural_oldies": "https://stream-162.zeno.fm/tksfwb1mgzzuv?zs=SxeQj1-7R0alsZSWJie5eQ",
    "radio_malayalam": "https://radiomalayalamfm.com/radio/8000/radio.mp3",
    "swaranjali": "https://stream-161.zeno.fm/x7mve2vt01zuv?zs-D4nK05-7SSK2FZAsvumh2w",
    "radio_beat_malayalam": "http://live.exertion.in:8050/radio.mp3",
    "shahul_radio": "https://stream-150.zeno.fm/cynbm5ngx38uv?zs=Ktca5StNRWm-sdIR7GloVg",
    "raja_radio": "http://159.203.111.241:8026/stream",
    "nonstop_hindi": "http://s5.voscast.com:8216/stream",
    "fm_gold": "https://airhlspush.pc.cdn.bitgravity.com/httppush/hispbaudio005/hispbaudio00564kbps.m3u8",
    "motivational_series": "http://104.7.66.64:8010",
    "deenagers_radio": "http://104.7.66.64:8003/",
    "hajj_channel": "http://104.7.66.64:8005",
    "abc_islam": "http://s10.voscast.com:9276/stream",
    "eram_fm": "http://icecast2.edisimo.com:8000/eramfm.mp3",
    "al_sumood_fm": "http://us3.internet-radio.com/proxy/alsumoodfm2020?mp=/stream",
    "nur_ala_nur": "http://104.7.66.64:8011/",
    "ruqya_radio": "http://104.7.66.64:8004",
    "seiyun_radio": "http://s2.radio.co/s26c62011e/listen",
    "noor_al_eman": "http://edge.mixlr.com/channel/boaht",
    "sam_yemen": "https://edge.mixlr.com/channel/kijwr",
    "afaq": "https://edge.mixlr.com/channel/rumps",
    "alfasi_radio": "https://qurango.net/radio/mishary_alafasi",
    "tafsir_quran": "https://radio.quranradiotafsir.com/9992/stream",
    "sirat_al_mustaqim": "http://104.7.66.64:8091/stream",
    "river_nile_radio": "http://104.7.66.64:8087",
    "quran_radio_cairo": "http://n02.radiojar.com/8s5u5tpdtwzuv",
    "quran_radio_nablus": "http://www.quran-radio.org:8002/",
    "al_nour": "http://audiostreaming.itworkscdn.com:9066/",
    "allahu_akbar_radio": "http://66.45.232.132:9996/stream",
    "omar_abdul_kafi_radio": "http://104.7.66.64:8007",
    "urdu_islamic_lecture": "http://144.91.121.54:27001/channel_02.aac",
    "hob_nabi": "http://216.245.210.78:8098/stream",
    "sanaa_radio": "http://dc5.serverse.com/proxy/pbmhbvxs/stream",
    "rubat_ataq": "http://stream.zeno.fm/5tpfc8d7xqruv",
    "al_jazeera": "http://live-hls-audio-web-aja.getaj.net/VOICE-AJA/index.m3u8",
    "asianet_news": "https://vidcdn.vidgyor.com/asianet-origin/audioonly/chunks.m3u8",
    "air_kavarati": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio189/chunklist.m3u8",
    "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
    "manjeri_fm": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio101/chunklist.m3u8",
    "real_fm": "http://air.pc.cdn.bitgravity.com/air/live/pbaudio083/playlist.m3u8",
    "vom_news": "https://psmnews.mv/stream/radio-dhivehi-raajjeyge-adu",
    "safari_tv": "https://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/chunks.m3u8",
    "victers_tv": "https://932y4x26ljv8-hls-live.5centscdn.com/victers/tv.stream/victers/tv1/chunks.m3u8",
    "kairali_we": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/wetv_nim_https/050522/wetv/playlist.m3u8",
    "flowers_tv": "http://103.199.161.254/Content/flowers/Live/Channel(Flowers)/index.m3u8",
    "dd_malayalam": "https://d3eyhgoylams0m.cloudfront.net/v1/manifest/93ce20f0f52760bf38be911ff4c91ed02aa2fd92/ed7bd2c7-8d10-4051-b397-2f6b90f99acb/562ee8f9-9950-48a0-ba1d-effa00cf0478/2.m3u8",
    "amrita_tv": "https://dr1zhpsuem5f4.cloudfront.net/master.m3u8",
    "24_news": "https://segment.yuppcdn.net/110322/channel24/playlist.m3u8",
    "mazhavil_manorama": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/mazhavilmanorama_nim_https/050522/mazhavilmanorama/playlist.m3u8",
    "manorama_news": "http://103.199.161.254/Content/manoramanews/Live/Channel(ManoramaNews)/index.m3u8",
    "aaj_tak": "https://feeds.intoday.in/aajtak/api/aajtakhd/master.m3u8",
    "bloomberg_tv": "https://bloomberg-bloomberg-3-br.samsung.wurl.tv/manifest/playlist.m3u8",
    "france_24": "https://live.france24.com/hls/live/2037218/F24_EN_HI_HLS/master_500.m3u8",
    "n1_news": "https://best-str.umn.cdn.united.cloud/stream?stream=sp1400&sp=n1info&channel=n1bos&u=n1info&p=n1Sh4redSecre7iNf0&player=m3u8",
    "vom_radio": "https://radio.psm.mv/draair",
"radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",

 
    "radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",
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
            position: fixed; bottom: 0; left: 0; width: 100%;
            background: #222; color: white; padding: 8px;
            text-align: center; display: none; z-index: 1000;
        }
        #playerModal {
            display: none; position: fixed; top: 0; left: 0;
            width: 100%; height: 100%; background: #000;
            z-index: 999; text-align: center;
            padding: 15px; box-sizing: border-box;
        }
        .close-btn {
            position: absolute; top: 10px; right: 15px;
            font-size: 1.2rem; cursor: pointer;
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

    <div id="miniPlayer" onclick="openPlayer()">
        🎶 <span id="miniTitle">Now Playing</span> ⬆️
    </div>

    <div id="playerModal">
        <div class="close-btn" onclick="closePlayer()">❌</div>
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
        const audio = document.getElementById('modalAudio');
        const volText = document.getElementById('volText');

        function playStation(index) {
            current = parseInt(index);
            const name = stations[current];
            audio.src = '/' + name;
            audio.play();
            document.getElementById("playerTitle").innerText = '🎶 Playing: ' + name;
            document.getElementById("miniTitle").innerText = name;
            document.getElementById("miniPlayer").style.display = 'block';
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
            document.getElementById("playerModal").style.display = 'block';
        }

        function closePlayer() {
            document.getElementById("playerModal").style.display = 'none';
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