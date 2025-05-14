from PIL import Image
import os
import shutil

# Define paths
script_dir = os.path.dirname(os.path.abspath(__file__))
textures_dir = os.path.join(script_dir, "../assets/backgrounds/textures")
output_dir   = os.path.join(script_dir, "../assets/backgrounds/textures-converted2-png")

# Create output directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# File extension counters
jpg_count = 0
png_count = 0

# Get all relevant image files, sorted
valid_exts = ('.jpg', '.jpeg', '.png')
image_files = sorted(
    f for f in os.listdir(textures_dir)
    if f.lower().endswith(valid_exts)
)

print(f"Found {len(image_files)} valid input files: {image_files}")


# Process all images and number them consistently
for i, filename in enumerate(image_files):
    input_path = os.path.join(textures_dir, filename)

    base_name = os.path.splitext(filename)[0].strip().replace(" ", "_")
    original_ext = os.path.splitext(filename)[1][1:].lower()  # e.g. 'jpg' without dot
    suffix = f"{i+1:02}"
    output_filename = f"{base_name}-{original_ext}-{suffix}.png"

    output_path = os.path.join(output_dir, output_filename)
    ext = os.path.splitext(filename)[1].lower()

    try:
        if filename.lower().endswith(('.jpg', '.jpeg')):
            with Image.open(input_path) as img:
                img.save(output_path)
            jpg_count += 1
        
        else:  # already a PNG, just copy and rename
            shutil.copy2(input_path, output_path)
            png_count += 1
        
        print(f"✔️  {filename} ({ext[1:]}) → {output_filename}")

    except Exception as e:
        print(f"⚠️  Failed to process {filename}: {e}")

# Summary
print(f"\n✅ Summary:")
print(f"  JPG/JPEG files processed: {jpg_count}")
print(f"  Preexisting PNG files copied: {png_count}")
print(f"  Total output PNG files: {jpg_count + png_count}")
