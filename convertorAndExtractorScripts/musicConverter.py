import csv
from pydub import AudioSegment
from pydub.utils import which
import os

# Ensure ffmpeg is available
AudioSegment.converter = which("ffmpeg")
if AudioSegment.converter is None:
    raise EnvironmentError("ffmpeg not found. Please install it and make sure it's in your PATH.")

def speed_change(sound, speed=1.0):
    """Change playback speed (tempo and pitch) by adjusting frame rate."""
    new_frame_rate = int(sound.frame_rate * speed)
    return sound._spawn(sound.raw_data, overrides={'frame_rate': new_frame_rate}).set_frame_rate(sound.frame_rate)

increment = 0.05

def generate_level_variants_for_file(input_path, output_subdir, csv_writer, base_speed=1.0, increment=None, levels=22):
    """Generate 22 tempo-increased .ogg variants of an audio file and record durations."""
    if increment is None:
        increment = globals()["increment"]  # or just: increment = increment (if declared global)

    if not os.path.exists(output_subdir):
        os.makedirs(output_subdir)

    original = AudioSegment.from_file(input_path)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    export_count = 0

    for level in range(1, levels + 1):
        speed = base_speed * (1 + increment * (level - 1))
        modified = speed_change(original, speed)
        duration_seconds = len(modified) / 1000.0
        out_path = os.path.join(output_subdir, f"{base_name}_level{level:02d}.ogg")
        modified.export(out_path, format="ogg")
        print(f"Exported: {out_path}")
        csv_writer.writerow([base_name, level, speed, f"{duration_seconds:.2f}", out_path])
        export_count += 1

    return export_count

def generate_ogg_levels_from_audio(input_dir, output_dir, csv_path):
    """Process all .wav, .mp3, and .ogg files, generate .ogg level variants, and log tempo/duration data to CSV."""
    os.makedirs(input_dir, exist_ok=True)
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)

    total_exports = 0

    file_exists = os.path.isfile(csv_path)
    with open(csv_path, mode='a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["Track Name", "Level", "Speed Multiplier", "Duration (s)", "Output Path"])

        for filename in os.listdir(input_dir):
            if filename.lower().endswith((".wav", ".mp3", ".ogg")):
                input_path = os.path.join(input_dir, filename)
                track_name = os.path.splitext(filename)[0]
                output_subdir = os.path.join(output_dir, f"{track_name}_inc{int(increment * 100):02d}")
                print(f"\nProcessing {filename}...")
                total_exports += generate_level_variants_for_file(input_path, output_subdir, writer)

    print(f"\n✅ Total exports completed: {total_exports} files")

# === USAGE ===
input_directory = "../assets/music/originals_final"
output_directory = "../assets/music/levels_final"
csv_output_path = "../assets/music/data/generated_track_durations.csv"

generate_ogg_levels_from_audio(input_directory, output_directory, csv_output_path)
