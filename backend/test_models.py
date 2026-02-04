import os
from elevenlabs import ElevenLabs, VoiceSettings
from dotenv import load_dotenv

load_dotenv()

elevenlabs_client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

test_text = "Hello! I'm Raj, your interviewer for today. It's great to meet you!"

# Test different models
models = [
    "eleven_monolingual_v1",
    "eleven_multilingual_v2",
    "eleven_turbo_v2_5",
    "eleven_turbo_v2"
]

print(f"Testing Voice ID: {VOICE_ID}\n")
print("=" * 80)

for model_id in models:
    print(f"\nTesting model: {model_id}")
    try:
        audio = elevenlabs_client.text_to_speech.convert(
            voice_id=VOICE_ID,
            text=test_text,
            model_id=model_id,
            voice_settings=VoiceSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                use_speaker_boost=True
            )
        )

        output_file = f"test_{model_id}.mp3"
        with open(output_file, 'wb') as f:
            for chunk in audio:
                f.write(chunk)

        print(f"✅ Success! Saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error with {model_id}: {e}")

print("\n" + "=" * 80)
print("\nAll test files generated. Playing them in sequence...\n")

# Play all files
for model_id in models:
    output_file = f"test_{model_id}.mp3"
    if os.path.exists(output_file):
        print(f"\n▶ Playing: {model_id}")
        os.system(f"afplay {output_file}")
        print(f"   (File: {output_file})")
