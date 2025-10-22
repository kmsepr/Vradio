🎧 Vradio

Vradio is a lightweight, Python-based radio streaming server designed for flexibility and quick deployment. It can host, relay, or play live internet radio streams using minimal system resources.


---

🚀 Features

📡 Serve or relay live audio streams

🐍 Built entirely in Python (91.9%)

🐳 Includes a Dockerfile for easy container deployment

⚙️ Configurable via stream.py and requirements.txt

🧩 Extensible modules: RVR, Radiobee

🖼️ Basic UI/branding asset (radio_bg.png)



---

🧰 Installation

Clone the repository

git clone https://github.com/kmsepr/Vradio.git
cd Vradio

Install dependencies

pip install -r requirements.txt


---

▶️ Usage

Run directly

python stream.py

Or with Docker

docker build -t vradio .
docker run -p 8000:8000 vradio

Then open in your browser or media player:

http://localhost:8000/stream


---

🧱 Project Structure

Vradio/
├── stream.py          # Core streaming logic
├── requirements.txt   # Python dependencies
├── Dockerfile         # Container configuration
├── radio_bg.png       # Background/logo
├── Radiobee/          # Supporting module
└── RVR/               # Supporting module


---

⚙️ Customization

You can modify stream.py to:

Add station lists or dynamic playlists

Proxy streams through FFmpeg or VLC

Integrate logging, metadata, or web UI



---

🐋 Deployment

Vradio can run on:

Local machines (Linux, macOS, Windows)

Docker containers (e.g., Koyeb, Heroku, etc.)

Raspberry Pi or small VPS servers



---

📜 License

This project currently has no explicit license. Please contact the repository owner before redistributing.


---

💡 Future Enhancements

Web interface for adding/editing stations

FFmpeg-based transcoding

Metadata (artist/title) display

Mobile-friendly player




