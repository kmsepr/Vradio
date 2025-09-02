import subprocess
import shutil
import os
from io import BytesIO
from datetime import datetime
from threading import Lock
from flask import Flask, Response, request, render_template_string, send_file, jsonify

app = Flask(__name__)

# ✅ Check ffmpeg
if not shutil.which("ffmpeg"):
    raise RuntimeError("ffmpeg not found. Please install ffmpeg.")

# 📡 Full list of radio stations (unchanged)
RADIO_STATIONS = {
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
    "bloomberg_tv": "https://bloomberg-bloomberg-3-br.samsung.wurl.tv/manifest/playlist.m3u8",
    "france_24": "https://live.france24.com/hls/live/2037218/F24_EN_HI_HLS/master_500.m3u8",
    "vom_radio": "https://radio.psm.mv/draair",
}

# ── State (single ffmpeg, in-memory recording) ────────────────────────────────
ffmpeg_process = None
current_station = None

recording_active = False
record_buffer = None           # BytesIO when recording
record_lock = Lock()           # guard record_buffer access

# ── HTML (your existing UI kept as-is) ────────────────────────────────────────
# Home and Player routes are unchanged from your code (omitted here for brevity)
# Keep your exact templates/scripts; they work with the same endpoints:
#   /play, /record, /record_size, /stop_record, /stop

# 🧰 helper: start ffmpeg once
def start_ffmpeg(url: str):
    global ffmpeg_process
    if ffmpeg_process:
        try:
            ffmpeg_process.kill()
        except Exception:
            pass
        ffmpeg_process = None

    # One ffmpeg -> mp3 -> stdout
    ffmpeg_process = subprocess.Popen(
        [
            "ffmpeg",
            "-reconnect", "1",
            "-reconnect_streamed", "1",
            "-reconnect_at_eof", "1",
            "-i", url,
            "-vn",
            "-c:a", "libmp3lame",
            "-b:a", "40k",
            "-f", "mp3",
            "-"  # stdout
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=0
    )

# 🎶 Stream playback (single source; Python-side tee to recorder)
@app.route("/play")
def play():
    global current_station

    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return "Station not found", 404

    url = RADIO_STATIONS[station]
    current_station = station

    start_ffmpeg(url)

    def generate():
        global ffmpeg_process
        try:
            while True:
                if not ffmpeg_process or not ffmpeg_process.stdout:
                    break
                chunk = ffmpeg_process.stdout.read(4096)
                if not chunk:
                    break
                # Tee to in-memory buffer if recording
                if recording_active:
                    with record_lock:
                        if record_buffer is not None:
                            record_buffer.write(chunk)
                yield chunk
        finally:
            # Do NOT kill ffmpeg here if someone else still needs it.
            # We leave /stop to kill explicitly.
            pass

    return Response(generate(), mimetype="audio/mpeg")

# 🎙 Toggle recording (no files written; buffer in RAM)
@app.route("/record")
def record():
    global recording_active, record_buffer

    station = request.args.get("station")
    if station not in RADIO_STATIONS:
        return jsonify({"status": "error", "message": "Station not found"}), 404

    # Ensure we're streaming the requested station
    if current_station != station:
        # Start stream for this station if needed
        start_ffmpeg(RADIO_STATIONS[station])

    if not recording_active:
        # Start: create a fresh in-memory buffer
        with record_lock:
            record_buffer = BytesIO()
        recording_active = True
        return jsonify({"status": "recording", "file": None})
    else:
        # Stop: prepare to download
        recording_active = False
        size_kb = 0
        with record_lock:
            if record_buffer is not None:
                size_kb = record_buffer.tell() // 1024
        return jsonify({"status": "stopped", "file": "/stop_record", "size": size_kb})

# 📏 Recording size API (RAM only)
@app.route("/record_size")
def record_size():
    active = recording_active
    size_kb = 0
    with record_lock:
        if active and record_buffer is not None:
            size_kb = record_buffer.tell() // 1024
    return jsonify({"size": size_kb, "active": active})

# ⏹️ Stop recording and download (send buffer; no disk writes)
@app.route("/stop_record")
def stop_record():
    global record_buffer
    with record_lock:
        if record_buffer is None or record_buffer.tell() == 0:
            return "No recording found", 404
        # Prepare a read handle
        record_buffer.seek(0)
        data = BytesIO(record_buffer.read())
        # free existing buffer
        record_buffer.close()
        record_buffer = None

    # Timestamped download name (but not saved server-side)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{(current_station or 'recording')}_{stamp}.mp3"
    return send_file(
        data,
        mimetype="audio/mpeg",
        as_attachment=True,
        download_name=filename
    )

# ⏹️ Stop playback (explicit)
@app.route("/stop")
def stop():
    global ffmpeg_process
    if ffmpeg_process:
        try:
            ffmpeg_process.kill()
        except Exception:
            pass
        ffmpeg_process = None
    return "⏹️ Stopped playback"

# ── Your existing Home / Player UI routes go here unchanged ───────────────────
# (Keep your same @app.route("/") home() and @app.route("/player") player() functions)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)