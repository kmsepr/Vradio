

Vradio – Python Flask Radio Server

Vradio is a lightweight Python-based radio streaming server that allows you to manage, play, and share internet radio stations in real-time via a web interface.


---

🔧 Features

Add, delete, and manage radio stations via a web interface.

Supports multiple streaming qualities: Small (32kbps), Medium (64kbps), and Best (128kbps).

Stream audio directly via browser or media players using ffmpeg.

Copy station stream URLs to share or use in other apps.

Backup all stations as a JSON file (stations.json).

Minimal dependencies: Python, Flask, and FFmpeg.



---

🛠 Installation

1. Clone the repository:

git clone https://github.com/kmsepr/Vradio.git
cd Vradio


2. Install dependencies:

pip install flask

Make sure ffmpeg is installed and available in your system PATH.




---

🚀 Running the App

python app.py

The app will run on http://0.0.0.0:8080/.

Open the URL in your browser to access the home page.

Add stations by providing a name, stream URL, and quality.



---

🖥 Web Interface

Home Page

Add Station: Enter the station name, streaming URL, and select quality. Click Add Station.

Your Stations: Lists all saved stations with options to:

Click station name to play.

Copy the streaming URL.

Delete a station.


Backup: Download stations.json for backup.



---

Stream Route

GET /stream/<station_name>?quality=<small|medium|best>

Returns an audio-only MP3 stream of the selected station at the chosen quality.



---

Delete Station

POST /delete/<station_name>

Deletes the station from the database.



---

Backup JSON

GET /backup

Download your stations database as stations.json.



---

⚙ Configuration

STATIONS_JSON: Path to store saved stations.

LOG_PATH: Path for server logs.

ffmpeg: Used for audio streaming; ensure it's installed.



---

📄 License

MIT License – free to use, modify, and distribute.


