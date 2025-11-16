from flask import Flask, request, jsonify, render_template_string, send_file import yt_dlp import os import uuid

app = Flask(name) CACHE_DIR = 'cache' os.makedirs(CACHE_DIR, exist_ok=True)

HOME_HTML = """ <!doctype html>

<html>
<head>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>YouTube Lite</title>
<style>
body { font-family:sans-serif; background:#111; color:#eee; text-align:center; }
input { width:80%; padding:10px; border-radius:10px; border:none; margin-top:20px; }
.video { background:#222; padding:10px; border-radius:12px; margin:10px auto; width:90%; max-width:330px; }
a { color:#4cf; text-decoration:none; }
</style>
</head>
<body>
<h2>YouTube Lite 🎬</h2>
<form action='/search'>
<input name='q' placeholder='Search YouTube...'>
</form><h3>Cached Downloads</h3>
{% for file in files %}
<div class='video'>
{{ file }}<br>
<a href='/cached/{{ file }}'>Download</a>
</div>
{% else %}
<p>No cached files yet.</p>
{% endfor %}
</body>
</html>
"""SEARCH_HTML = """ <!doctype html>

<html>
<head>
<meta name='viewport' content='width=device-width, initial-scale=1'>
<title>Results</title>
<style>
body { font-family:sans-serif; background:#111; color:#eee; text-align:center; }
.video { background:#222; padding:10px; border-radius:12px; margin:10px auto; width:90%; max-width:330px; }
a { color:#4cf; text-decoration:none; }
</style>
</head>
<body>
<h2>Results for '{{ query }}'</h2>
{% for v in results %}
<div class='video'>
<b>{{ v.title }}</b><br>
<a href='/download?id={{ v.id }}'>Download MP3</a>
</div>
{% endfor %}
<br><a href='/'>⬅ Home</a>
</body>
</html>
"""@app.route('/') def home(): files = os.listdir(CACHE_DIR) return render_template_string(HOME_HTML, files=files)

@app.route('/search') def search(): q = request.args.get('q','').strip() if not q: return "No query", 400

ydl_opts = {
    'quiet': True,
    'skip_download': True,
    'extract_flat': True,
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    data = ydl.extract_info(f"ytsearch10:{q}", download=False)

results = []
for entry in data.get('entries',[]):
    results.append(type('Obj', (object,), {
        'title': entry.get('title'),
        'id': entry.get('id')
    }))

return render_template_string(SEARCH_HTML, results=results, query=q)

@app.route('/download') def download(): vid = request.args.get('id') if not vid: return "Missing ID", 400

filename = f"{uuid.uuid4()}.mp3"
outpath = os.path.join(CACHE_DIR, filename)

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': outpath,
    'quiet': True,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
}

with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.download([f'https://www.youtube.com/watch?v={vid}'])

return redirect(f'/cached/{filename}')

@app.route('/cached/path:name') def cached(name): path = os.path.join(CACHE_DIR, name) return send_file(path, as_attachment=True)

if name == 'main': app.run(host='0.0.0.0', port=8080)