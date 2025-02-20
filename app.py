import os
import requests
import base64
import cloudinary
import cloudinary.uploader
from flask import Flask, request, jsonify, render_template

# API KEYS (Keep unchanged)
ELEVENLABS_API_KEY = "sk_e9333e611284999a1dabff584a7320362516e89b510bfe92"
DID_API_KEY = "ZGFuaWVsam9uc2VncEBnbWFpbC5jb20:eCaRO3pAQQHjQZWyyiGY_"
CLOUDINARY_CLOUD_NAME = "dvimbdohg"
CLOUDINARY_API_KEY = "568644676231352"
CLOUDINARY_API_SECRET = "m6qxR3SsOePnfi1C8nUC25k1kYY"

app = Flask(__name__)

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_CLOUD_NAME,
    api_key=CLOUDINARY_API_KEY,
    api_secret=CLOUDINARY_API_SECRET
)

# Fixed actor image URL (Replace if needed)
ACTOR_IMAGE_URL = "https://d-id-public-bucket.s3.us-west-2.amazonaws.com/alice.jpg"

# Store generated videos
video_storage = {}

@app.route("/")
def index():
    return render_template("index.html")

def text_to_speech(text):
    """Convert text to speech using ElevenLabs API"""
    print("🔹 Converting text to speech...")
    url = "https://api.elevenlabs.io/v1/text-to-speech/9BWtsMINqrJLrRacOk9x"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.8}
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        audio_path = "output.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)
        print("✅ TTS Success")
        return audio_path
    else:
        print(f"❌ TTS Error [{response.status_code}]:", response.text)
        return None

def upload_to_cloudinary(audio_path):
    """Upload MP3 file to Cloudinary and return URL"""
    print("🔹 Uploading audio to Cloudinary...")
    try:
        response = cloudinary.uploader.upload(audio_path, resource_type="auto")
        os.remove(audio_path)
        print("✅ Cloudinary Upload Success:", response["secure_url"])
        return response["secure_url"]
    except Exception as e:
        print("❌ Cloudinary Upload Error:", str(e))
        return None

def generate_video(audio_url):
    """Send audio to D-ID API for video generation"""
    print("🔹 Sending audio to D-ID API...")

    encoded_api_key = base64.b64encode(DID_API_KEY.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_api_key}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    payload = {
        "source_url": ACTOR_IMAGE_URL,
        "script": {
            "type": "audio",
            "audio_url": audio_url,
            "provider": "elevenlabs"
        },
        "config": {"stitch": True}
    }

    response = requests.post("https://api.d-id.com/talks", json=payload, headers=headers)

    if response.status_code == 201:
        video_id = response.json().get("id")
        print("✅ D-ID Video Started! Video ID:", video_id)
        return video_id
    else:
        print(f"❌ D-ID API Error [{response.status_code}]:", response.text)
        return None

@app.route("/generate", methods=["POST"])
def generate():
    """Generate AI video from text input"""
    data = request.json
    script = data.get("script")

    if not script:
        return jsonify({"error": "Missing script parameter"}), 400

    print(f"📝 Received script: {script}")

    # Step 1: Convert text to speech
    audio_path = text_to_speech(script)
    if not audio_path:
        return jsonify({"error": "Failed to generate audio"}), 500

    # Step 2: Upload to Cloudinary
    audio_url = upload_to_cloudinary(audio_path)
    if not audio_url:
        return jsonify({"error": "Failed to upload audio"}), 500

    # Step 3: Generate AI video
    video_id = generate_video(audio_url)
    if not video_id:
        return jsonify({"error": "D-ID API error"}), 500

    # Store video ID
    video_storage[video_id] = None  # Placeholder for video URL retrieval

    return jsonify({"message": "Video generation started!", "video_id": video_id})

@app.route("/retrieve", methods=["GET"])
def retrieve():
    """Retrieve video URL from D-ID API"""
    video_id = request.args.get("video_id")

    if not video_id:
        return jsonify({"error": "Missing video ID"}), 400

    if video_id in video_storage and video_storage[video_id]:
        return jsonify({"video_url": video_storage[video_id]})

    print(f"🔹 Retrieving video with ID: {video_id}")

    encoded_api_key = base64.b64encode(DID_API_KEY.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_api_key}",
        "Accept": "application/json"
    }

    response = requests.get(f"https://api.d-id.com/talks/{video_id}", headers=headers)

    if response.status_code == 200:
        video_url = response.json().get("result_url")
        if video_url:
            video_storage[video_id] = video_url  # Store for future use
            print(f"✅ Video Ready! URL: {video_url}")
            return jsonify({"video_url": video_url})
        else:
            return jsonify({"error": "Video still processing"}), 202
    else:
        return jsonify({"error": f"D-ID API Error [{response.status_code}]: {response.text}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
