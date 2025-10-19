import subprocess
import time
import math
from flask import Flask, Response, request, render_template_string

# --- Configuration and Setup ---

app = Flask(__name__)

# 📡 
RADIO_STATIONS = {
    "quran_radio_nablus": "http://www.quran-radio.org:8002/",
    "oman_radio": "https://partwota.cdn.mgmlcdn.com/omanrdoorg/omanrdo.stream_aac/chunklist.m3u8",
    "al_nour": "http://audiostreaming.itworkscdn.com:9066/",
    "allahu_akbar_radio": "http://66.45.232.132:9996/stream",
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
    "muthnabi_radio": "http://cast4.my-control-panel.com/proxy/muthnabi/stream",
    "radio_nellikka": "https://usa20.fastcast4u.com:2130/stream",
    "air_kavarati": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio189/chunklist.m3u8",
    "air_calicut": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio082/chunklist.m3u8",
    "manjeri_fm": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio101/chunklist.m3u8",
    "real_fm": "http://air.pc.cdn.bitgravity.com/air/live/pbaudio083/playlist.m3u8",
    "safari_tv": "https://j78dp346yq5r-hls-live.5centscdn.com/safari/live.stream/chunks.m3u8",
    "victers_tv": "https://932y4x26ljv8-hls-live.5centscdn.com/victers/tv.stream/victers/tv1/chunks.m3u8",
    "kairali_we": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/wetv_nim_https/050522/wetv/playlist.m3u8",
    "mazhavil_manorama": "https://yuppmedtaorire.akamaized.net/v1/master/a0d007312bfd99c47f76b77ae26b1ccdaae76cb1/mazhavilmanorama_nim_https/050522/mazhavilmanorama/playlist.m3u8",
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
    "river_nile_radio": "http://104.7.66.64:8087",
    "quran_radio_cairo": "http://n02.radiojar.com/8s5u5tpdtwzuv",
    "omar_abdul_kafi_radio": "http://104.7.66.64:8007",
    "urdu_islamic_lecture": "http://144.91.121.54:27001/channel_02.aac",
    "hob_nabi": "http://216.245.210.78:8098/stream",
    "sanaa_radio": "http://dc5.serverse.com/proxy/pbmhbvxs/stream",
    "rubat_ataq": "http://stream.zeno.fm/5tpfc8d7xqruv",
    "al_jazeera": "http://live-hls-audio-web-aja.getaj.net/VOICE-AJA/index.m3u8",
    "bloomberg_tv": "https://bloomberg-bloomberg-3-br.samsung.wurl.tv/manifest/playlist.m3u8",
    "france_24": "https://live.france24.com/hls/live/2037218/F24_EN_HI_HLS/master_500.m3u8",
    "vom_radio": "https://radio.psm.mv/draair",
}
# Convert station keys to a list for indexed access
STATION_NAMES = list(RADIO_STATIONS.keys())
STATIONS_PER_PAGE = 5

