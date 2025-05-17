import pygame
pygame.init()

# List of fonts installed on system
available_fonts = pygame.font.get_fonts()

# Check for specific emoji-supporting font
emoji_font_name = "apple color emoji"
if emoji_font_name.lower().replace(" ", "") in available_fonts:
    print(f"✅ '{emoji_font_name}' is available!")
else:
    print(f"❌ '{emoji_font_name}' is NOT available.")