# region SYSTEM SETUP (IMPORTS & INIT)
# === SYSTEM SETUP (IMPORTS & INIT) ===

# Standard library
import datetime
import glob
import json
import os
import random
import re
import shutil
import sys
import tempfile

# Third-party
import pygame
from pygame.math import Vector2

# Initialize all pygame modules (important: call before any mixer or display operations)
pygame.init()

# We compute screen size constants based on the display AFTER pygame is initialized
# We only load and convert images AFTER setting the real display mode
# So, convert() and convert_alpha() won’t crash due to missing display surface.
# If you move asset loading earlier in the file (before set_mode), add a dummy display

# Initialize the mixer module for sound and music
pygame.mixer.init()

# Reserve channel 4 for food voices to avoid conflict with other sound effects
pygame.mixer.set_reserved(4) # see: self.food_voice_channel = pygame.mixer.Channel(4)

# endregion

# region CONSTANTS & CONFIG
# === CONSTANTS & CONFIG ===

# Display & Timing
os.environ['SDL_VIDEO_CENTERED'] = '1'

info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h

CELL_SIZE = 30
NUM_CELLS = min(int(screen_width * 0.8) // CELL_SIZE, 
                int(screen_height * 0.8) // CELL_SIZE)
SCREEN_SIZE = CELL_SIZE * NUM_CELLS

HUD_HEIGHT = int(screen_height * 0.08)
OFFSET = Vector2(0, HUD_HEIGHT)  # Global offset for drawing under HUD

screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE + HUD_HEIGHT))
pygame.display.set_caption("Python Portals")

clock = pygame.time.Clock()
TICK = pygame.USEREVENT
RESTORE_VOLUME_AFTER_FOOD_SOUND = pygame.USEREVENT + 1

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
MY_FONT = "assets/fonts/VT323-Regular.ttf"
GAME_NAME = "Python Portals"

