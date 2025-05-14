import os
from PIL import Image

script_dir = os.path.dirname(os.path.abspath(__file__))
sprite_sheet_path = os.path.join(script_dir, "../assets/sprite-sheets/portals.png")
output_folder = os.path.join(script_dir, "../assets/portals")
os.makedirs(output_folder, exist_ok=True)

# Sprite sheet layout: 8 columns × 3 rows
columns = 8
rows = 3
sheet = Image.open(sprite_sheet_path)
sheet_width, sheet_height = sheet.size
frame_width = sheet_width // columns
frame_height = sheet_height // rows

# Extract frames 9–24 (indices 8 to 23)
for idx in range(8, 24):
    row = idx // columns
    col = idx % columns
    left = col * frame_width
    upper = row * frame_height
    right = left + frame_width
    lower = upper + frame_height
    frame = sheet.crop((left, upper, right, lower))
    frame.save(os.path.join(output_folder, f"portal_frame_{idx+1}.png"))

print(f"✅ Saved portal frames 9–24 to {output_folder}/")
