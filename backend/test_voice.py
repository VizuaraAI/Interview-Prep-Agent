import os
from elevenlabs import ElevenLabs, VoiceSettings
from dotenv import load_dotenv

load_dotenv()

# Initialize ElevenLabs client
elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

print(f"Using Voice ID: {VOICE_ID}")
print(f"API Key (first 20 chars): {os.getenv('ELEVENLABS_API_KEY')[:20]}...")

# Test text
test_text = "Hello! I'm Raj, your interviewer for today. It's great to meet you! Let's have a wonderful conversation about your ML engineering experience."

print(f"\nGenerating speech for: '{test_text}'")

try:
    # Generate audio
    audio = elevenlabs_client.text_to_speech.convert(
        voice_id=VOICE_ID,
        text=test_text,
        model_id="eleven_monolingual_v1",
        voice_settings=VoiceSettings(
            stability=0.5,
            similarity_boost=0.75,
            style=0.0,
            use_speaker_boost=True
        )
    )

    # Save to file
    output_file = "test_voice_output.mp3"
    with open(output_file, 'wb') as f:
        for chunk in audio:
            f.write(chunk)

    print(f"\n✅ Success! Audio saved to: {output_file}")
    print(f"\nPlay it with: open {output_file}")
    print(f"Or: afplay {output_file}")

except Exception as e:
    print(f"\n❌ Error: {e}")
