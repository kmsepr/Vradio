from flask import Flask, send_file, abort
import os

app = Flask(__name__)

@app.route("/")
def home():
    return "RVR XML Access Server"

@app.route("/vr.xml")
def serve_vr():
    file_path = "RVR/vr.xml"
    if os.path.exists(file_path):
        return send_file(file_path, mimetype="application/xml")
    else:
        return abort(404, description="vr.xml not found")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)