import pygame
pygame.init()

# Desired font name
emoji_font_name = "apple color emoji"
normalized_name = emoji_font_name.lower().replace(" ", "")

# Get all system fonts (lowercase, spaceless)
available_fonts = pygame.font.get_fonts()

if normalized_name in available_fonts:
    print(f"✅ '{emoji_font_name}' is available!")
    matched_path = pygame.font.match_font(emoji_font_name)
    print(f"🔎 Matched font path: {matched_path}")
else:
    print(f"❌ '{emoji_font_name}' is NOT available.")