class FontManager:
    def __init__(self, screen_size):
        base_path = "assets/fonts/VT323-Regular.ttf"
        self.title = pygame.font.Font(base_path, screen_size // 12)
        self.body = pygame.font.Font(base_path, screen_size // 14)
        self.instructions = pygame.font.Font(base_path, screen_size // 18)
        self.small = pygame.font.Font(base_path, screen_size // 22)

        # keyword(s) for cleanup: font, screen_size

# FONTS = FontManager(SCREEN_SIZE)
# screen.blit(FONTS.instructions.render("Press P to pause", True, WHITE), pos)


class MarginsAndSpacing:
    pass # addtl keyword search: _y 

# Leaderboard
LEADERBOARD_FILE = "assets/leaderboard/leaderboard.json"
MAX_LEADERBOARD_ENTRIES = 10

# Game Timing
START_SPEED_SLOW = 240 # Initial speed in milliseconds
START_SPEED_FAST = 135 # Initial speed in milliseconds

SPEED_DELTA_SLOW = 10
SPEED_DELTA_FAST = 5

FINAL_LEVEL_SLOW = 2
FINAL_LEVEL_FAST = 3

MOUSE_BONUS_UNLOCK_SLOW = 240  # Snake must be moving at or faster than this to allow mouse bonuses
MOUSE_BONUS_UNLOCK_FAST = 135

BONUS_SPAWN_INTERVAL = 5000  # 5 seconds = 5000 ms
BONUS_LIFETIME_SEC = 5 # in seconds
NUM_MUSIC_TRACKS = 22

# Snake Eyes
EYE_RADIUS = CELL_SIZE // 6 # Eye size is 1/6 of the snake's body segment
EYE_OFFSET = CELL_SIZE // 4 # Eyes are positioned 1/4 of cell size from the edges
PUPIL_RADIUS = CELL_SIZE // 15 # Pupil size is 1/15 of the cell size
PUPIL_OFFSET = CELL_SIZE // 15 # Pupils can move within the eye by this amount

# endregion


# region UTILITY HELPERS
# === UTILITY HELPERS ===

# Load and prepare image function
def load_image(path, size=None, use_alpha=False, transparency=None):
    """
    Load an image, optionally scale it, convert for display, and set transparency.
    
    Args:
        path (str): Path to the image.
        size (tuple): Optional (width, height) to scale image to.
        use_alpha (bool): Preserve per-pixel transparency for PNG with full or partial transparency.
        transparency (int): Optional global alpha (0-255) to apply to entire surface.

    Returns:
        pygame.Surface: The prepared image surface.
    """
    raw = pygame.image.load(path)
    optimized = raw.convert_alpha() if use_alpha else raw.convert()
    if size:
        optimized = pygame.transform.scale(optimized, size)
    if transparency is not None:
        optimized.set_alpha(transparency)
    return optimized

# Sort by the numeric suffix (01, 02, ...)
def extract_suffix(path):
    """Extract numeric suffix from filename like 'texture-01.png' or 'texture-01.jpg'."""
    match = re.search(r"-(\d{2})\.(png|jpe?g)$", os.path.basename(path), re.IGNORECASE)
    return int(match.group(1)) if match else 0

def extract_fruit_index(path):
    """Extract the fruit index from a file path."""
    match = re.search(r"fruit_(\d+)\.png$", os.path.basename(path))
    return int(match.group(1)) if match else None

def load_yummy_sounds(directory):
    """Load all WAV files from the given directory and return a dict keyed by base name."""
    sounds = {}
    for path in glob.glob(os.path.join(directory, "*.wav")):
        filename = os.path.splitext(os.path.basename(path))[0]
        key = filename.lower().replace(" ", "_")
        sounds[key] = pygame.mixer.Sound(path)
    return sounds

# endregion


# region ASSET LOADING
# === ASSET LOADING ===

# Load available music options (one subfolder per music style)
music_folder_root = "assets/music/levels_final"
music_folder_paths = [
    os.path.join(music_folder_root, name)
    for name in os.listdir(music_folder_root)
    if os.path.isdir(os.path.join(music_folder_root, name))
]
music_folder_paths.sort()  # Optional alphabetical sorting
music_folder_names = [os.path.basename(path) for path in music_folder_paths]

# Load available food voice options (one subfolder per food voice)
voice_pack_root = "assets/sounds"
voice_pack_paths = [
    os.path.join(voice_pack_root, name)
    for name in os.listdir(voice_pack_root)
    if os.path.isdir(os.path.join(voice_pack_root, name))
]
voice_pack_paths.sort()
voice_pack_names = [os.path.basename(path) for path in voice_pack_paths]


def get_preview_track(folder_path):
    candidates = glob.glob(os.path.join(folder_path, "*level01.ogg"))
    if not candidates:
        raise FileNotFoundError(f"No preview track found in: {folder_path}")
    return candidates[0]  # Return the first match

def get_level_track_path(folder_path, level_number):
    """Returns the first matching *_levelXX.ogg file in the selected folder."""
    pattern = f"*level{level_number:02}.ogg"
    matches = glob.glob(os.path.join(folder_path, pattern))
    if not matches:
        raise FileNotFoundError(f"No music file found for level {level_number} in {folder_path}")
    return matches[0]  # Use first match: level 1

# Load skin, sorted alphabetically by number (file prefix: 01_, 02_, ..., 14_)
skin_files = sorted(glob.glob("assets/snakeskins/*.png"))

# Correct fantasy names for each skin, matching alphabetical file order
skin_names = [
    "Brickback",
    "Dragonscale",
    "Emberlash",
    "Serpentleaf",
    "Bloodhide",
    "Midnight Denim",
    "Rootscale",
    "Rusthide",
    "Zebrastrike",
    "Rocktongue",
    "Pitgold",
    "Glaciercoil",
    "Marbled Viper",
    "Corroscale"
]

HEAD_COLORS = [
    (162, 84, 77),  # Brickback
    (154, 111, 73),  # Dragonscale
    (171, 94, 45),  # Emberlash
    (76, 151, 53),  # Serpentleaf
    (89, 59, 57),  # Bloodhide
    (67, 75, 83),  # Midnight Denim
    (114, 94, 80),  # Rootscale
    (121, 74, 69),  # Rusthide
    (102, 100, 99),  # Zebrastrike
    (148, 147, 147),  # Rocktongue
    (117, 104, 85),  # Pitgold
    (59, 210, 202),  # Glaciercoil
    (162, 163, 175),  # Marbled Viper
    (112, 101, 52),  # Corroscale
]

# FYI: This uses os.path and glob for now.
# For cleaner path handling later, consider switching to pathlib (Python 3.4+).

# === BACKGROUND IMAGE LOADING ===

# Supported extensions (case-insensitive)
supported_exts = ["png", "PNG", "jpg", "JPG", "jpeg", "JPEG"]

# Collect matching files for each extension
background_files_by_ext = {
    ext: glob.glob(f"assets/backgrounds/Textures/*.{ext}")
    for ext in supported_exts
}

# Combine all files into one list
background_files = []
for ext in supported_exts:
    files = background_files_by_ext[ext]
    if files:
        print(f"Found {len(files)} files with extension .{ext}")
    background_files.extend(files)

if not background_files:
    raise FileNotFoundError("❌ No background images found in supported formats.")

# Sort by suffix (e.g., file-01.png, file-02.jpg) or fallback to alphabetical
background_files = sorted(background_files, key=extract_suffix)

print(f"✅ Loaded {len(background_files)} backgrounds across all extensions.")

# Load and scale backgrounds
backgrounds = [
    load_image(path, (SCREEN_SIZE, SCREEN_SIZE + HUD_HEIGHT), use_alpha=True)
    for path in background_files
]

# Load leaderboard trophy
trophy_img = load_image("assets/leaderboard/trophy.png", 
                        size=(CELL_SIZE*2, CELL_SIZE*2), use_alpha=False, transparency=255)

# Get all .png files in assets/food/food64
all_food_paths = glob.glob("assets/food/food64/*.png")

# Sort them alphabetically by filename
valid_food_paths = sorted(all_food_paths, key=lambda p: os.path.basename(p).lower())

# # legacy code: fruit PNG in assets/food
# # Filter only valid files and sort by number
# valid_food_paths = sorted(
#     [path for path in all_food_paths if extract_fruit_index(path) is not None],
#     key=extract_fruit_index
# )

# Load each image
food_images = [
    load_image(path, size=(CELL_SIZE, CELL_SIZE), use_alpha=True)
    for path in valid_food_paths
]

# endregion


# region LEADERBOARD LOGIC
# === LEADERBOARD LOGIC ===

def load_leaderboard():
    """
    Load and return the leaderboard data from a JSON file.

    Attempts to read the leaderboard data from the predefined file path (LEADERBOARD_FILE).
    Returns an empty list if the file doesn't exist, is unreadable, or contains invalid data.

    Returns:
        list: A list of leaderboard entries if the file is valid,
              or an empty list otherwise.
    """
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    
    try:
        with open(LEADERBOARD_FILE, "r") as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
            else:
                print("⚠️ Leaderboard file is not a list. Ignoring.")
                return []
    except (json.JSONDecodeError, OSError) as e:
        print(f"⚠️ Failed to load leaderboard: {e}")
        return []

def save_leaderboard(leaderboard):
    """Safely save the leaderboard to a JSON file using a temporary file and atomic replace."""
    temp_path = None
    try:
        # extract directory path of LEADERBOARD_FILE (if just filename default to current directory)
        dir_name = os.path.dirname(LEADERBOARD_FILE) or "."

        # create temp file in that same folder (real leaderboard.json untouched)
        with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name) as temp_file:
            json.dump(leaderboard, temp_file, indent=4)
            temp_path = temp_file.name
        
        # Replace real leaderboard.json only after temp write
        shutil.move(temp_path, LEADERBOARD_FILE)

    except Exception as e:
        print(f"❌ Error saving leaderboard: {e}")
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

def update_leaderboard(player_name, score, snake_length, level, bonus_points, duration=None):
    """
    Updates the game's leaderboard with new player data and returns timestamp if entry was successful.

    Args:
        player_name (str): Name of the player to add to leaderboard
        score (int): Player's final score
        snake_length (int): Final length of player's snake
        level (int): Level reached by player
        bonus_points (int): Additional bonus points earned

    Returns:
        float or None: Timestamp of the entry if successfully added to leaderboard, None if entry didn't make the cut

    Note:
        - Leaderboard is sorted by score (primary), snake size (secondary), and level (tertiary) in descending order
        - Only keeps top entries up to MAX_LEADERBOARD_ENTRIES
        - Automatically adds current date and timestamp to entry
        - Saves updated leaderboard to storage after modification

    Example:
        >>> timestamp = update_leaderboard("Player1", 100, 10, 2, 50)
        >>> print(timestamp)
        1634567890.123
    """
    leaderboard = load_leaderboard()
    today = datetime.datetime.now().strftime("%m/%d/%y")
    timestamp = datetime.datetime.now().timestamp()
    leaderboard.append({
        "name": player_name,
        "score": score,
        "size": snake_length,
        "date": today,
        "level": level,
        "bonus": bonus_points,
        "ts": timestamp,
        "duration": duration, 
        })
    leaderboard = sorted(
        leaderboard,
        key=lambda x: (
            x["score"],
            x["size"], 
            x["level"],
            -int(100 * x["bonus"] / x["score"]) if x["score"] > 0 else float("-inf")
        ),
        reverse=True
    )

    leaderboard = leaderboard[:MAX_LEADERBOARD_ENTRIES]
    save_leaderboard(leaderboard)

    return timestamp if any(entry.get("ts") == timestamp for entry in leaderboard) else None

# endregion


# region UI SCREENS & PLAYER SETUP
# === UI SCREENS & PLAYER SETUP ===

def initialize_game_session():
    player_name, snake_skin, skin_index, selected_music_index, selected_voice_index, selected_speed, voice_enabled = prompt_player_name_skin_music_voice_speed()
    
    head_color = HEAD_COLORS[skin_index]
    music_folder = music_folder_paths[selected_music_index]
    voice_folder = voice_pack_paths[selected_voice_index]

    game = Game(player_name, head_color, music_folder, voice_folder, selected_speed, voice_enabled)
    game.apply_player_name_and_skin(player_name, skin_index)
    game.speed_mode = selected_speed
    game.apply_speed_mode(selected_speed)
    game.reset_game_state()
    game.show_leaderboard = True
    return game, snake_skin, skin_names[skin_index]

def prompt_player_name_skin_music_voice_speed():
    INSTRUCTION_MARGIN_BOTTOM_2 = SCREEN_SIZE // 15
    
    center_y = SCREEN_SIZE // 16  # Base anchor point
    SPACING = CELL_SIZE*2

    welcome_y = center_y
    name_y = welcome_y + SPACING 
    voice_y = name_y + SPACING
    speed_y = voice_y + SPACING
    skin_y  = speed_y + SPACING
    preview_y = skin_y + SPACING

    PROMPT_BODY = pygame.font.Font(MY_FONT, SCREEN_SIZE // 14)
    PROMPT_INSTRUCTIONS = pygame.font.Font(MY_FONT, SCREEN_SIZE // 18)

    error_sound = pygame.mixer.Sound("assets/sounds/crunchybite.ogg")
    
    name = ""
    cursor_visible = True
    cursor_timer = 0
    skin_index = 0
    selected_music_index = 0
    selected_voice_index = 0
    voice_selected = False
    selected_speed = "Slow"

    while True:
        screen.fill(WHITE)

        # Welcome prompt
        speed_text = "WELCOME TO PYTHON PORTALS"
        speed_surf = PROMPT_BODY.render(speed_text, True, BLACK)
        speed_rect = speed_surf.get_rect(center=(SCREEN_SIZE // 2, welcome_y))
        screen.blit(speed_surf, speed_rect)

        # Name Prompt
        prompt_text = "Name: " + name
        if cursor_visible:
            prompt_text += "_"
        name_surf = PROMPT_BODY.render(prompt_text, True, BLACK)
        name_rect = name_surf.get_rect(center=(SCREEN_SIZE // 2, name_y))
        screen.blit(name_surf, name_rect)
        
        # Voice Label
        if voice_selected:
            voice_text = f"Voice: {voice_pack_names[selected_voice_index].capitalize()}"
        else:
            voice_text = "Voice: None (chomp only)"
     
        voice_label = PROMPT_BODY.render(voice_text, True, BLACK)
        voice_rect = voice_label.get_rect(center=(SCREEN_SIZE // 2, voice_y))
        screen.blit(voice_label, voice_rect)
        
        # Speed Label
        skin_label = PROMPT_BODY.render(f"Snake Speed: {selected_speed}", True, BLACK)
        skin_rect = skin_label.get_rect(center=(SCREEN_SIZE // 2, speed_y))
        screen.blit(skin_label, skin_rect)
        
        # Skin Label
        speed_label = PROMPT_BODY.render(f"Snakeskin: {skin_names[skin_index]}", True, BLACK)
        speed_rect = speed_label.get_rect(center=(SCREEN_SIZE // 2, skin_y))
        screen.blit(speed_label, speed_rect)

        # # Skin Preview 
        # skin_size = CELL_SIZE * 6
        # skin_preview = load_image(skin_files[skin_index], 
        #                           size=(skin_size, skin_size), 
        #                           use_alpha=True)
        
        # x = SCREEN_SIZE // 2 - (skin_size // 2)
        # y = skin_rect.bottom + SPACING*2
        # screen.blit(skin_preview, (x, preview_y))

        # # Font used above for "Snakeskin:"
        # font = PROMPT_BODY

        # skin_label_surf = font.render(f"Snakeskin: {skin_names[skin_index]}", True, BLACK)
        # skin_rect = skin_label_surf.get_rect(center=(SCREEN_SIZE // 2, skin_y))
        # screen.blit(skin_label_surf, skin_rect)

        # # Preview Position (fixed padding below label)
        # preview_spacing = SCREEN_SIZE // 40  # fixed spacing not tied to CELL_SIZE
        # skin_size = SCREEN_SIZE // 10        # fixed size for preview box
        # skin_preview = load_image(skin_files[skin_index], size=(skin_size, skin_size), use_alpha=True)

        # x = (SCREEN_SIZE - skin_size) // 2
        # y = skin_rect.bottom + preview_spacing
        # screen.blit(skin_preview, (x, y))


        # Constants (top of file or nearby)
        SKIN_PREVIEW_SIZE = SCREEN_SIZE // 4  # Larger preview
        PREVIEW_SPACING_BELOW_LABEL = SCREEN_SIZE // 40

        # In draw logic, after skin label
        skin_label_surf = PROMPT_BODY.render(f"Snakeskin: {skin_names[skin_index]}", True, BLACK)
        skin_rect = skin_label_surf.get_rect(center=(SCREEN_SIZE // 2, skin_y))
        screen.blit(skin_label_surf, skin_rect)

        # Load and draw preview box
        skin_preview = load_image(skin_files[skin_index], 
                                size=(SKIN_PREVIEW_SIZE, SKIN_PREVIEW_SIZE), 
                                use_alpha=True)

        x = (SCREEN_SIZE - SKIN_PREVIEW_SIZE) // 2


        # y = skin_rect.bottom + PREVIEW_SPACING_BELOW_LABEL
        # screen.blit(skin_preview, (x, y))

        # Voice instructions
        tab_surf = PROMPT_INSTRUCTIONS.render("Select Voice with Tab/Shift+Tab", True, BLACK)
        tab_rect = tab_surf.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - INSTRUCTION_MARGIN_BOTTOM_2*5))
        screen.blit(tab_surf, tab_rect)

        # Position box exactly between Snakeskin label and Voice Instructions
        center_y = (skin_rect.bottom + tab_rect.top) // 2
        preview_x = (SCREEN_SIZE - SKIN_PREVIEW_SIZE) // 2
        screen.blit(skin_preview, (preview_x, center_y - SKIN_PREVIEW_SIZE // 2))

        
        # Music instructions
        ud_arrow_surf = PROMPT_INSTRUCTIONS.render("Select Music with Up/Down Arrows", True, BLACK)
        ud_arrow_rect = ud_arrow_surf.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - INSTRUCTION_MARGIN_BOTTOM_2*4))
        screen.blit(ud_arrow_surf, ud_arrow_rect)
        
        # Skin instructions
        lr_arrow_surf = PROMPT_INSTRUCTIONS.render("Select Skin with Left/Right Arrows", True, BLACK)
        lr_arrow_rect = lr_arrow_surf.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - INSTRUCTION_MARGIN_BOTTOM_2*3))
        screen.blit(lr_arrow_surf, lr_arrow_rect)

        # Speed mode
        speed_text = "Click Anywhere on Screen to Change Speed"
        speed_surf = PROMPT_INSTRUCTIONS.render(speed_text, True, BLACK)
        speed_rect = speed_surf.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - INSTRUCTION_MARGIN_BOTTOM_2*2))
        screen.blit(speed_surf, speed_rect)
        
        confirm_surf = PROMPT_INSTRUCTIONS.render("Press ENTER to Confirm All", True, BLACK)
        confirm_rect = confirm_surf.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - INSTRUCTION_MARGIN_BOTTOM_2))
        screen.blit(confirm_surf, confirm_rect)
        
        pygame.display.update()
        clock.tick(30)
        cursor_timer += 1
        if cursor_timer >= 15:  # 15 frames equals 1/2 second at 30 FPS
            cursor_visible = not cursor_visible
            cursor_timer = 0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and name:
                    pygame.mixer.music.fadeout(250)
                    snake_skin = load_image(skin_files[skin_index], 
                                            size=(CELL_SIZE, CELL_SIZE), 
                                            use_alpha=True)
                    voice_enabled = voice_selected
                    return name, snake_skin, skin_index, selected_music_index, selected_voice_index, selected_speed, voice_enabled

                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]

                elif event.key == pygame.K_LEFT:
                    skin_index = (skin_index - 1) % len(skin_files)

                elif event.key == pygame.K_RIGHT:
                    skin_index = (skin_index + 1) % len(skin_files)

                elif event.key == pygame.K_UP:
                    selected_music_index = (selected_music_index - 1) % len(music_folder_paths)
                    preview_path = get_preview_track(music_folder_paths[selected_music_index])
                    pygame.mixer.music.load(preview_path)
                    pygame.mixer.music.set_volume(0.25)
                    pygame.mixer.music.play(-1, fade_ms=500)

                elif event.key == pygame.K_DOWN:
                    selected_music_index = (selected_music_index + 1) % len(music_folder_paths)
                    preview_path = get_preview_track(music_folder_paths[selected_music_index])
                    pygame.mixer.music.load(preview_path)
                    pygame.mixer.music.set_volume(0.25)
                    pygame.mixer.music.play(-1, fade_ms=500)

                elif event.key == pygame.K_TAB:
                    if not voice_selected:
                        voice_selected = True
                        selected_voice_index = 0 # Start at first voice (index 0) on first Tab
                    else:
                        if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                            selected_voice_index = (selected_voice_index - 1) % len(voice_pack_paths)
                        else:
                            selected_voice_index = (selected_voice_index + 1) % len(voice_pack_paths)

                    # === Mandatory voice preview: play first .wav in folder ===
                    preview_folder = voice_pack_paths[selected_voice_index]
                    wav_files = sorted(glob.glob(os.path.join(preview_folder, "*.wav")))

                    if wav_files:
                        try:
                            pygame.mixer.Sound(wav_files[0]).play()
                        except pygame.error as e:
                            print(f"⚠️ Error playing preview: {wav_files[0]} → {e}")
                    else:
                        print(f"❌ No .wav files found in: {preview_folder}")

                elif event.unicode.isprintable():
                    # Allow up to 8 characters total — we check length *before* adding next character
                    if len(name) < 8:
                        name += event.unicode
                    else:
                        error_sound.play()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):  # Left or right click
                selected_speed = "Fast" if selected_speed == "Slow" else "Slow"

def show_instructions_screen(game):
    font_title = pygame.font.Font(MY_FONT, SCREEN_SIZE // 12)
    font_body = pygame.font.Font(MY_FONT, SCREEN_SIZE // 20)
    font_prompt = pygame.font.Font(MY_FONT, SCREEN_SIZE // 20)

    title_y = SCREEN_SIZE // 14
    instructions_y = SCREEN_SIZE // 6
    prompt_y = SCREEN_SIZE + HUD_HEIGHT - (SCREEN_SIZE // 14)

    howto_lines = [
        "Use arrow keys to move your snake.",
        "Eat food to grow and score points.",
        "Eat four foods for portal.",
        "Enter portal to advance to next level.",
        "Snake speed increases each level.",
        "Food value increases each level.",
        "Use cursor to click blue square bonuses.",
        "Game ends when snake hits wall.",
        "Game ends when snake eats tail.",
        "Press P to pause and catch your breath.",
        f"Reach level {game.final_level} to achieve immortality.",
        "See you on the leaderboard!"
    ]

    while True:
        screen.fill(WHITE)

        # Title
        title = font_title.render("How to Play Python Portals", True, BLACK)
        screen.blit(title, title.get_rect(center=(SCREEN_SIZE // 2, title_y)))

        # How-to Lines
        for i, line in enumerate(howto_lines):
            rendered = font_body.render(line, True, BLACK)
            screen.blit(rendered, rendered.get_rect(center=(SCREEN_SIZE // 2, instructions_y + i * (SCREEN_SIZE // 15))))

        # Instructions
        prompt = font_prompt.render("Press ENTER to Return to Leaderboard", True, BLACK)
        screen.blit(prompt, prompt.get_rect(center=(SCREEN_SIZE // 2, prompt_y)))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return

# endregion


# region CLASSES
# === CLASSES ===

class Snake:
    
    def __init__(self, head_color, body_image):
        """Initialize the snake at the center of the screen with a single segment."""
        self.head_color = head_color
        self.body_image = body_image
        center = NUM_CELLS // 2
        self.body = [Vector2(center, center)]
        self.direction = Vector2(1, 0)

        # Copy the vector values of self.direction,
        # but store them in a separate Vector2 object.
        # Changing self.direction later will not affect self.last_direction.
        # Prevents snake from instantly reversing direction and crashing into itself
        # See docsdirection_vs_last_direction.md for full explanation.
        self.last_direction = Vector2(self.direction.x, self.direction.y) 
        self.grow = False

    def move(self):
        """Updates the snake's position based on its current direction.
        If the snake should grow, a new segment is added without removing the tail.
        """
        new_head = self.body[0] + self.direction
        self.body.insert(0, new_head)
        if not self.grow:
            self.body.pop()
        else:
            self.grow = False
        self.last_direction = self.direction 

    def draw(self):
        """
        Draws the snake on the game screen with a distinct head and body segments.
        The snake's head is drawn with a different color and includes animated eyes that follow
        the snake's direction. The body segments use a predefined body image texture.
        The drawing process includes:
        1. Converting grid coordinates to pixel coordinates
        2. Drawing the head with a special color
        3. Drawing body segments using the body image
        4. Adding eyes to the head:
            - White circles for the eye whites
            - Black pupils that move based on the snake's direction
        Note:
             - Coordinates are adjusted for HUD height
             - Eyes are positioned using EYE_OFFSET from cell edges
             - Pupils move based on PUPIL_OFFSET and current direction
        Dependencies:
             - pygame for drawing primitives
             - Global constants: CELL_SIZE, HUD_HEIGHT, EYE_OFFSET, EYE_RADIUS,
                PUPIL_OFFSET, PUPIL_RADIUS, WHITE, BLACK
        Returns:
             None
        """
        # loop through all cell coordinates in snake's body and convert to pixel coordinates
        # iow, px and py convert grid coordinates to pixel coordinates
        for index, segment in enumerate(self.body):
            px = segment.x * CELL_SIZE
            py = segment.y * CELL_SIZE + HUD_HEIGHT # Apply HUD shift
            rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)
            
            if index == 0:
                # Draw head with a different color
                pygame.draw.rect(screen, self.head_color, rect)
            else:
                screen.blit(self.body_image, (px, py))

            if index == 0:  # Draw eyes only for head
                
                base_x = px
                base_y = py
                
                # left eye is offset from left edge of cell
                eye1_center = (
                    int(base_x + EYE_OFFSET),
                    int(base_y + EYE_OFFSET)
                )

                # right eye is offset from right edge of cell
                eye2_center = (
                    int(base_x + CELL_SIZE - EYE_OFFSET),
                    int(base_y + EYE_OFFSET)
                )

                # Draw eyes
                pygame.draw.circle(screen, WHITE, eye1_center, EYE_RADIUS)
                pygame.draw.circle(screen, WHITE, eye2_center, EYE_RADIUS)

                # Calculate pupil direction based on snake's direction
                dir_x = int(self.direction.x * PUPIL_OFFSET)
                dir_y = int(self.direction.y * PUPIL_OFFSET)

                # Draw pupils
                pupil1_center = (eye1_center[0] + dir_x, eye1_center[1] + dir_y)
                pupil2_center = (eye2_center[0] + dir_x, eye2_center[1] + dir_y)
                
                pygame.draw.circle(screen, BLACK, pupil1_center, PUPIL_RADIUS)
                pygame.draw.circle(screen, BLACK, pupil2_center, PUPIL_RADIUS)

class Food:    
    def __init__(self, snake_body, image):
        """Initialize food at a random position not occupied by the snake."""
        self.position = self.random_position(snake_body)
        self.image = image

    def random_position(self, snake_body):
        """Generate a random position for food that doesn't overlap with the snake.
        
        Args:
            snake_body: List of Vector2 positions occupied by the snake
            
        Returns:
            Vector2: Random position for the food
        """
        all_positions = [Vector2(x, y) for x in range(NUM_CELLS) for y in range(NUM_CELLS)]
        safe_positions = [pos for pos in all_positions if pos not in snake_body]
        return random.choice(safe_positions)

    def draw(self):
        """Render the food on the screen."""
        px = self.position.x * CELL_SIZE
        py = self.position.y * CELL_SIZE + HUD_HEIGHT
        screen.blit(self.image, (px, py))

class Game:
    """Main game class that manages game state, updates, and rendering."""
    
    FADE_FRAMES = 15  # Number of frames for level transition fade effect
    
    def __init__(self, player_name, head_color, music_folder, voice_folder, speed_mode, voice_enabled):
        # Basic identity
        self.player_name = player_name
        self.head_color = head_color
        self.speed_mode = speed_mode
        self.voice_enabled = voice_enabled
        self.mouse_bonus_unlock_ms = None

        # Visuals
        self.background_index = random.randint(0, len(backgrounds) - 1)
        self.background = backgrounds[self.background_index]

        # Audio
        self.eat_sound = pygame.mixer.Sound("assets/sounds/crunchybite.ogg")
        self.bonus_sound = pygame.mixer.Sound("assets/sounds/shimmerbonus.ogg")
        self.portal_sound = pygame.mixer.Sound("assets/sounds/going-to-the-next-level-114480.ogg")
        self.food_voice_channel = pygame.mixer.Channel(4)
        self.food_voice_queue = []  # FIFO queue for pending sounds
        self.voice_queue_ready_time = 0  # Time (ms) after which we allow playing voice
        
        self.music_folder = music_folder

        self.voice_folder = voice_folder
        self.yummy_sounds = load_yummy_sounds(voice_folder)

        # Leaderboard
        self.show_leaderboard = False
        self.highlight_entry_ts = None  # holds the just-played timestamp
        
        # Portal Animation
        self.load_portal_animation()

        # Bonus Tracking
        self.bonus_points_total = 0

        # UI Fonts
        self.font_large = pygame.font.Font(MY_FONT, 64)
        self.font_medium = pygame.font.Font(MY_FONT, 32)

        # Game Duration
        self.start_time = None
        self.end_time = None

        # Beat Game
        self.show_victory_screen = False
        self.victory_start_time = None

        # Game Over
        self.game_over_already_ran = False

    def reset_game_state(self):
        """Reset the game to its initial state used on first load and after game over."""

        # Game progress
        self.start_time = pygame.time.get_ticks()
        self.end_time = None
        self.level = 1
        self.score = 0
        self.level_score = 0  # Track points earned in current level
        self.points_to_portal = 4  # Points needed per level to open portal
        self.food_point_value = 1  # Base point value for level 1
        
        # Snake speed
        self.apply_speed_mode(self.speed_mode)

        # Snake head and body
        self.snake = Snake(self.head_color, self.snake_body_image)

        # Food
        self.food_name, self.food_image = self.current_food()
        self.food = Food(self.snake.body, self.food_image)

        # Level transition
        self.portal_open = False
        self.portal_position = None
        self.transitioning = False
        self.transition_total_frames = self.FADE_FRAMES
        self.transition_frames = 0
        self.fade_surface = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE + HUD_HEIGHT))
        self.fade_surface.fill(WHITE) # Fill with white color
        self.fade_surface.set_alpha(0) # Make invisible at start
        
        # Bonus state
        self.bonus_active = False
        self.bonus_position = None
        self.bonus_popup = None
        self.bonus_timer = 0
        self.bonus_points_total = 0
        self.last_bonus_spawn_time = pygame.time.get_ticks() # Timestamp of last bonus spawn

        # Clean up food voice queue (prevent leftover playback from prior session)
        self.food_voice_queue.clear()
        self.voice_queue_ready_time = 0

        # Game state
        self.game_over_already_ran = False
        self.paused = False
        pygame.time.set_timer(TICK, self.snake_speed_ms)

        # Victory state resets
        self.victory_start_time = None  # Prevent carryover from previous game
        self.show_victory_screen = False

    def apply_player_name_and_skin(self, player_name, skin_index):
        """Safely update name, head color, and body image, even if snake not yet created."""
        self.player_name = player_name
        self.head_color = HEAD_COLORS[skin_index]
        self.snake_body_image = load_image(
            skin_files[skin_index], size=(CELL_SIZE, CELL_SIZE), use_alpha=True
        )
        # Only update the snake if it already exists
        if hasattr(self, "snake"):
            self.snake.head_color = self.head_color
            self.snake.body_image = self.snake_body_image

    def apply_speed_mode(self, mode):
        """Configure snake speed, delta, final level, and bonus unlock thresholds."""
        self.speed_mode = mode
        if mode == "Slow":
            self.snake_speed_ms = START_SPEED_SLOW
            self.speed_delta = SPEED_DELTA_SLOW
            self.final_level = FINAL_LEVEL_SLOW
            self.mouse_bonus_unlock_ms = START_SPEED_SLOW
        else:
            self.snake_speed_ms = START_SPEED_FAST
            self.speed_delta = SPEED_DELTA_FAST
            self.final_level = FINAL_LEVEL_FAST
            self.mouse_bonus_unlock_ms = START_SPEED_FAST

        print(f"[DEBUG] Speed mode set to {mode} → final level {self.final_level}")

    def load_portal_animation(self):
        PORTAL_SCALE = 2
        self.portal_frames = [
            load_image(f"assets/portals/portal_frame_{i}.png", 
                       size=(int(CELL_SIZE*PORTAL_SCALE), 
                             int(CELL_SIZE*PORTAL_SCALE)), use_alpha=True)
            for i in range(9, 25)
        ]
        self.portal_frame_index = 0
        self.portal_frame_tick_count = 0 # Counts number of ticks since last image frame change.
        # Ticks (game frames) before switching to next image frame. 
        # At 60 fps, each image frame runs for fps divided by tick_delay eg 60/3.75 = 16 fps. 
        # (for sprite sheet with 16 frames: 16 frames / 16 fps = 1 second animation cycle duration)
        self.portal_frame_tick_delay = 3.75
    
    def update(self):
        if self.game_over_already_ran or self.paused or self.show_victory_screen:
            return  # Do nothing if game_over() triggered, game paused, or victory message on screen

        # Handles fade transition/controlled pause between levels
        if self.paused or self.transitioning:
            if self.transitioning:
                self.transition_frames -= 1
                if self.transition_frames <= 0:
                    self.transitioning = False
                    self.start_level()
            return

        self.snake.move()
        self.check_food()
        self.check_collisions_and_portals()
        self.check_tail()

        current_time = pygame.time.get_ticks()
        time_since_last_bonus = current_time - self.last_bonus_spawn_time

        if (
            not self.transitioning and
            not self.bonus_active and  # No existing bonus
            self.snake_speed_ms <= self.mouse_bonus_unlock_ms and
            current_time - self.last_bonus_spawn_time >= BONUS_SPAWN_INTERVAL  # Enough time passed
        ):
            print(f"[DEBUG] Bonus check triggered after {time_since_last_bonus} ms")
            self.last_bonus_spawn_time = current_time  # Reset timer

            random_roll_for_bonus = random.random()
            print(f"[DEBUG] Random roll for bonus: {random_roll_for_bonus:.3f}")
            if random_roll_for_bonus <= 1/3:  # 33% bonus box spawn probability
                print("[DEBUG] Bonus will spawn.")
                self.spawn_bonus()
            else:
                print("[DEBUG] Bonus spawn skipped.")
    
        if self.bonus_active:
            DEBUG = False
            if DEBUG:
                print(f"Bonus active: {self.bonus_timer} frames remaining")
            self.bonus_timer -= 1
            if self.bonus_timer <= 0:
                self.bonus_active = False
                self.bonus_position = None
        
        head = self.snake.body[0]
        if not (0 <= head.x < NUM_CELLS) or not (0 <= head.y < NUM_CELLS):
            print(f"[FATAL] Snake head moved out of bounds: {head}")

        if (not self.food_voice_channel.get_busy() 
            and self.food_voice_queue 
            and current_time >= self.voice_queue_ready_time
            and self.voice_enabled):
                food_name_key, next_sound = self.food_voice_queue.pop(0)

                # Temporarily reduce background music volume
                pygame.mixer.music.set_volume(0.50)

                self.food_voice_channel.play(next_sound)
                print(f"Played: {food_name_key} from voice: {os.path.basename(self.voice_folder)}")

                # Schedule background volume restoration after food sound finishes
                food_sound_duration_ms = int(next_sound.get_length() * 1000)
                pygame.time.set_timer(RESTORE_VOLUME_AFTER_FOOD_SOUND, food_sound_duration_ms, loops=1)

    def check_food(self):
        """Check if the snake has eaten food and handle accordingly."""
        if self.snake.body[0] == self.food.position:
            self.snake.grow = True
            self.score += self.food_point_value  # Add level-specific point value to total score
            self.level_score += self.food_point_value  # Add to level-specific score
        
            # Play eating sound
            self.eat_sound.play()

            self.voice_queue_ready_time = pygame.time.get_ticks() + 100  # wait 100ms

            # Play food voice
            food_name_key = self.food_name.lower()
            if food_name_key in self.yummy_sounds:
                self.food_voice_queue.append((food_name_key, self.yummy_sounds[food_name_key]))
                print(f"Queued: {food_name_key}") # debug

            print(f"Ate: {self.food_name}")

            self.food_name, self.food_image = self.current_food()
            self.food = Food(self.snake.body, self.food_image)

            # Open portal when reaching required points in the current level
            if not self.portal_open and self.level_score >= self.points_to_portal:
                self.generate_random_portal()

    def check_collisions_and_portals(self):
        """Check if the snake has hit walls or entered a portal."""
        head = self.snake.body[0]

        # debug
        if not head.x.is_integer() or not head.y.is_integer():
            print(f"[ERROR] Non-integer snake head detected: {head}")

        if self.portal_open and head == self.portal_position:
            self.portal_sound.play()
            print(f"[DEBUG] Portal entered at level {self.level}")

            if self.level == self.final_level - 1:
                print(f"[DEBUG] Triggering victory screen for final_level={self.final_level}")
                self.show_victory_screen = True
                self.transitioning = False  # Prevents unwanted level start
                return
        
            self.snake_speed_ms -= self.speed_delta  # Progressive speed increase
            self.level += 1
            self.transitioning = True
            self.transition_total_frames = self.FADE_FRAMES
            self.transition_frames = self.transition_total_frames
            self.portal_open = False
            self.portal_position = None

            # Clean blue bonus boxes during level transition
            self.bonus_active = False
            self.bonus_position = None
            self.bonus_popup = None

            return

        if head.x < 0 or head.x >= NUM_CELLS or head.y < 0 or head.y >= NUM_CELLS:
            print(f"[DEBUG] Wall collision at {head} — triggering game over")
            if self.portal_open:
                print(f"[DEBUG] Portal open at: {self.portal_position}")
            self.game_over()

    def check_tail(self):
        """Check if the snake has collided with itself."""
        head = self.snake.body[0]
        body_positions = {(segment.x, segment.y) for segment in self.snake.body[1:]} # set of tuples
        head_pos = (head.x, head.y)
        if head_pos in body_positions:
            self.game_over()

    def game_over(self):
        if self.game_over_already_ran:
            return
        self.game_over_already_ran = True

        self.end_time = pygame.time.get_ticks()
        if self.score > 0:
            entry_timestamp = update_leaderboard(
                self.player_name, self.score, len(self.snake.body),
                self.level, self.bonus_points_total, self.game_duration())
            self.highlight_entry_ts = entry_timestamp
        
        pygame.mixer.music.fadeout(500)  # ⬅️ Stop music immediately
        print("Game Over - resetting everything")
        self.show_leaderboard = True

    def game_duration(self):
        if self.start_time is None or self.end_time is None:
            return "N/A"
        duration_ms = self.end_time - self.start_time
        minutes = duration_ms // 60000
        seconds = (duration_ms % 60000) // 1000
        return f"{minutes}:{seconds:02}"

    def spawn_bonus(self):
        """Randomly spawn a bonus on the board."""
        all_positions = [Vector2(x, y) for x in range(NUM_CELLS) for y in range(NUM_CELLS)]
        available_positions = [pos for pos in all_positions if pos not in self.snake.body]

        if available_positions:
            self.bonus_position = random.choice(available_positions)
            self.bonus_timer = int(BONUS_LIFETIME_SEC * (1000 / self.snake_speed_ms))
            self.bonus_active = True

    def draw(self):
        if self.show_leaderboard:
            self.draw_leaderboard()
            return  # Skip normal game drawing if showing leaderboard
       
        dimmed_bg = self.background.copy()
        overlay = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE + HUD_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, int(255*1/3)))  # RGBA tuple with desired alpha
        dimmed_bg.blit(overlay, (0, 0))

        # Blit dimmed background
        screen.blit(dimmed_bg, (0, 0))

        # Draw game elements on top — full brightness
        self.snake.draw()
        self.food.draw()

        if self.transitioning:
            font = self.font_large
            message = font.render(f"LEVEL {self.level}", True, WHITE)
            text_rect = message.get_rect(center=(SCREEN_SIZE // 2, (SCREEN_SIZE // 2) + HUD_HEIGHT))
            screen.blit(message, text_rect)

        self.draw_score()

        if self.transitioning:
            # Fading from full white (255) to transparent (0) over transition frames (15)
            # Fade ratio starts at 1.0 and goes to 0.0
            fade_ratio = self.transition_frames / self.transition_total_frames
            fade_alpha = int(255 * fade_ratio)
            self.fade_surface.set_alpha(fade_alpha)
            screen.blit(self.fade_surface, (0, 0))

        if self.portal_open and self.portal_position:
            px = self.portal_position.x * CELL_SIZE
            py = self.portal_position.y * CELL_SIZE + HUD_HEIGHT

            self.portal_frame_tick_count += 1
            if self.portal_frame_tick_count >= self.portal_frame_tick_delay:
                self.portal_frame_tick_count = 0
                self.portal_frame_index = (self.portal_frame_index + 1) % len(self.portal_frames)

            frame = self.portal_frames[self.portal_frame_index]

            offset_x = (frame.get_width() - CELL_SIZE) // 2
            offset_y = (frame.get_height() - CELL_SIZE) // 2

            screen.blit(frame, (px - offset_x, py - offset_y))

        if self.paused:
            pause_overlay = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE + HUD_HEIGHT))
            pause_overlay.fill(BLACK)
            pause_overlay.set_alpha(256/4)
            screen.blit(pause_overlay, (0, 0))
            
            font = self.font_large
            pause_text = font.render("PAUSED", True, WHITE)
            text_rect = pause_text.get_rect(center=(SCREEN_SIZE // 2, 
                                                    SCREEN_SIZE // 2 + HUD_HEIGHT))
            screen.blit(pause_text, text_rect)
            
            font = self.font_medium
            instruction = font.render("Press P to Resume", True, WHITE)
            inst_rect = instruction.get_rect(center=(SCREEN_SIZE // 2, 
                                                     SCREEN_SIZE // 2 + 50 + HUD_HEIGHT))
            screen.blit(instruction, inst_rect)

        if not self.paused and self.bonus_active and self.bonus_position:
            px = self.bonus_position.x * CELL_SIZE
            py = self.bonus_position.y * CELL_SIZE + HUD_HEIGHT
            bonus_rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (0, 0, 255), bonus_rect)

        if self.bonus_popup:
            if not self.paused: 
                popup_font = self.font_medium
                popup_text = popup_font.render(self.bonus_popup["text"], True, WHITE)
                popup_rect = popup_text.get_rect(center=self.bonus_popup["position"])
                screen.blit(popup_text, popup_rect)

                self.bonus_popup["timer"] -= 1
                if self.bonus_popup["timer"] <= 0:
                    self.bonus_popup = None  # Erase popup after time expires


    def draw_score(self):
        # Draw HUD background
        hud_bg = pygame.Rect(0, 0, SCREEN_SIZE, HUD_HEIGHT)
        pygame.draw.rect(screen, BLACK, hud_bg)

        # Setup font and color
        label_font = self.font_medium
        value_font = self.font_medium
        color = WHITE

        # List of all stat strings
        stats = [
            f"Score: {self.score}",
            f"Size: {len(self.snake.body)}",
            f"Speed: {round(1000 / self.snake_speed_ms, 1)}",
            f"Level: {self.level}",
            f"Portal: {max(0, self.points_to_portal - self.level_score)}"
        ]

        # Calculate spacing for even distribution across screen width
        spacing = SCREEN_SIZE // len(stats)

        # Render and center each stat
        for i, stat in enumerate(stats):
            label, value = stat.split(": ")

            x_center = spacing * i + spacing // 2

            label_surf = label_font.render(label.upper(), True, color)
            label_rect = label_surf.get_rect(center=(x_center, HUD_HEIGHT // 3))

            value_surf = value_font.render(value, True, color)
            value_rect = value_surf.get_rect(center=(x_center, (HUD_HEIGHT * 2) // 3))

            screen.blit(label_surf, label_rect)
            screen.blit(value_surf, value_rect)

    def draw_leaderboard(self):
        screen.fill(WHITE)

        # Layout Constants
        TITLE_MARGIN_TOP = SCREEN_SIZE // 14
        HEADER_MARGIN_TOP = SCREEN_SIZE // 6
        ENTRY_MARGIN_TOP = SCREEN_SIZE // 4
        INSTRUCTION_MARGIN_BOTTOM = SCREEN_SIZE // 16
        ENTRY_LINE_SPACING = SCREEN_SIZE // 15

        # Fonts
        title_font = pygame.font.Font(MY_FONT, SCREEN_SIZE // 14)
        header_font = pygame.font.Font(MY_FONT, SCREEN_SIZE // 18)
        entry_font = pygame.font.Font(MY_FONT, SCREEN_SIZE // 20)  
        instruction_font = pygame.font.Font(MY_FONT, SCREEN_SIZE // 20)

        # Draw Title
        title_text = title_font.render("Python Portals Leaderboard", True, BLACK)
        title_rect = title_text.get_rect(center=(SCREEN_SIZE // 2, TITLE_MARGIN_TOP))
        screen.blit(title_text, title_rect)

        # Calculate positions
        total_width = trophy_img.get_width() + title_text.get_width() + trophy_img.get_width() + 40

        center_x = SCREEN_SIZE // 2

        left_trophy_x = center_x - total_width // 2
        text_x = left_trophy_x + trophy_img.get_width() + 20
        right_trophy_x = text_x + title_text.get_width() + 20

        y = TITLE_MARGIN_TOP

        # Blit left trophy
        screen.blit(trophy_img, (left_trophy_x, y - trophy_img.get_height() // 2))

        # Blit title
        screen.blit(title_text, (text_x, y - title_text.get_height() // 2))

        # Blit right trophy
        screen.blit(trophy_img, (right_trophy_x, y - trophy_img.get_height() // 2))

        # Draw Headers
        headers = ["Rank", "Name", "Score", "Size", "Level", "Bonus", "Time", "Date"]
        spacing = SCREEN_SIZE // len(headers)

        for i, header in enumerate(headers):
            header_surf = header_font.render(header, True, BLACK)
            header_rect = header_surf.get_rect(center=(spacing * i + spacing // 2, 
                                                       HEADER_MARGIN_TOP))
            screen.blit(header_surf, header_rect)

        # Draw Leaderboard Entries
        leaderboard = load_leaderboard()

        # Find starting y so entries are centered between HEADER_MARGIN_TOP and screen bottom
        entries_start_y = ENTRY_MARGIN_TOP

        for idx, entry in enumerate(leaderboard):
            score = entry.get("score", 0)
            bonus = entry.get("bonus", 0)
            bonus_percent = int(100 * bonus / score) if score > 0 else 0
            short_date = entry.get("date", "N/A")[:5]  # Get first 5 characters of date string
            row = [
                f"{idx+1}",
                entry["name"],
                str(score),
                str(entry["size"]),
                str(entry["level"]),
                f"{bonus_percent}%",
                entry.get("duration", "N/A"),
                short_date
            ]

            is_highlight = self.highlight_entry_ts and entry.get("ts") == self.highlight_entry_ts
            row_color = (173, 216, 230) if is_highlight else WHITE

            row_height = entry_font.get_height()
            row_y = entries_start_y + idx * ENTRY_LINE_SPACING
            row_top = row_y - row_height // 2  # center align background with text

            row_rect = pygame.Rect(0, row_top, SCREEN_SIZE, row_height)
            pygame.draw.rect(screen, row_color, row_rect)

            for i, item in enumerate(row):
                entry_surf = entry_font.render(item, True, BLACK)
                entry_rect = entry_surf.get_rect(center=(
                    spacing * i + spacing // 2,
                    entries_start_y + idx * ENTRY_LINE_SPACING
                ))
                screen.blit(entry_surf, entry_rect)
        
        instructions_text = instruction_font.render(
            "Press ENTER to Play,", True, BLACK)
        instructions_rect = instructions_text.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - INSTRUCTION_MARGIN_BOTTOM*2))
        screen.blit(instructions_text, instructions_rect)

        instructions_text_2 = instruction_font.render(
            "H for How to Play, N for New Player", True, BLACK)
        instructions_rect_2 = instructions_text_2.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - INSTRUCTION_MARGIN_BOTTOM))
        screen.blit(instructions_text_2, instructions_rect_2)

    def generate_random_portal(self):
        """Generate a portal at a random position along the game boundary not occupied by food."""
        attempts = 0
        while True:
            wall = random.choice(["top", "bottom", "left", "right"])
            if wall == "top":
                x = random.randint(1, NUM_CELLS - 2)
                y = 0
            elif wall == "bottom":
                x = random.randint(1, NUM_CELLS - 2)
                y = NUM_CELLS - 1
            elif wall == "left":
                x = 0
                y = random.randint(1, NUM_CELLS - 2)
            else:
                x = NUM_CELLS - 1
                y = random.randint(1, NUM_CELLS - 2)

            candidate = Vector2(x, y)
            if candidate != self.food.position:
                self.portal_position = candidate
                self.portal_open = True
                print(f"\U0001f6aa Portal spawned at ({x}, {y})")
                break

            attempts += 1
            if attempts > 3:
                print("⚠️ Did not find portal position not occupied by food after 3 tries (~1 in 72 million)")
                self.portal_position = candidate # portal and food overlap
                self.portal_open = True
                break  

        if attempts > 0 and self.portal_open:
            print(f"🔁 Portal placement took {attempts} additional attempt{'s' if attempts != 1 else ''}")

    def start_level(self):
        """Initialize a new level after transition while preserving snake length."""
        pygame.mixer.music.fadeout(500) # Fade out over 0.5 seconds
        track_path = get_level_track_path(self.music_folder, self.level)
        print(f"Now playing: {track_path}")
        pygame.mixer.music.load(track_path)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play(-1, fade_ms=1000)

        previous_index = self.background_index
        while (new_index := random.randint(0, len(backgrounds) - 1)) == previous_index:
            pass
        self.background_index = new_index

        self.background = backgrounds[self.background_index]
        
        snake_length = len(self.snake.body) # Store snake length before reset
    
        self.snake = Snake(self.head_color, self.snake_body_image) # Reset position to single seg at center
        starting_pos = Vector2(NUM_CELLS // 2, NUM_CELLS // 2)
        # Rebuild snake body with preserved length
        for i in range(1, snake_length):
            segment_pos = starting_pos - self.snake.direction * i
            self.snake.body.append(segment_pos)
        
        self.food_name, self.food_image = self.current_food()
        self.food = Food(self.snake.body, self.food_image)

        self.level_score = 0 
        self.points_to_portal = 4 * self.level
        self.food_point_value = self.level
        self.portal_open = False
        self.portal_position = None
        pygame.time.set_timer(TICK, self.snake_speed_ms)
        print(f"\U0001f680 Level {self.level} @ {self.snake_speed_ms}ms")

    def current_food(self):
        """Return a random (food name, food image) pair."""
        index = random.randint(0, len(food_images) - 1)
        image = food_images[index]
        name = os.path.splitext(os.path.basename(valid_food_paths[index]))[0].lower()
        return name, image
    

    def show_victory(self):
        """Display the Victory screen after completing level 21."""
        self.transitioning = False  # Defensive: ensure level doesn’t accidentally start
        if self.victory_start_time is None:
            self.victory_start_time = pygame.time.get_ticks()
            self.victory_extra = 88
            self.score += self.victory_extra
            self.portal_sound.play()
            print(f"[DEBUG] Triggered victory screen at {self.victory_start_time}")
            return

        victory_y = SCREEN_SIZE // 4
        font_body = pygame.font.Font(MY_FONT, SCREEN_SIZE // 16)

        # Determine final top speed after one more level
        final_speed_ms = self.snake_speed_ms - self.speed_delta
        moves_per_sec = round(1000 / final_speed_ms, 2)

        lines = [
            "You entered the final portal!",
            "Snake is about to reach top speed",
            f"— {moves_per_sec} moves per second —",
            "too fast for the human brain to track.",
            "Luckily, you've achieved immortality.",
            f"Immortality bonus: {self.victory_extra} points",
            f"Final Score: {self.score} points"
        ]

        screen.fill(WHITE)

        for i, line in enumerate(lines):
            rendered = font_body.render(line, True, BLACK)
            screen.blit(rendered, rendered.get_rect(center=(
                SCREEN_SIZE // 2, victory_y + i * (SCREEN_SIZE // 15)))
                )

        pygame.display.update()

        # After 15 seconds, go to leaderboard
        elapsed = pygame.time.get_ticks() - self.victory_start_time
        print(f"[DEBUG] Victory screen shown for {elapsed} ms")
        if elapsed >= 15000:
            self.game_over()
            self.show_victory_screen = False

# endregion


# region GAME INITIALIZATION & MAIN LOOP
# === GAME INITIALIZATION & MAIN LOOP ===

game, snake_skin, chosen_skin_name = initialize_game_session()

# Main game loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            print(f"[DEBUG KEYDOWN] {pygame.key.name(event.key)}")

        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if game.show_leaderboard:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    game.apply_speed_mode(game.speed_mode) 
                    game.food_voice_queue.clear()
                    game.voice_queue_ready_time = 0
                    game.reset_game_state()
                    game.background_index = 0
                    game.start_level()
                    game.show_leaderboard = False
                    game.highlight_entry_ts = None

                elif event.key == pygame.K_h:
                    show_instructions_screen(game)

                elif event.key == pygame.K_n:
                    # Get player inputs from welcome screen
                    player_name, snake_skin, skin_index, selected_music_index, selected_voice_index, selected_speed, voice_enabled = prompt_player_name_skin_music_voice_speed()
                    
                    # Apply skin and player name
                    game.apply_player_name_and_skin(player_name, skin_index)
                    chosen_skin_name = skin_names[skin_index]
                    
                    # Set music and voice folder selections
                    game.music_folder = music_folder_paths[selected_music_index]
                    game.voice_folder = voice_pack_paths[selected_voice_index]
                    game.yummy_sounds = load_yummy_sounds(game.voice_folder)
                    
                    # Clean up voice queue before reusing game object
                    game.food_voice_queue.clear()
                    game.voice_queue_ready_time = 0

                    # Ensure speed mode and voice state are updated
                    game.voice_enabled = voice_enabled
                    game.speed_mode = selected_speed
                    game.apply_speed_mode(game.speed_mode)  # ensure final_level updates BEFORE reset
                    
                    # Reset all game state
                    game.reset_game_state()
                    
                    # Clear highlight from previous leaderboard entry
                    game.highlight_entry_ts = None

        else:
            if event.type == TICK and not game.paused:
                game.update()

            # Restore music volume after food voice ends
            if event.type == RESTORE_VOLUME_AFTER_FOOD_SOUND:
                pygame.mixer.music.set_volume(1.0)
                    
            # keyboard controls
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    game.paused = not game.paused
                    print(f"Game {'paused' if game.paused else 'resumed'}")
                elif not game.paused and not game.transitioning:

                    # See doc direction_vs_last_direction.md for full explanation.
                    if event.key == pygame.K_UP and game.snake.last_direction != Vector2(0, 1):
                        game.snake.direction = Vector2(0, -1)
                    elif event.key == pygame.K_DOWN and game.snake.last_direction != Vector2(0, -1):
                        game.snake.direction = Vector2(0, 1)
                    elif event.key == pygame.K_LEFT and game.snake.last_direction != Vector2(1, 0):
                        game.snake.direction = Vector2(-1, 0)
                    elif event.key == pygame.K_RIGHT and game.snake.last_direction != Vector2(-1, 0):
                        game.snake.direction = Vector2(1, 0)
                    
                    # Manual debug trigger
                    elif event.key == pygame.K_d:  # D for debug
                        print("=== Snake Debug Dump ===")
                        for i, segment in enumerate(game.snake.body):
                            print(f"  [{i}] {segment}")

            #   mouse controls
            if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3): # Left, Right click
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    
                    if game.bonus_active and game.bonus_position:
                        bonus_rect = pygame.Rect(
                            game.bonus_position.x * CELL_SIZE,
                            game.bonus_position.y * CELL_SIZE + HUD_HEIGHT,
                            CELL_SIZE,
                            CELL_SIZE
                        )
                        if bonus_rect.collidepoint(mouse_x, mouse_y):
                            bonus_points = game.level + 1
                            game.score += bonus_points
                            game.bonus_points_total += bonus_points
                            game.bonus_sound.play()
                            print(f"🎯 Bonus clicked: + {bonus_points}")
                            game.bonus_active = False
                            px = game.bonus_position.x * CELL_SIZE
                            py = game.bonus_position.y * CELL_SIZE + HUD_HEIGHT
                            game.bonus_popup = {
                                "text": f"+{bonus_points}",
                                "position": (px + CELL_SIZE // 2, py + CELL_SIZE // 2),
                                "timer": 60  # Frames the popup will last (~1 second at 60 fps)
                            }           

    if game.show_victory_screen:
        game.show_victory()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                print("⏩ Skipping to leaderboard early")
                game.game_over()
                game.show_victory_screen = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        continue

    game.draw()
    pygame.display.update()
    clock.tick(60)

# endregion