import os
import requests

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

def transcribe_audio(audio_bytes: bytes) -> str:
    url = "https://api.deepgram.com/v1/listen?model=nova-2&language=en"
    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "audio/wav"
    }

    response = requests.post(url, headers=headers, data=audio_bytes)
    response.raise_for_status()

    return response.json()["results"]["channels"][0]["alternatives"][0]["transcript"]