# --- Home Page with Pagination and Keypad Logic ---
@app.route("/")
def home():
    total_stations = len(STATION_NAMES)
    total_pages = math.ceil(total_stations / STATIONS_PER_PAGE)
    
    # 1. Get current page from query parameter, default to 1
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    
    # 2. Keypad Command Processing
    key = request.args.get('key')
    
    if key:
        current_page_index = page - 1 # 0-indexed page number
        
        try:
            # 1-based index of the station on the *current* page
            station_index_on_page = int(key) 
            
            # Keypad 1-5 maps to a station on the current page
            if 1 <= station_index_on_page <= STATIONS_PER_PAGE:
                
                # Global 0-indexed index of the selected station
                global_station_index = current_page_index * STATIONS_PER_PAGE + (station_index_on_page - 1)
                
                if 0 <= global_station_index < total_stations:
                    selected_station = STATION_NAMES[global_station_index]
                    # Redirect to the stream route for direct playback
                    return f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <title>Playing {selected_station.replace('_', ' ').title()}</title>
                        <meta http-equiv="refresh" content="0; url=/{selected_station}">
                    </head>
                    <body>
                        <p>Starting stream for <strong>{selected_station.replace('_', ' ').title()}</strong>... <a href="/{selected_station}">Click here if you are not redirected.</a></p>
                        <audio controls autoplay>
                            <source src="/{selected_station}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                        <br><br>
                        <a href="/">Go back to list</a>
                    </body>
                    </html>
                    """
                
            # Keypad 4: Previous Page
            elif key == '4' and page > 1:
                page -= 1
            
            # Keypad 6: Next Page
            elif key == '6' and page < total_pages:
                page += 1
                
            # Keypad 0: Random Station (Redirect to random station's stream link)
            elif key == '0':
                import random
                random_station = random.choice(STATION_NAMES)
                return f"""
                    <!DOCTYPE html>
                    <html lang="en">
                    <head>
                        <title>Playing {random_station.replace('_', ' ').title()}</title>
                        <meta http-equiv="refresh" content="0; url=/{random_station}">
                    </head>
                    <body>
                        <p>Starting random stream for <strong>{random_station.replace('_', ' ').title()}</strong>... <a href="/{random_station}">Click here if you are not redirected.</a></p>
                        <audio controls autoplay>
                            <source src="/{random_station}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>
                        <br><br>
                        <a href="/">Go back to list</a>
                    </body>
                    </html>
                    """
            
        except ValueError:
            # Ignore non-integer key inputs
            pass
            
    # 3. Handle page bounds after command processing
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages

    # 4. Determine slice indices for the current page
    start_index = (page - 1) * STATIONS_PER_PAGE
    end_index = start_index + STATIONS_PER_PAGE
    
    # 5. Get stations for the current page
    stations_on_page = STATION_NAMES[start_index:end_index]
    
    # 6. Prepare Station List for HTML
    station_list_html = ""
    for i, station_name in enumerate(stations_on_page):
        # 1-based index for keypad
        keypad_number = i + 1 
        display_name = station_name.replace('_', ' ').title()
        
        # Stream link
        stream_link = f'/{station_name}'
        
        # The new list item includes the keypad number and a link that simulates a keypress
        station_list_html += f"""
            <li>
                <a href="/?page={page}&key={keypad_number}">
                    <span class="keypad-num">[{keypad_number}]</span> 
                    <strong>{display_name}</strong>
                </a>
                <audio controls style="display: block; margin-top: 5px;">
                    <source src="{stream_link}" type="audio/mpeg">
                    <p style="font-size: 0.8em; color: #666; margin: 5px 0 0;">Browser not supported.</p>
                </audio>
            </li>
        """

    # 7. Render HTML
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>📻 Radio Stations Keypad</title>
        <style>
            body {{ font-family: sans-serif; margin: 20px; max-width: 600px; margin-left: auto; margin-right: auto; }}
            h1 {{ color: #333; font-size: 1.5em; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 8px; background-color: #f9f9f9; }}
            a {{ text-decoration: none; color: #007BFF; display: block; padding: 5px 0; }}
            a:hover {{ text-decoration: underline; color: #0056b3; }}
            .keypad-num {{ color: #dc3545; font-weight: bold; font-size: 1.2em; margin-right: 10px; }}
            .keypad-controls {{ margin-top: 20px; display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; }}
            .keypad-controls a {{ padding: 15px 25px; border: 1px solid #007BFF; border-radius: 10px; display: inline-block; text-align: center; font-size: 1.2em; font-weight: bold; background-color: #e6f0ff; color: #007BFF; width: 40%; box-sizing: border-box; }}
            .keypad-controls a:active {{ background-color: #007BFF; color: white; }}
            .keypad-controls .special {{ background-color: #28a745; color: white; border-color: #28a745; }}
            audio {{ width: 100%; }}
        </style>
    </head>
    <body>
        <h1>📻 Stations (Page {page}/{total_pages})</h1>
        <p>Tap a station's name or use the keypad controls below (4=Prev, 6=Next, 0=Random).</p>
        <ul>
            {station_list_html}
        </ul>
        <div class="keypad-controls">
            <a href="/?page={page}&key=4">4: PREV PAGE</a>
            <a href="/?page={page}&key=6">6: NEXT PAGE</a>
            <a href="/?page={page}&key=0" class="special">0: RANDOM</a>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html_content)

# --- Streaming Function (Kept as is) ---

# 🔄 Streaming function with error handling
def generate_stream(url):
    process = None
    while True:
        if process:
            process.kill()

        process = subprocess.Popen(
            [
                "ffmpeg", "-reconnect", "1", "-reconnect_streamed", "1",
                "-reconnect_delay_max", "10", "-fflags", "nobuffer", "-flags", "low_delay",
                "-i", url, "-vn", "-ac", "1", "-b:a", "40k", "-buffer_size", "1024k", "-f", "mp3", "-"
            ],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=8192
        )

        print(f"🎵 Streaming from: {url} (Mono, 40kbps)")

        try:
            for chunk in iter(lambda: process.stdout.read(8192), b""):
                yield chunk
        except GeneratorExit:
            if process.poll() is None:
                process.kill()
            break
        except Exception as e:
            print(f"⚠️ Stream error: {e}")

        print("🔄 FFmpeg stopped, restarting stream...")
        time.sleep(5)

# --- Stream API (Kept as is) ---

# 🌍 API to stream a station
@app.route("/<station_name>")
def stream(station_name):
    url = RADIO_STATIONS.get(station_name)
    if not url:
        return "⚠️ Station not found", 404
    # Note: Returning the audio/mpeg stream directly.
    return Response(generate_stream(url), mimetype="audio/mpeg")

# --- Launch the app ---

if __name__ == "__main__":
    # Ensure you have FFmpeg installed and accessible in your environment's PATH!
    app.run(host="0.0.0.0", port=8000, debug=True)
