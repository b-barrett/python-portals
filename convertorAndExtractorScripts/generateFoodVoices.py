import os
import glob
import subprocess

# === CONFIG ===
FOOD_DIR = "../assets/food/food64"
OUTPUT_ROOT = "../assets/sounds"

VOICES = [
    "Bahh",
    "Carmit",
    "Cellos",
    "Daniel",
    "Flo",
    "Good",
    "Karen",
    "Organ",
    "Ralph",
    "Reed",
    "Rishi",
    "Rocko",
    "Whisper",
    "Wobble",
    "Zarvox"
]

# === Get all valid food .pngs (skip .meta) ===
food_files = [
    f for f in glob.glob(os.path.join(FOOD_DIR, "*"))
    if f.lower().endswith(".png") and not f.lower().endswith(".png.meta")
]

food_names = sorted(set(
    os.path.splitext(os.path.basename(f))[0].lower()
    for f in food_files
))

# === Generate clips for each voice ===
for voice in VOICES:
    output_dir = os.path.join(OUTPUT_ROOT, f"{voice.lower()}")
    os.makedirs(output_dir, exist_ok=True)
    generated_count = 0

    print(f"\n🎙️ Voice: {voice}")
    for food in food_names:
        tts_phrase = food.replace('_', ' ')
        display_name = tts_phrase.title()
        filename_safe = display_name.replace(" ", "_")

        aiff_path = os.path.join(output_dir, f"{filename_safe}.aiff")
        wav_path = os.path.join(output_dir, f"{filename_safe}.wav")

        if os.path.exists(wav_path):
            print(f"✅ Already exists: {voice}/{filename_safe}.wav")
            continue

        print(f"🎤 Generating: {voice}/{display_name}")
        try:
            subprocess.run(["say", "-v", voice, tts_phrase, "-o", aiff_path], check=True)
            subprocess.run(["afconvert", "-f", "WAVE", "-d", "LEI16", aiff_path, wav_path], check=True)
            os.remove(aiff_path)
            generated_count += 1
        except subprocess.CalledProcessError as e:
            print(f"❌ Error generating '{display_name}' for {voice}: {e}")

    print(f"✅ {voice}: {generated_count} new WAV files generated.")
