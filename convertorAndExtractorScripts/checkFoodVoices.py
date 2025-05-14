import os
import glob

# === CONFIG ===
VOICE_ROOT = "../assets/sounds"
VOICES = [
    "Bahh", "Carmit", "Cellos", "Daniel", "Flo", "Good", "Karen",
    "Organ", "Ralph", "Reed", "Rishi", "Rocko", "Whisper", "Wobble", "Zarvox"
]

# Lowercase version of folder names
voice_dirs = [os.path.join(VOICE_ROOT, v.lower()) for v in VOICES]

# === Collect the full set of .wav filenames from the first voice ===
reference_dir = voice_dirs[0]
reference_files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(reference_dir, "*.wav")))

print(f"📂 Reference: {os.path.basename(reference_dir)} has {len(reference_files)} files.")

# === Compare all others against the reference ===
for v_dir, v_name in zip(voice_dirs, VOICES):
    if not os.path.exists(v_dir):
        print(f"❌ MISSING FOLDER: {v_name}")
        continue

    current_files = sorted(os.path.basename(f) for f in glob.glob(os.path.join(v_dir, "*.wav")))
    missing = set(reference_files) - set(current_files)
    extra = set(current_files) - set(reference_files)

    if missing or extra:
        print(f"\n⚠️ {v_name} has inconsistencies:")
        if missing:
            print(f"   - Missing: {', '.join(sorted(missing))}")
        if extra:
            print(f"   - Extra:   {', '.join(sorted(extra))}")
    else:
        print(f"✅ {v_name}: all files present")
