import os
from elevenlabs import ElevenLabs
from dotenv import load_dotenv

load_dotenv()

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

print("Fetching all voices from your ElevenLabs account...\n")

try:
    # Get all voices
    voices = elevenlabs_client.voices.get_all()

    print(f"Found {len(voices.voices)} voices:\n")
    print("=" * 80)

    for voice in voices.voices:
        print(f"\nName: {voice.name}")
        print(f"Voice ID: {voice.voice_id}")
        print(f"Category: {voice.category if hasattr(voice, 'category') else 'N/A'}")
        print(f"Description: {voice.description if hasattr(voice, 'description') and voice.description else 'N/A'}")
        print("-" * 80)

except Exception as e:
    print(f"Error: {e}")
