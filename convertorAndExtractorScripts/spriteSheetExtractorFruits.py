import os
from PIL import Image

script_dir = os.path.dirname(os.path.abspath(__file__))
sprite_sheet_path = os.path.join(script_dir, "../assets/sprite-sheets/fruits.png")
output_folder = os.path.join(script_dir, "../assets/food")
os.makedirs(output_folder, exist_ok=True)

# Sprite sheet layout: 6 columns × 6 rows
columns = 6
rows = 6
sheet = Image.open(sprite_sheet_path)
sheet_width, sheet_height = sheet.size
frame_width = sheet_width // columns
frame_height = sheet_height // rows

for idx in range(0, 36):
    row = idx // columns
    col = idx % columns
    left = col * frame_width
    upper = row * frame_height
    right = left + frame_width
    lower = upper + frame_height
    frame = sheet.crop((left, upper, right, lower))
    frame.save(os.path.join(output_folder, f"fruit_{idx+1}.png"))

print(f"✅ Saved fruit frames 1-36 to {output_folder}/")
