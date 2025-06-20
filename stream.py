import subprocess
import time
from flask import Flask, Response

app = Flask(__name__)

# 🌟 Sidebar Bookmarks (Main)
BOOKMARKS = [
    {"name": "🎥 YouTube", "url": "http://capitalist-anthe-pscj-4a28f285.koyeb.app/"},
    {"name": "📚 Others", "url": "/bookmarks"},
]

# 📚 Additional Bookmarks (accessible via /bookmarks)
OTHER_BOOKMARKS = [
    {"name": "📻 Radio Keralam", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/radio_keralam"},
    {"name": "📻 Radio Nellikka", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/radio_nellikka"},
    {"name": "📺 Bloomberg TV", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/bloomberg_tv"},
    {"name": "📺 Mazhavil Manorama", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/mazhavil_manorama"},
    {"name": "📺 Kairali WE", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/kairali_we"},
    {"name": "📺 Safari TV", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/safari_tv"},
    {"name": "📺 Victers TV", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/victers_tv"},
    {"name": "📻 Al Jazeera", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/al_jazeera"},
    {"name": "📻 Asianet News", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/asianet_news"},
    {"name": "📻 AIR Kavarati", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/air_kavarati"},
    {"name": "📻 AIR Calicut", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/air_calicut"},
    {"name": "📻 Manjeri FM", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/manjeri_fm"},
    {"name": "📻 Real FM", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/real_fm"},
    {"name": "📻 Quran Radio Nablus", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/quran_radio_nablus"},
    {"name": "📻 Al Nour", "url": "http://surviving-audy-sadiqkm-fb03800f.koyeb.app/al_nour"},
]

# 🛁 Stream Proxy
RADIO_STATIONS = {
    "radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",
    "asianet_news": "https://vidcdn.vidgyor.com/asianet-origin/audioonly/chunks.m3u8",
    "air_kavarati": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio189/chunklist.m3u8",
    "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
    "manjeri_fm": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio101/chunklist.m3u8",
    "real_fm": "http://air.pc.cdn.bitgravity.com/air/live/pbaudio083/playlist.m3u8",
    "quran_radio_nablus": "http://www.quran-radio.org:8002/",
    "al_nour": "http://audiostreaming.itworkscdn.com:9066/",
    "radio_keralam": "http://ice31.securenetsystems.net/RADIOKERAL",
    "bloomberg_tv": "https://bloomberg-bloomberg-3-br.samsung.wurl.tv/manifest/playlist.m3u8",
    "mazhavil_manorama": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/mazhavilmanorama_nim_https/050522/mazhavilmanorama/playlist.m3u8",
    "kairali_we": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/wetv_nim_https/050522/wetv/playlist.m3u8",
    "safari_tv": "https://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/chunks.m3u8",
    "victers_tv": "https://932y4x26ljv8-hls-live.5centscdn.com/victers/tv.stream/victers/tv1/chunks.m3u8",
    "al_jazeera": "http://live-hls-audio-web-aja.getaj.net/VOICE-AJA/index.m3u8",
}

# 🔁 FFmpeg proxy generator
def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()
        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1", "-reconnect_delay_max", "10",
                "-fflags", "nobuffer", "-flags", "low_delay",
                "-i", url, "-vn", "-ac", "1", "-b:a", "40k", "-buffer_size", "1024k",
                "-f", "mp3", "-"
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
    def pastel_color(i):
        r = (100 + (i * 40)) % 256
        g = (150 + (i * 60)) % 256
        b = (200 + (i * 80)) % 256
        return f"{r}, {g}, {b}"

    bookmarks_html = "".join(
        f"<a href='{b['url']}' style='color:white;text-decoration:none;border-bottom:1px solid #333;padding:8px 0;display:block;'>{b['name']}</a>"
        for b in BOOKMARKS
    )
    links_html = "".join(
        f"<div class='card' style='background-color: rgba({pastel_color(i)}, 0.85);'><a href='/{name}' target='_blank'>{name}</a></div>"
        for i, name in enumerate(RADIO_STATIONS)
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name='viewport' content='width=device-width, initial-scale=1' />
        <title>Radio</title>
        <style>
            body {{ background: #111; color: white; font-family: sans-serif; margin: 0; }}
            .menu-icon {{ position: absolute; top: 10px; left: 10px; font-size: 1.5rem; cursor: pointer; }}
            .sidebar {{ position: fixed; left: -250px; top: 0; width: 220px; height: 100%; background: #222; padding: 15px; overflow-y: auto; transition: left 0.3s; }}
            .sidebar.open {{ left: 0; }}
            h1 {{ font-size: 1.2rem; text-align: center; padding: 10px; background: #222; margin: 0; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 10px; padding: 10px; margin-top: 50px; }}
            .card {{ padding: 10px; border-radius: 8px; text-align: center; background: #333; }}
            .card a {{ color: white; text-decoration: none; font-size: 0.95rem; }}
        </style>
        <script>
            function toggleSidebar() {{ document.getElementById('sidebar').classList.toggle('open'); }}
            document.addEventListener('keydown', function(e) {{ if (e.key === '1') toggleSidebar(); }});
        </script>
    </head>
    <body>
        <div class='menu-icon' onclick='toggleSidebar()'>☰</div>
        <div class='sidebar' id='sidebar'>{bookmarks_html}</div>
        <h1>📻 Radio Stations</h1>
        <div class='grid'>{links_html}</div>
    </body>
    </html>
    """

@app.route("/bookmarks")
def show_bookmarks():
    other_links = "".join(
        f"<li><a href='{b['url']}' target='_blank' style='color:white;text-decoration:none;'>{b['name']}</a></li>"
        for b in OTHER_BOOKMARKS
    )
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>📚 Other Bookmarks</title>
        <meta name='viewport' content='width=device-width, initial-scale=1' />
        <style>
            body {{ background: #111; color: white; font-family: sans-serif; padding: 20px; }}
            a {{ display: block; margin: 8px 0; }}
        </style>
    </head>
    <body>
        <h2>📚 Other Bookmarks</h2>
        <ul>{other_links}</ul>
        <a href="/" style="color:#ccc;">⬅️ Back to Home</a>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)