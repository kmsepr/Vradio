import subprocess
import time
from flask import Flask, Response, redirect, request
import json
from pathlib import Path

app = Flask(__name__)
STATIONS_FILE = "radio_stations.json"

DEFAULT_STATIONS = {
    "News": {
        "al_jazeera": {
            "name": "Al Jazeera",
            "url": "http://live-hls-audio-web-aja.getaj.net/VOICE-AJA/index.m3u8"
        },
        "asianet_news": {
            "name": "Asianet News",
            "url": "https://vidcdn.vidgyor.com/asianet-origin/audioonly/chunks.m3u8"
        },
        "vom_news": {
            "name": "VOM News",
            "url": "https://psmnews.mv/stream/radio-dhivehi-raajjeyge-adu"
        },
        "aaj_tak": {
            "name": "Aaj Tak",
            "url": "https://feeds.intoday.in/aajtak/api/aajtakhd/master.m3u8"
        },
        "bloomberg_tv": {
            "name": "Bloomberg TV",
            "url": "https://bloomberg-bloomberg-3-br.samsung.wurl.tv/manifest/playlist.m3u8"
        },
        "france_24": {
            "name": "France 24",
            "url": "https://live.france24.com/hls/live/2037218/F24_EN_HI_HLS/master_500.m3u8"
        },
        "n1_news": {
            "name": "N1 News",
            "url": "https://best-str.umn.cdn.united.cloud/stream?stream=sp1400&sp=n1info&channel=n1bos&u=n1info&p=n1Sh4redSecre7iNf0&player=m3u8"
        }
    },
    "Islamic": {
        "muthnabi_radio": {
            "name": "Muthnabi Radio",
            "url": "http://cast4.my-control-panel.com/proxy/muthnabi/stream"
        },
        "deenagers_radio": {
            "name": "Deenagers Radio",
            "url": "http://104.7.66.64:8003/"
        },
        "hajj_channel": {
            "name": "Hajj Channel",
            "url": "http://104.7.66.64:8005"
        },
        "abc_islam": {
            "name": "ABC Islam",
            "url": "http://s10.voscast.com:9276/stream"
        },
        "eram_fm": {
            "name": "Eram FM",
            "url": "http://icecast2.edisimo.com:8000/eramfm.mp3"
        },
        "al_sumood_fm": {
            "name": "Al Sumood FM",
            "url": "http://us3.internet-radio.com/proxy/alsumoodfm2020?mp=/stream"
        },
        "nur_ala_nur": {
            "name": "Nur Ala Nur",
            "url": "http://104.7.66.64:8011/"
        },
        "ruqya_radio": {
            "name": "Ruqya Radio",
            "url": "http://104.7.66.64:8004"
        },
        "sirat_al_mustaqim": {
            "name": "Sirat Al Mustaqim",
            "url": "http://104.7.66.64:8091/stream"
        },
        "quran_radio_cairo": {
            "name": "Quran Radio Cairo",
            "url": "http://n02.radiojar.com/8s5u5tpdtwzuv"
        },
        "quran_radio_nablus": {
            "name": "Quran Radio Nablus",
            "url": "http://www.quran-radio.org:8002/"
        },
        "al_nour": {
            "name": "Al Nour",
            "url": "http://audiostreaming.itworkscdn.com:9066/"
        },
        "allahu_akbar_radio": {
            "name": "Allahu Akbar Radio",
            "url": "http://66.45.232.132:9996/stream"
        },
        "omar_abdul_kafi_radio": {
            "name": "Omar Abdul Kafi Radio",
            "url": "http://104.7.66.64:8007"
        },
        "urdu_islamic_lecture": {
            "name": "Urdu Islamic Lecture",
            "url": "http://144.91.121.54:27001/channel_02.aac"
        },
        "hob_nabi": {
            "name": "Hub Nabi",
            "url": "http://216.245.210.78:8098/stream"
        },
        "tafsir_quran": {
            "name": "Tafsir Quran",
            "url": "https://radio.quranradiotafsir.com/9992/stream"
        },
        "alfasi_radio": {
            "name": "Alfasi Radio",
            "url": "https://qurango.net/radio/mishary_alafasi"
        }
    },
    "Malayalam": {
        "radio_nellikka": {
            "name": "Radio Nellikka",
            "url": "https://usa20.fastcast4u.com:2130/stream"
        },
        "radio_keralam": {
            "name": "Radio Keralam",
            "url": "http://ice31.securenetsystems.net/RADIOKERAL"
        },
        "malayalam_1": {
            "name": "Malayalam 1",
            "url": "http://167.114.131.90:5412/stream"
        },
        "radio_digital_malayali": {
            "name": "Digital Malayali",
            "url": "https://radio.digitalmalayali.in/listen/stream/radio.mp3"
        },
        "malayalam_90s": {
            "name": "Malayalam 90s",
            "url": "https://stream-159.zeno.fm/gm3g9amzm0hvv?zs-x-7jq8ksTOav9ZhlYHi9xw"
        },
        "aural_oldies": {
            "name": "Aural Oldies",
            "url": "https://stream-162.zeno.fm/tksfwb1mgzzuv?zs=SxeQj1-7R0alsZSWJie5eQ"
        },
        "radio_malayalam": {
            "name": "Radio Malayalam",
            "url": "https://radiomalayalamfm.com/radio/8000/radio.mp3"
        },
        "swaranjali": {
            "name": "Swaranjali",
            "url": "https://stream-161.zeno.fm/x7mve2vt01zuv?zs-D4nK05-7SSK2FZAsvumh2w"
        },
        "radio_beat_malayalam": {
            "name": "Radio Beat Malayalam",
            "url": "http://live.exertion.in:8050/radio.mp3"
        },
        "shahul_radio": {
            "name": "Shahul Radio",
            "url": "https://stream-150.zeno.fm/cynbm5ngx38uv?zs=Ktca5StNRWm-sdIR7GloVg"
        },
        "raja_radio": {
            "name": "Raja Radio",
            "url": "http://159.203.111.241:8026/stream"
        }
    },
    "Others": {
        "nonstop_hindi": {
            "name": "Nonstop Hindi",
            "url": "http://s5.voscast.com:8216/stream"
        },
        "motivational_series": {
            "name": "Motivational Series",
            "url": "http://104.7.66.64:8010"
        },
        "seiyun_radio": {
            "name": "Seiyun Radio",
            "url": "http://s2.radio.co/s26c62011e/listen"
        },
        "noor_al_eman": {
            "name": "Noor Al Eman",
            "url": "http://edge.mixlr.com/channel/boaht"
        },
        "sam_yemen": {
            "name": "SAM Yemen",
            "url": "https://edge.mixlr.com/channel/kijwr"
        },
        "afaq": {
            "name": "Afaq",
            "url": "https://edge.mixlr.com/channel/rumps"
        },
        "sanaa_radio": {
            "name": "Sanaa Radio",
            "url": "http://dc5.serverse.com/proxy/pbmhbvxs/stream"
        },
        "rubat_ataq": {
            "name": "Rubat Ataq",
            "url": "http://stream.zeno.fm/5tpfc8d7xqruv"
        }
    },
    "TV": {
        "safari_tv": {
            "name": "Safari TV",
            "url": "https://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/chunks.m3u8"
        },
        "victers_tv": {
            "name": "Victers TV",
            "url": "https://932y4x26ljv8-hls-live.5centscdn.com/victers/tv.stream/victers/tv1/chunks.m3u8"
        },
        "kairali_we": {
            "name": "Kairali WE",
            "url": "https://yuppmedtaorire.akamaized.net/.../wetv/playlist.m3u8"
        },
        "flowers_tv": {
            "name": "Flowers TV",
            "url": "http://103.199.161.254/Content/flowers/Live/Channel(Flowers)/index.m3u8"
        },
        "dd_malayalam": {
            "name": "DD Malayalam",
            "url": "https://d3eyhgoylams0m.cloudfront.net/.../2.m3u8"
        },
        "amrita_tv": {
            "name": "Amrita TV",
            "url": "https://dr1zhpsuem5f4.cloudfront.net/master.m3u8"
        },
        "24_news": {
            "name": "24 News",
            "url": "https://segment.yuppcdn.net/110322/channel24/playlist.m3u8"
        },
        "mazhavil_manorama": {
            "name": "Mazhavil Manorama",
            "url": "https://yuppmedtaorire.akamaized.net/.../mazhavilmanorama/playlist.m3u8"
        },
        "manorama_news": {
            "name": "Manorama News",
            "url": "http://103.199.161.254/Content/manoramanews/Live/Channel(ManoramaNews)/index.m3u8"
        }
    },
    "YouTube": {
        "shajahan_rahmani": {
            "name": "Shajahan Rahmani",
            "url": "http://capitalist-anthe-pscj-4a28f285.koyeb.app/shajahan_rahmani"
        },
        "media_one": {
            "name": "Mediaone",
            "url": "http://capitalist-anthe-pscj-4a28f285.koyeb.app/media_one"
        }
    }
}



