import requests
import base64
import time

DID_API_KEY = "ZGFuaWVsam9uc2VncEBnbWFpbC5jb20:eCaRO3pAQQHjQZWyyiGY_"

def retrieve_video(video_id, max_retries=10, delay=5):
    """Retrieve video URL from D-ID API with retries"""
    if not video_id:
        print("❌ Error: Missing video ID")
        return None

    encoded_api_key = base64.b64encode(DID_API_KEY.encode()).decode()
    headers = {
        "Authorization": f"Basic {encoded_api_key}",
        "Accept": "application/json"
    }

    print(f"🔹 Fetching video for ID: {video_id}...")

    for attempt in range(max_retries):
        response = requests.get(f"https://api.d-id.com/talks/{video_id}", headers=headers)

        if response.status_code == 200:
            video_url = response.json().get("result_url")
            if video_url:
                print(f"✅ Video is ready! Download here: {video_url}")
                return video_url
            else:
                print(f"⏳ Attempt {attempt + 1}/{max_retries}: Video is still processing...")
        else:
            print(f"❌ Error [{response.status_code}]: {response.text}")
            return None

        time.sleep(delay)  # Wait before retrying

    print("❌ Video processing took too long. Try again later.")
    return None

if __name__ == "__main__":
    video_id = input("Enter Video ID: ")
    retrieve_video(video_id)
