import os
import glob
from PIL import Image
from skin_config import skin_names as fantasy_names  # Imported fantasy skin names

def average_rgb_explicit(path, resize_to=(32, 32)):
    img = Image.open(path).convert("RGB")
    img = img.resize(resize_to)
    pixels = list(img.getdata())

    total_r = total_g = total_b = 0
    for r, g, b in pixels:
        total_r += r
        total_g += g
        total_b += b

    num_pixels = len(pixels)
    return (total_r // num_pixels, total_g // num_pixels, total_b // num_pixels)

def average_rgb_compact(path, resize_to=(32, 32)):
    img = Image.open(path).convert("RGB")
    img = img.resize(resize_to)
    pixels = list(img.getdata())

    num_pixels = len(pixels)
    return tuple(sum(c[i] for c in pixels) // num_pixels for i in range(3))

def extract_names_from_filename(filename):
    base = os.path.basename(filename)
    name_part = base.split("_", 1)[-1].rsplit(".", 1)[0]
    formatted = name_part.replace("_", " ").title().replace(" ", "")
    return formatted

def main():
    folder = "../assets/snake_skins"
    pattern = os.path.join(folder, "[0-1][0-9]_*.png")  # matches 01_ to 14_
    skin_paths = sorted(glob.glob(pattern))

    print(f"Matched {len(skin_paths)} skin files:")
    for path in skin_paths:
        print(f" - {path}")

    if not skin_paths:
        print("⚠️  No skin files matched. Check folder path or filename pattern.")
        return

    original_names = []
    head_colors_explicit = []
    head_colors_compact = []

    for i, path in enumerate(skin_paths):
        try:
            original_name = extract_names_from_filename(path)
            original_names.append(original_name)
            head_colors_explicit.append(average_rgb_explicit(path))
            head_colors_compact.append(average_rgb_compact(path))
        except Exception as e:
            print(f"❌ Error processing {path}: {e}")

    output_file = "snake_skin_data.py"
    with open(output_file, "w") as f:
        f.write("HEAD_COLORS_EXPLICIT = [\n")
        for rgb, name in zip(head_colors_explicit, fantasy_names):
            f.write(f"    {rgb},  # {name}\n")
        f.write("]\n\n")

        f.write("HEAD_COLORS_COMPACT = [\n")
        for rgb, name in zip(head_colors_compact, fantasy_names):
            f.write(f"    {rgb},  # {name}\n")
        f.write("]\n\n")

        f.write("ORIGINAL_NAMES = [\n")
        for name in original_names:
            f.write(f"    \"{name}\",\n")
        f.write("]\n\n")

        f.write("SKIN_NAMES = [\n")
        for name in fantasy_names:
            f.write(f"    \"{name}\",\n")
        f.write("]\n\n")

        f.write("# Combined mapping (index-matched)\n")
        f.write("SKIN_TO_COLOR_EXPLICIT = list(zip(SKIN_NAMES, ORIGINAL_NAMES))\n")

    print(f"\n✅ Saved to {output_file}")

if __name__ == "__main__":
    main()