def load_data(filename, default_data):
    try:
        if Path(filename).exists():
            with open(filename, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
    return default_data

def save_data(filename, data):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {filename}: {e}")

RADIO_STATIONS = load_data(STATIONS_FILE, DEFAULT_STATIONS)

FLAT_STATION_MAP = {
    sid: station["url"]
    for category in RADIO_STATIONS.values()
    for sid, station in category.items()
    if not station["url"].startswith("http://capitalist-anthe")
}

def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()
        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10", "-fflags", "nobuffer", "-flags", "low_delay",
                "-i", url, "-vn", "-ac", "1", "-b:a", "64k", "-f", "mp3", "-"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
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

@app.route("/<station_id>")
def direct_stream(station_id):
    if station_id in FLAT_STATION_MAP:
        return Response(generate_stream(FLAT_STATION_MAP[station_id]), mimetype="audio/mpeg")
    return "Station not found", 404

@app.route("/delete/<category>/<station_id>", methods=["POST"])
def delete_station(category, station_id):
    if category in RADIO_STATIONS and station_id in RADIO_STATIONS[category]:
        del RADIO_STATIONS[category][station_id]
        if not RADIO_STATIONS[category]:
            del RADIO_STATIONS[category]
        save_data(STATIONS_FILE, RADIO_STATIONS)
    return redirect("/")

@app.route("/")
def index():
    html_stations = ""
    for category, stations in RADIO_STATIONS.items():
        for sid, station in stations.items():
            display_name = station.get("name", sid.replace("_", " ").title())
            url = station.get("url", "")
            is_direct = url.startswith("http://capitalist-anthe") or sid.startswith("http")
            play_link = url if is_direct else f"/{sid}"
            html_stations += f"""
            <div class='station-card' data-category="{category}">
                <div class='station-header'>
                    <span class='station-name' onclick="playStream('{play_link}', '{display_name}')">{display_name}</span>
                    <form method='POST' action='/delete/{category}/{sid}' style='display:inline;'>
                        <button type='submit'>🗑️</button>
                    </form>
                </div>
            </div>
            """

    html_categories = "".join(
        f"""
        <div class='category-card' onclick="showStations('{cat}')">
            <h3>{cat}</h3>
            <p>{len(stations)} stations</p>
        </div>
        """ for cat, stations in RADIO_STATIONS.items()
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Radio</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ background:#111; color:#fff; font-family:sans-serif; padding:20px; }}
            .categories {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; }}
            .category-card, .station-card {{ background:#222; border-radius:8px; padding:10px; margin-bottom:10px; cursor:pointer; }}
            .station-header {{ display:flex; justify-content:space-between; align-items:center; }}
            .station-name {{ color:#4CAF50; font-weight:bold; cursor:pointer; }}
            button {{ background:none; border:1px solid #555; color:white; padding:4px 8px; border-radius:4px; cursor:pointer; }}
            .back-button {{ color:#4CAF50; margin-bottom:10px; cursor:pointer; }}
            #player {{ margin:10px 0; display:none; }}
        </style>
    </head>
    <body>
        <h1>📻 Radio Stations</h1>
        <div id="categories" class="categories">{html_categories}</div>

        <div id="stations-container" style="display:none;">
            <div class="back-button" onclick="showCategories()">← Back</div>
            <div id="stations">{html_stations}</div>
        </div>

        <div id="player">
            <p id="now-playing"></p>
            <audio id="audio-player" controls style="width:100%;"></audio>
        </div>

        <script>
            function showStations(category) {{
                document.getElementById('categories').style.display = 'none';
                document.getElementById('stations-container').style.display = 'block';
                const cards = document.querySelectorAll('.station-card');
                cards.forEach(card => {{
                    card.style.display = card.dataset.category === category ? 'block' : 'none';
                }});
            }}
            function showCategories() {{
                document.getElementById('categories').style.display = 'grid';
                document.getElementById('stations-container').style.display = 'none';
                document.getElementById('player').style.display = 'none';
            }}
            function playStream(url, name) {{
                const audio = document.getElementById('audio-player');
                const player = document.getElementById('player');
                const nowPlaying = document.getElementById('now-playing');
                audio.src = url;
                audio.play();
                nowPlaying.innerText = "🎶 Now Playing: " + name;
                player.style.display = 'block';
            }}
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    if not Path(STATIONS_FILE).exists():
        save_data(STATIONS_FILE, DEFAULT_STATIONS)
    app.run(host="0.0.0.0", port=8000, threaded=True)