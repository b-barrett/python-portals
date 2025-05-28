# region SYSTEM SETUP
# === SYSTEM SETUP ===

# Standard library
import datetime
import glob
import json
import os
import random
import re
import shutil
import string
import subprocess
import sys
import tempfile

# Third-party
import pygame
import pygame.freetype
from pygame.math import Vector2
from pygame import Color

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

# endregion SYSTEM SETUP


# region CONSTANTS & CONFIG
# === CONSTANTS & CONFIG ===

# Display & Timing
os.environ['SDL_VIDEO_CENTERED'] = '1'

info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h

NUM_CELLS = 26
CELL_SIZE = min(int(screen_width * 0.82) // NUM_CELLS, 
                int(screen_height * 0.82) // NUM_CELLS)
SCREEN_SIZE = CELL_SIZE * NUM_CELLS

HUD_HEIGHT = int(screen_height * 0.10)
OFFSET = Vector2(0, HUD_HEIGHT)  # Global offset for drawing under HUD

screen = pygame.display.set_mode((SCREEN_SIZE, SCREEN_SIZE + HUD_HEIGHT), pygame.SCALED)
pygame.display.set_caption("Python Portals")

clock = pygame.time.Clock()
TICK = pygame.USEREVENT
RESTORE_VOLUME_AFTER_FOOD_SOUND = pygame.USEREVENT + 1

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (136, 8, 8)
GOLD = (255, 215, 0)
SMOKE = (177, 177, 177)
GAME_NAME = "Python Portals"

# In Frames Per Second
# Note: game framerate is 60 FPS. See: game.draw(); pygame.display.update(); clock.tick(60)

EFFECT_LIFETIME_SHORT = 15
EFFECT_LIFETIME_STANDARD = 30
EFFECT_LIFETIME_LONG = 60 # effect lasts 1 second at game's current framerate: clock.tick(60)

MY_FONT = "assets/fonts/VT323-Regular.ttf"
EMOJI_FONT = "Apple Color Emoji"

class Font:
    def __init__(self, screen_size):
        path = "assets/fonts/VT323-Regular.ttf"
        self.title_large = pygame.font.Font(path, screen_size // 12)
        self.title_medium = pygame.font.Font(path, screen_size // 14)
        self.body_large = pygame.font.Font(path, screen_size // 16)
        self.body_medium = pygame.font.Font(path, screen_size // 18)
        self.body_small = pygame.font.Font(path, screen_size // 20)
        self.label = pygame.font.Font(path, screen_size // 24)
        self.emoji = pygame.freetype.Font("/System/Library/Fonts/Apple Color Emoji.ttc", 64)

FONTS = Font(SCREEN_SIZE)

class Layout: # for future cleanup, keywords spacing, margin, layout, screen_size, _y, _x, cell_size
        def __init__(self, screen_size):
            self.center_x = screen_size // 2 # refactor "SCREEN_SIZE // 2" to LAYOUTS.center_x
            self.welcome_margin_bottom = screen_size // 16

LAYOUTS = Layout(SCREEN_SIZE)

# Leaderboard
LEADERBOARD_FILE = "assets/leaderboard/leaderboard.json"
MAX_LEADERBOARD_ENTRIES = 10

# Game Timing
START_SPEED_SLOW = 240 # Initial speed in milliseconds
START_SPEED_FAST = 135 # Initial speed in milliseconds

SPEED_DELTA_SLOW = 10
SPEED_DELTA_FAST = 5

FINAL_LEVEL_SLOW = 22
FINAL_LEVEL_FAST = 21

MOUSE_BONUS_UNLOCK_SLOW = 240  # Snake must be moving at or faster than this to allow mouse bonuses
MOUSE_BONUS_UNLOCK_FAST = 135

BONUS_SPAWN_INTERVAL = 4000  # 4 seconds = 4000 ms
BONUS_SPAWN_PROBABILITY = 1/4
BONUS_LIFETIME_SEC = 5 # in seconds

# === Enemy Snake Spawn Conditions ===
ENEMY_SPAWN_INTERVAL = 5000
ENEMY_SPAWN_PROBABILITY = 1
ENEMY_MARGIN = 4  # Number of cells from edge that enemy snakes avoid
ENEMY_MAX_SIZE = None

# Snake Eyes
EYE_RADIUS = CELL_SIZE // 6 # Eye size is 1/6 of the snake's body segment
EYE_OFFSET = CELL_SIZE // 4 # Eyes are positioned 1/4 of cell size from the edges
PUPIL_RADIUS = CELL_SIZE // 15 # Pupil size is 1/15 of the cell size
PUPIL_OFFSET = CELL_SIZE // 15 # Pupils can move within the eye by this amount

# endregion CONSTANTS & CONFIG


# region UTILITY HELPERS
# === UTILITY HELPERS ===

DEBUG_ENABLED = True  # Global master switch

DEBUG_ENABLED_TAGS = {
    "leaderboard": True,
    "UI": True,
    "snake": True,
    "enemy": True,
    "food": True,
    "portal": True,
    "music": True,
    "bonus": True,
    "draw": True,
    "game_over": True,
    "default": True
}

# 500 is 500ms or 1/2 second; 1000 is 1000ms or 1 second, etc...
DEBUG_THROTTLES = {
    "leaderboard": 500,
    "UI": 500,
    "snake": 500,
    "enemy": 1000,
    "food": 500,
    "portal": 500,
    "music": 500,
    "bonus": 500,
    "draw": 500,
    "game_over": 500,
    "default": 500
}

_last_debug_times = {}

def print_debug(tag, msg):
    """
    Print debug messages with timestamp-based throttling for specific tags.

    Args:
        tag (str): Debug category tag used for filtering and throttling messages
        msg (str): Debug message to be printed

    The function will only print if:
    - DEBUG_ENABLED is True
    - The tag is enabled in DEBUG_ENABLED_TAGS
    - Enough time has passed since last message with same tag (controlled by DEBUG_THROTTLES)

    Global variables used:
        DEBUG_ENABLED (bool): Master switch for debug output
        DEBUG_ENABLED_TAGS (dict): Dict of tag->bool indicating which tags are enabled
        DEBUG_THROTTLES (dict): Dict of tag->int for minimum ms between messages
        _last_debug_times (dict): Dict tracking last print time for each tag
    """
    if not DEBUG_ENABLED or not DEBUG_ENABLED_TAGS.get(tag, False):
        return

    now = pygame.time.get_ticks()
    throttle = DEBUG_THROTTLES.get(tag, DEBUG_THROTTLES["default"])
    last = _last_debug_times.get(tag, 0)

    if now - last >= throttle:
        print(f"[{tag.upper()}] {msg}")
        _last_debug_times[tag] = now

def to_cell(pos):
    """Return a Vector2 with integer (grid-snapped) coordinates.
    Accepts Vector2, tuple, or any object with .x and .y attributes.
    """
    if not isinstance(pos, Vector2):
        raise TypeError(f"Expected Vector2, got {type(pos).__name__}")
    return Vector2(int(pos.x), int(pos.y))

def get_snake_head_cell(snake):
    head = snake.body[0]
    return Vector2(int(head.x), int(head.y))

# endregion UTILITY HELPERS


# region ASSET LOADING
# === ASSET LOADING ===

# Load and prepare images
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

def load_yummy_sounds(directory):
    """Load all WAV files from the given directory and return a dict keyed by base name."""
    sounds = {}
    for path in glob.glob(os.path.join(directory, "*.wav")):
        filename = os.path.splitext(os.path.basename(path))[0]
        key = filename.lower().replace(" ", "_")
        sounds[key] = pygame.mixer.Sound(path)
    return sounds

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
    "King Cobra",
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

# For cleaner path handling later, consider switching from os.path and glob to pathlib.

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
    background_files.extend(files)

if not background_files:
    raise FileNotFoundError("❌ No background images found in supported formats.")

def extract_suffix(path):
    """Extract numeric suffix from filename like 'texture-01.png' or 'texture-01.jpg'."""
    match = re.search(r"-(\d{2})\.(png|jpe?g)$", os.path.basename(path), re.IGNORECASE)
    return int(match.group(1)) if match else 0

# Sort by suffix (e.g., file-01.png, file-02.jpg) or fallback to alphabetical
background_files = sorted(background_files, key=extract_suffix)

# Load and scale backgrounds
backgrounds = [
    load_image(path, (SCREEN_SIZE, SCREEN_SIZE + HUD_HEIGHT), use_alpha=True)
    for path in background_files
]

# Get all .png files in assets/food/food64
all_food_paths = glob.glob("assets/food/food64/*.png")

# Sort them alphabetically by filename
valid_food_paths = sorted(all_food_paths, key=lambda p: os.path.basename(p).lower())

# Load each image
food_images = [
    load_image(path, size=(CELL_SIZE, CELL_SIZE), use_alpha=True)
    for path in valid_food_paths
]

# endregion ASSET LOADING


# region LEADERBOARD LOGIC
# === LEADERBOARD LOGIC ===

def get_leaderboard_path(player_name=None, tournament_mode=False):
    if tournament_mode and player_name:
        safe_name = player_name.lower().replace(" ", "_")
        return os.path.join("assets", "leaderboard", f"{safe_name}.json")
    return LEADERBOARD_FILE
    
def save_active_leaderboard(player_name, leaderboard, tournament_mode=False):
    """Safely save the leaderboard (global or named) using a temporary file and atomic replace."""
    path = get_leaderboard_path(player_name, tournament_mode)
    temp_path = None
    try:
        # fallback in case path is just a filename
        dir_name = os.path.dirname(path) or "."
        # write to temp file first
        with tempfile.NamedTemporaryFile("w", delete=False, dir=dir_name) as temp_file:
            json.dump(leaderboard, temp_file, indent=4)
            temp_path = temp_file.name
        
        # atomically replace original
        shutil.move(temp_path, path)
        print_debug("leaderboard", f"✅ Saved leaderboard to {path}")

    except Exception as e:
        print_debug("leaderboard", f"[ERROR] Failed to save leaderboard to {path}: {e}")
        
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

def load_active_leaderboard(player_name=None, tournament_mode=False):
    path = get_leaderboard_path(player_name, tournament_mode)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            else:
                print_debug("leaderboard", f"⚠️ Leaderboard file {path} is not a list. Ignoring.")
                return []
    except (json.JSONDecodeError, OSError) as e:
        print_debug("leaderboard", f"⚠️ Failed to load leaderboard {path}: {e}")
        return []

def git_pull_leaderboard():
    if os.path.isdir(".git"):
        try:
            subprocess.run(["git", "pull", "origin", "main"], check=True)
            print_debug("leaderboard", "✅ Pulled latest leaderboard.json from GitHub")
        except subprocess.CalledProcessError as e:
            print_debug("leaderboard", f"❌ Git pull failed: {e}")
    else:
        print_debug("leaderboard", "Git pull skipped (not a Git repo)")

def git_push_leaderboard():
    if os.path.isdir(".git"):
        try:
            subprocess.run(["git", "add", "assets/leaderboard/leaderboard.json"], check=True)
            subprocess.run(["git", "commit", "-m", "Autoupdate leaderboard"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            print_debug("leaderboard", "✅ Pushed updated leaderboard.json to GitHub")
        except subprocess.CalledProcessError as e:
            print_debug("leaderboard", f"❌ Git push failed: {e}")
    else:
        print_debug("leaderboard", "Git push skipped (not a Git repo)")

def update_leaderboard(player_name, score, snake_length, level, bonus_points, penalty_points, duration=None, tournament_mode=False):
    leaderboard = load_active_leaderboard(player_name, tournament_mode)
    today = datetime.datetime.now().strftime("%m/%d/%y")
    timestamp = datetime.datetime.now().timestamp()
    leaderboard.append({
        "name": player_name,
        "score": score,
        "size": snake_length,
        "date": today,
        "level": level,
        "bonus": bonus_points,
        "penalty": penalty_points,
        "ts": timestamp,
        "duration": duration,
        })
    leaderboard = sorted(
        leaderboard,
        key=lambda x: (
            x["score"],
            x["size"], 
            x["level"],
            int(-100 * x["bonus"] / x["score"]) if x["score"] > 0 else float("inf")
        ),
        reverse=True
    )

    leaderboard = leaderboard[:MAX_LEADERBOARD_ENTRIES]
    
    # Save to correct path
    save_active_leaderboard(player_name, leaderboard, tournament_mode)
    
    # If this is the global leaderboard (not a named one), push changes to git
    if not tournament_mode:
        git_push_leaderboard()

    return timestamp if any(entry.get("ts") == timestamp for entry in leaderboard) else None

def load_global_leaderboard():
    if not os.path.exists(LEADERBOARD_FILE):
        return []
    try:
        with open(LEADERBOARD_FILE, "r") as file:
            data = json.load(file)
            if isinstance(data, list):
                return data
            else:
                print_debug("leaderboard", "⚠️ Leaderboard file is not a list. Ignoring.")
                return []
    except (json.JSONDecodeError, OSError) as e:
        print_debug("leaderboard", f"⚠️ Failed to load leaderboard: {e}")
        return []
    
def merge_named_leaderboards():
    """Merge all named test leaderboards in the high-level testing directory."""
    folder = os.path.dirname(LEADERBOARD_FILE)
    all_jsons = glob.glob(os.path.join(folder, "*.json"))

    merged = load_global_leaderboard()
    merged_count = 0

    for path in all_jsons:
        filename = os.path.basename(path)
        if filename == "leaderboard.json":
            continue
        print_debug("leaderboard", f"Merging: {filename}")
        merged_count += 1

        try:
            with open(path, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        required_keys = {"name", "score", "size", "date", "level", "bonus", "ts", "duration"}
                        if required_keys.issubset(entry.keys()):
                            merged.append(entry)
                        else:
                            print_debug("leaderboard", f"[WARN] Skipping malformed entry in {path}: {entry}")
        except Exception as e:
            print_debug("leaderboard", f"[ERROR] Failed to read {path}: {e}")

    # Deduplicate and sort
    seen_ts = set()
    unique = []

    for entry in merged:
        if entry["ts"] not in seen_ts:
            seen_ts.add(entry["ts"])
            unique.append(entry)

    if not unique:
        print_debug("leaderboard", f"[WARN] No valid leaderboard entries found — merge skipped.")
        return  # Just exit the function early without saving or pushing

    unique.sort(key=lambda x: (-x["score"], -x["size"], -x["level"],
                               int(-100 * x["bonus"] / x["score"]) if x["score"] > 0 
                               else float("inf")))
    
    top_10 = unique[:MAX_LEADERBOARD_ENTRIES]

    output_path = os.path.join(folder, "leaderboard.json")

    with open(output_path, "w") as f:
        json.dump(top_10, f, indent=4)

    print_debug("leaderboard", f"✅ Merged {len(unique)} unique entries from {merged_count} files → {output_path}")

    git_push_leaderboard()

    return len(unique)

# endregion LEADERBOARD LOGIC


# region UI & PLAYER SETUP
# === UI & PLAYER SETUP ===

def initialize_game_session():
    player_name, snake_skin, skin_index, selected_music_index, selected_voice_index, selected_speed, voice_enabled, tournament_mode = prompt_player_name_skin_music_voice_speed()
    
    head_color = HEAD_COLORS[skin_index]
    music_folder = music_folder_paths[selected_music_index]
    voice_folder = voice_pack_paths[selected_voice_index]

    game = Game(player_name, head_color, music_folder, voice_folder, selected_speed, voice_enabled,tournament_mode=tournament_mode)
    game.apply_player_name_and_skin(player_name, skin_index)
    game.speed_mode = selected_speed
    game.apply_speed_mode(selected_speed)
    game.reset_game_state()
    game.show_leaderboard = True
    return game, snake_skin, skin_names[skin_index]

def prompt_player_name_skin_music_voice_speed():
    # center_y = SCREEN_SIZE // 16  # Base anchor point
    center_y = LAYOUTS.welcome_margin_bottom
    SPACING = CELL_SIZE*2

    welcome_y = center_y
    name_y = welcome_y + SPACING 
    tourn_y = name_y + SPACING
    voice_y = tourn_y + SPACING
    speed_y = voice_y + SPACING
    skin_y  = speed_y + SPACING

    # Constants (top of file or nearby)
    SKIN_PREVIEW_SIZE = SCREEN_SIZE // 4

    # same as Game.eat_sound
    error_sound = pygame.mixer.Sound("assets/sounds/crunchybite.ogg")

    SAFE_CHARS = set(string.ascii_letters + string.digits + string.punctuation + " ")
    
    tournament_mode = False
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

        # Welcome Text
        welcom_text = "WELCOME TO PYTHON PORTALS"
        welcome_surf = FONTS.title_medium.render(welcom_text, True, BLACK)
        welcome_rect = welcome_surf.get_rect(center=(SCREEN_SIZE // 2, welcome_y))
        screen.blit(welcome_surf, welcome_rect)

        # Name Prompt
        name_label = "Name: " + name
        if cursor_visible:
            name_label += "_"
        name_surf = FONTS.title_medium.render(name_label, True, BLACK)
        name_rect = name_surf.get_rect(center=(SCREEN_SIZE // 2, name_y))
        screen.blit(name_surf, name_rect)

        tourn_text = f"Personal Leaderboard: {'On' if tournament_mode else 'Off'}"
        tourn_surf = FONTS.title_medium.render(tourn_text, True, BLACK)
        tourn_rect = tourn_surf.get_rect(center=(SCREEN_SIZE // 2, tourn_y))
        screen.blit(tourn_surf, tourn_rect)

        # Voice Label
        if voice_selected:
            voice_text = f"Voice: {voice_pack_names[selected_voice_index].capitalize()}"
        else:
            voice_text = "Voice: None (chomp only)"
     
        voice_surf = FONTS.title_medium.render(voice_text, True, BLACK)
        voice_rect = voice_surf.get_rect(center=(SCREEN_SIZE // 2, voice_y))
        screen.blit(voice_surf, voice_rect)
        
        # Speed Label
        speed_label_surf = FONTS.title_medium.render(f"Speed: {selected_speed}", True, BLACK)
        speed_label_rect = speed_label_surf.get_rect(center=(SCREEN_SIZE // 2, speed_y))
        screen.blit(speed_label_surf, speed_label_rect)
        
        # Skin Label
        skin_label_surf = FONTS.title_medium.render(f"Skin: {skin_names[skin_index]}", True, BLACK)
        skin_label_rect = skin_label_surf.get_rect(center=(SCREEN_SIZE // 2, skin_y))
        screen.blit(skin_label_surf, skin_label_rect)

        # Voice Instructions
        tab_surf = FONTS.body_medium.render("Select Voice with Tab/Shift+Tab", True, BLACK)
        tab_rect = tab_surf.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - LAYOUTS.welcome_margin_bottom*5))
        screen.blit(tab_surf, tab_rect)
        
        # Load and draw preview box
        skin_preview = load_image(skin_files[skin_index], 
                                size=(SKIN_PREVIEW_SIZE, SKIN_PREVIEW_SIZE), 
                                use_alpha=True)
        
        # Vertically center preview box between Skin Label above and Voice Instructions below
        skin_preview_x = (SCREEN_SIZE - SKIN_PREVIEW_SIZE) // 2
        skin_preview_y = (skin_label_rect.bottom + tab_rect.top) // 2
        screen.blit(skin_preview, (skin_preview_x, skin_preview_y - SKIN_PREVIEW_SIZE // 2))

        # Music Instructions
        ud_arrow_surf = FONTS.body_medium.render("Select Music with Up/Down Arrow", True, BLACK)
        ud_arrow_rect = ud_arrow_surf.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - LAYOUTS.welcome_margin_bottom*4))
        screen.blit(ud_arrow_surf, ud_arrow_rect)
        
        # Skin Instructions
        lr_arrow_surf = FONTS.body_medium.render("Select Skin with Left/Right Arrow", True, BLACK)
        lr_arrow_rect = lr_arrow_surf.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - LAYOUTS.welcome_margin_bottom*3))
        screen.blit(lr_arrow_surf, lr_arrow_rect)

        # Speed Instructions
        mouse_text = "Click Anywhere on Screen to Change Speed"
        mouse_surf = FONTS.body_medium.render(mouse_text, True, BLACK)
        mouse_rect = mouse_surf.get_rect(center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - LAYOUTS.welcome_margin_bottom*2))
        screen.blit(mouse_surf, mouse_rect)
        
        # Confirm All Instructions
        confirm_surf = FONTS.body_medium.render("Press ENTER to Confirm All", True, BLACK)
        confirm_rect = confirm_surf.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - LAYOUTS.welcome_margin_bottom))
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
                    return name, snake_skin, skin_index, selected_music_index, selected_voice_index, selected_speed, voice_enabled, tournament_mode
                
                elif event.key == pygame.K_F1:
                    tournament_mode = not tournament_mode

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

                    preview_folder = voice_pack_paths[selected_voice_index]
                    wav_files = sorted(glob.glob(os.path.join(preview_folder, "*.wav")))

                    if wav_files:
                        try:
                            pygame.mixer.Sound(wav_files[0]).play()
                        except pygame.error as e:
                            print_debug("UI", f"⚠️ Error playing preview: {wav_files[0]} → {e}")
                    else:
                        print_debug("UI", f"❌ No .wav files found in: {preview_folder}")

                elif event.unicode and event.unicode.isprintable():
                    if event.unicode in SAFE_CHARS:
                        if len(name) < 7: # check length *before* adding next character
                            name += event.unicode
                        else:
                            error_sound.play()
                    else:
                        error_sound.play()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):  # Left or right click
                selected_speed = "Fast" if selected_speed == "Slow" else "Slow"

def show_instructions_screen(game):
    title_y = SCREEN_SIZE // 14
    instructions_y = SCREEN_SIZE // 6
    prompt_y = SCREEN_SIZE + HUD_HEIGHT - (SCREEN_SIZE // 14)

    howto_lines = [
        "Use arrow keys to move your snake.",
        "Eat food to grow and score points.",
        "Protect your head from enemy snake contact.",
        "(Tip: they're afraid of the edges).",
        "Eat four foods for portal.",
        "Enter portal to advance to next level.",
        "Snake speed increases each level.",
        "Food value increases each level.",
        "Use cursor to click blue square bonuses.",
        "Game ends when snake hits wall or tail.",
        "Press P to pause and catch your breath.",
        f"Reach level {game.final_level} to achieve immortality.",
        "See you on the leaderboard!",
        "Made with Love by Julia and Ben, Co-Devs"
    ]

    while True:
        screen.fill(WHITE)

        # Title
        title = FONTS.title_large.render("How to Play Python Portals", True, BLACK)
        screen.blit(title, title.get_rect(center=(SCREEN_SIZE // 2, title_y)))

        # How-to Lines
        for i, line in enumerate(howto_lines):
            rendered = FONTS.body_small.render(line, True, BLACK)
            screen.blit(rendered, rendered.get_rect(center=(SCREEN_SIZE // 2, instructions_y + i * (SCREEN_SIZE // 16))))

        # Instructions
        prompt = FONTS.body_small.render("Press ENTER to Return to Leaderboard", True, BLACK)
        screen.blit(prompt, prompt.get_rect(center=(SCREEN_SIZE // 2, prompt_y)))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                return

# endregion UI & PLAYER SETUP


# region SNAKE CLASSES
# === SNAKE CLASSES ===

class Snake:
    
    def __init__(self, head_color, body_image):
        """Initialize the snake at the center of the screen with a single segment."""
        self.head_color = head_color
        self.body_image = body_image
        center = NUM_CELLS // 2
        self.body = [Vector2(center, center)]
        self.direction = Vector2(1, 0)
        # See docs "direction_vs_last_direction.md" for full explanation.
        self.last_direction = Vector2(self.direction.x, self.direction.y) 
        self.grow = False

    def move(self):
        """Updates the snake's position based on its current direction.
        If the snake should grow, a new segment is added without removing the tail.
        """
        new_head = to_cell(self.body[0]) + self.direction
        self.body.insert(0, new_head)
        if not self.grow:
            self.body.pop()
        else:
            self.grow = False
        self.last_direction = self.direction 

    def draw(self):
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

            if index == 0:
                draw_eyes(screen, px, py, self.direction)
    
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

class EnemySnake:
    def __init__(self, body, direction, head_color=None, body_color=None):
        self.body = body  # list of Vector2
        self.direction = Vector2(direction)
        self.facing_horizontally = (self.direction.y == 0)
        self._spawn_direction = Vector2(direction)  # Store original for debug
        self.head_color = head_color if head_color else HEAD_COLORS[8]
        self.body_color = body_color if body_color else load_image(skin_files[8], 
                                     size=(CELL_SIZE, CELL_SIZE), use_alpha=True)
        self.move_counter = 0
        self.move_threshold = 1

        print_debug("enemy", f"[INIT] EnemySnake initialized with direction: {direction}")
        
        # Computes initial direction by comparing head and second segment
        # Example: if head is (-1, 14) and next is (-2, 14), then direction is (1, 0)
        if self.direction is None:
            if len(body) >= 2:
                self.direction = (body[0] - body[1]).normalize() # normalize ensures direction vector is of length 1
            else:
                # Random initial direction (no movement into wall guaranteed yet)
                self.direction = random.choice(
                    [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]
                    )

    def move(self, player_body):
        new_head = to_cell(self.body[0]) + self.direction

        # Off-screen check - wall collision
        if new_head.x < 0 or new_head.x >= NUM_CELLS or new_head.y < 0 or new_head.y >= NUM_CELLS:
            print_debug("enemy", f"[DEATH] Enemy collided with wall at {new_head}. Player rewarded!")
            self._death_position = self.body[0]  # Save for Game to trigger smoke
            self.body = []  # Clear the body = effectively removed
            return True  # Return True to indicate player should be rewarded

        # Final safety guard against moving through player
        if new_head in player_body:
            print_debug("enemy", f"[TRAPPED] Enemy would hit player at {new_head}. Self-destructing.")
            self._death_position = self.body[0]
            self.body = []
            return
        
        self.body.insert(0, new_head)
        self.body.pop()

    def choose_safe_direction_if_needed(self, player_body):
        if not self.body:  # Add this guard check
            return
        
        head = to_cell(self.body[0])
        if self._is_next_move_onscreen(head.x, head.y, self.direction, margin=ENEMY_MARGIN):
            next_pos = head + self.direction
            if next_pos not in self.body and next_pos not in player_body:
                return

        # Allow newly spawned enemy snake to keep moving in spawn direction until it's past margin
        if not (ENEMY_MARGIN <= head.x < NUM_CELLS - ENEMY_MARGIN and 
                ENEMY_MARGIN <= head.y < NUM_CELLS - ENEMY_MARGIN):
            if self.direction == self._spawn_direction:  # Keep original direction while entering
                next_pos = head + self.direction
                if next_pos in player_body:
                    print_debug("enemy", f"Enemy hit player at {next_pos}. Player rewarded!")
                    self._death_position = head
                    self.body = []
                    return True # Player should be rewarded

            return # Safe to keep moving in spawn direction through safe zone

        # Try ALL possible directions systematically
        all_directions = [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]
        max_attempts = 5 # Try directions multiple times in different orders via .shuffle()

        for attempt in range(max_attempts):
            random.shuffle(all_directions) # Shuffle for each attempt to avoid patterns

            for dir in all_directions:
                if dir == -self.direction or self._is_turn_offscreen(head, dir):
                    continue

                next_pos = head + dir
                if (self._is_next_move_onscreen(head.x, head.y, dir, margin=ENEMY_MARGIN) and
                    next_pos not in self.body and # Avoid self-collision
                    next_pos not in player_body): # Avoid moving through player's body
                    self.direction = dir
                    self.facing_horizontally = (self.direction.y == 0)
                    return False # Valid move found

        # If we get here, enemy did not move legally - reward player
        print_debug("enemy", f"Enemy trapped at {head}. Player rewarded!")
        self._death_position = head
        self.body = []
        return True # Player should be rewarded
    
    def choose_new_direction_toward_player(self, player_head, player_body, margin=None):
        # Don't try to chase if we're already colliding
        if not self.body or self.body[0] in player_body:
            return False

        head = to_cell(self.body[0])
        dx = player_head.x - head.x
        dy = player_head.y - head.y

        options = []
        if abs(dx) >= abs(dy):
            options.append(Vector2(1, 0) if dx > 0 else Vector2(-1, 0))
            if dy != 0:
                options.append(Vector2(0, 1) if dy > 0 else Vector2(0, -1))
        else:
            options.append(Vector2(0, 1) if dy > 0 else Vector2(0, -1))
            if dx != 0:
                options.append(Vector2(1, 0) if dx > 0 else Vector2(-1, 0))

         # Add remaining non-180° directions as backup options
        all_directions = [Vector2(1,0), Vector2(-1,0), Vector2(0,1), Vector2(0,-1)]
        for dir in all_directions:
            if dir not in options and dir != -self.direction:
                options.append(dir)
        
        for dir in options:
            if self._is_turn_offscreen(head, dir):
                continue # Skip this direction and try the next one
            next_pos = head + dir
            if (dir != -self.direction and 
                self._is_next_move_onscreen(head.x, head.y, dir, margin=0) and
                next_pos not in self.body and # Avoid self-collision
                next_pos not in player_body): # Avoid moving through player's body
                self.direction = dir
                self.facing_horizontally = (self.direction.y == 0)
                return True # Found valid move

        return False # No valid moves found
        
    def update(self, target_length, player_body):
        if not self.body:
            return  # Snake is dead (e.g., went offscreen), skip update

        self.move_counter += 1
        if self.move_counter >= self.move_threshold:
            # Check if player is in safe zone (near edges)
            player_head = to_cell(player_body[0])
            is_player_safe = (player_head.x < ENEMY_MARGIN or 
                            player_head.x >= NUM_CELLS - ENEMY_MARGIN or 
                            player_head.y < ENEMY_MARGIN or 
                            player_head.y >= NUM_CELLS - ENEMY_MARGIN)
            
            # Always try to find a valid move, whether player is in safe zone or not
            found_valid_move = False
            if not is_player_safe:
                # Try to chase player if they're not in safe zone
                found_valid_move = self.choose_new_direction_toward_player(player_head, player_body, margin=ENEMY_MARGIN)

            # If we couldn't find a valid move toward player (or player is in safe zone),
            # try to find ANY valid move
            if not found_valid_move:
                result = self.choose_safe_direction_if_needed(player_body)
                if result is True:
                    return True  # Player should be rewarded - enemy trapped
            
            # Move the snake and check for wall collision
            wall_collision = self.move(player_body)
            if wall_collision:
                return True  # Player should be rewarded - enemy hit wall
            
            self.move_counter = 0

        # target_length = min(ENEMY_MAX_SIZE, target_length)

        # Only grow if we have at least one body segment
        if self.body:
            while len(self.body) < target_length:
                self.body.append(self.body[-1])
        
    def draw(self, surface):
        for i, segment in enumerate(self.body):
            px = segment.x * CELL_SIZE
            py = segment.y * CELL_SIZE + HUD_HEIGHT
            rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)

            if i == 0:
                pygame.draw.rect(surface, self.head_color, rect)
                draw_eyes(surface, px, py, self.direction)
                if self.facing_horizontally:
                    draw_crown(surface, px, py)
                elif self.direction == Vector2(0, 1):
                    draw_crown_base(surface, px, py, vertical_align="top")
                elif self.direction == Vector2(0, -1):
                    draw_crown_base(surface, px, py, vertical_align="bottom")

            else:
                surface.blit(self.body_color, (px, py))

            print_debug("enemy",f"Drawing {len(self.body)} segments at {[tuple(s) for s in self.body]}")

    @staticmethod
    def _generate_enemy_snake_offscreen(side, length):

        # Cap the enemy snake length at max size when spawning
        # capped_length = min(ENEMY_MAX_SIZE, length)

        direction_map = {
            "left": Vector2(1, 0),
            "right": Vector2(-1, 0),
            "top": Vector2(0, 1),
            "bottom": Vector2(0, -1),
        }
        max_attempts = 5  # Prevent infinite loop
        for attempt in range(max_attempts):

            direction = direction_map[side]

            if side in ("left", "right"):
                y = random.randint(0, NUM_CELLS - 1)
                x = -1 if side == "left" else NUM_CELLS
                head = Vector2(x, y)
            else:
                x = random.randint(0, NUM_CELLS - 1)
                y = -1 if side == "top" else NUM_CELLS
                head = Vector2(x, y)

            # Check if enemy will enter screen in ≤ 2 moves
            next_pos = head + direction
            next_next_pos = head + direction * 2
            enters_screen = any(0 <= p.x < NUM_CELLS and 0 <= p.y < NUM_CELLS
                                for p in (next_pos, next_next_pos))
            
            if not enters_screen:
                print_debug("enemy", f"Rejected spawn: won't enter screen from {side} in next two moves with direction {direction}.")

            else:
                print_debug("enemy", f"Accepted spawn: will enter screen from {side} in next two moves with direction {direction}.")

            if enters_screen:
                body = [head + (-i * direction) for i in range(length)]

                # Debug output
                print_debug("enemy", f"Enemy Head Position (offscreen): {head}")
                print_debug("enemy", f"Enemy Full Body: {[tuple(seg) for seg in body]}")

                return body, direction
            
            else:
                print_debug("enemy", "Spawned enemy won't enter screen. Retrying.")

            # Try again from a different side
            side = random.choice(["left", "right", "top", "bottom"])

        # Fallback
        print_debug("enemy", "Failed to spawn enemy snake after multiple attempts.")
        return None, None

    @staticmethod # does not depend on instance state; can be called without constructing an object.
    def _is_next_move_onscreen(x, y, direction, margin=0):
        """Predict the next move and decide whether moving in a given direction
        will keep enemy snake within screen bounds, including a safety margin if desired."""
        next_x = x + direction.x
        next_y = y + direction.y
        return (
            margin <= next_x < NUM_CELLS - margin and 
            margin <= next_y < NUM_CELLS - margin)
    
    @staticmethod
    def _is_turn_offscreen(head, dir):
        """Called when evaluating new turn options.
        Prevents turning into a wall when already at the edge.
        Used to block new directions if enemy snake is about to turn offscreen."""
        return (
            (head.x <= 0 and dir == Vector2(-1, 0)) or
            (head.x >= NUM_CELLS - 1 and dir == Vector2(1, 0)) or
            (head.y <= 0 and dir == Vector2(0, -1)) or
            (head.y >= NUM_CELLS - 1 and dir == Vector2(0, 1))
        )
    
# endregion SNAKE CLASSES


# region SNAKE CLASS HELPERS
# === SNAKE CLASS HELPERS ===

def draw_eyes(surface, head_x, head_y, direction):
    """
    Draws two eyes and their pupils on a snake head at pixel coords (head_x, head_y).
    direction is a Vector2 indicating movement.
    """

    left_eye_center = (
        int(head_x + EYE_OFFSET),
        int(head_y + CELL_SIZE - EYE_OFFSET) if direction.y == 1 else int(head_y + EYE_OFFSET)
    )

    right_eye_center = (
        int(head_x + CELL_SIZE - EYE_OFFSET),
        int(head_y + CELL_SIZE - EYE_OFFSET) if direction.y == 1 else int(head_y + EYE_OFFSET)
    )

    # Draw eyes
    pygame.draw.circle(surface, WHITE, left_eye_center, EYE_RADIUS)
    pygame.draw.circle(surface, WHITE, right_eye_center, EYE_RADIUS)

    # Calculate pupil direction based on snake's direction
    dir_x = int(direction.x * PUPIL_OFFSET)
    dir_y = int(direction.y * PUPIL_OFFSET)

    # Draw pupils
    left_eye_center = (left_eye_center[0] + dir_x, left_eye_center[1] + dir_y)
    right_eye_center = (right_eye_center[0] + dir_x, right_eye_center[1] + dir_y)
    
    pygame.draw.circle(surface, BLACK, left_eye_center, PUPIL_RADIUS)
    pygame.draw.circle(surface, BLACK, right_eye_center, PUPIL_RADIUS)

def draw_crown_base(surface, px, py, vertical_align="center"):
    """
    Draw just the crown base rectangle (no spikes).
    - `px`, `py` is top-left coordinate of the snake head.
    - `vertical_align`: 'top', 'bottom', or 'center' of the head.
    """
    base_width_factor = 1.0 # Multiplier of CELL_SIZE
    base_height = int(CELL_SIZE * 1/5) # Vertical height of crown base (in pixels)
    crown_width = int(CELL_SIZE * base_width_factor)
    
    # centers crowns on head: if crown_width == CELL_SIZE, then crown_left_x = px
    crown_left_x = px - (crown_width - CELL_SIZE) // 2

    # Compute crown base vertical position
    if vertical_align == "top":
        base_top = py  # flush with top of head
        base_bottom = base_top + base_height
    elif vertical_align == "bottom":
        base_bottom = py + CELL_SIZE  # flush with bottom of head
        base_top = base_bottom - base_height
    else:
        raise ValueError("vertical_align must be 'top' or 'bottom'")

    base_rect = pygame.Rect(
        crown_left_x, base_top,
        crown_width, base_height
    )
    pygame.draw.rect(surface, GOLD, base_rect)

def draw_crown(surface, px, py):
    """Draw a gold crown above the snake's head at pixel coords (px, py)."""
    # === CONFIGURABLE VALUES ===
    base_width_factor = 1.0   # Multiplier of CELL_SIZE
    base_height = int(CELL_SIZE * 1/5) # Vertical height of crown base (in pixels)
    spike_height = int(CELL_SIZE * 1/3) # From Tip to top of crown base
    num_spikes = 3 # Number of spikes
    crown_width = int(CELL_SIZE * base_width_factor)
    # note: px, py is top left x, y coord of snake head
    crown_left_x = px - (crown_width - CELL_SIZE) // 2 # centers crowns on head: if crown_width == CELL_SIZE, then crown_x = px
    crown_base_bottom_y = py  # Aligns the bottom of the crown with the top of the snake head
    crown_base_top = crown_base_bottom_y - base_height
    crown_top_y = crown_base_bottom_y - spike_height # tip of each spike to top of crown base

    base_rect = pygame.Rect(
        crown_left_x, crown_base_top,
        crown_width, base_height
    )
    pygame.draw.rect(surface, GOLD, base_rect)

    spike_spacing = crown_width // num_spikes
    for i in range(num_spikes):
        left = crown_left_x + i * spike_spacing
        right = left + spike_spacing
        tip = ((left + right) // 2, crown_top_y)

        pygame.draw.polygon(surface, GOLD, [
            (left, crown_base_top),
            tip,
            (right, crown_base_top)
        ])

# endregion SNAKE CLASS HELPERS


# region GAME CLASS
# === GAME CLASS ===

# region INIT & RESET
# === INIT & RESET ===

class Game:
    """Main game class that manages game state, updates, and rendering."""
    
    FADE_FRAMES = 15  # Number of frames for level transition fade effect
    
    def __init__(self, player_name, head_color, music_folder, voice_folder, speed_mode, voice_enabled, tournament_mode=False):
        # Basic identity
        self.player_name = player_name
        self.head_color = head_color
        self.speed_mode = speed_mode
        self.voice_enabled = voice_enabled
        self.tournament_mode = tournament_mode
        self.mouse_bonus_unlock_ms = None

        #Enemy Snake-related
        self.enemy_snake = None  # will hold an EnemySnake instance or None
        self.enable_enemy_snake = True  # Toggle this off to disable enemy logic
        self.player_entry_side = None
        self.smoke_effects = []  # List of dicts: {"pos": Vector2, "timer": int, "initial": int}
        self.penalty_points = 0  # Track total penalty points

        # Visuals
        self.background_index = random.randint(0, len(backgrounds) - 1)
        self.background = backgrounds[self.background_index]
        self.popups = []

        # Audio
        self.eat_sound = pygame.mixer.Sound("assets/sounds/crunchybite.ogg")
        self.bonus_sound = pygame.mixer.Sound("assets/sounds/shimmerbonus.ogg")
        self.penalty_sound = pygame.mixer.Sound("assets/sounds/disappear.ogg")
        self.portal_sound = pygame.mixer.Sound("assets/sounds/nextlevel.ogg")
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
        self.bonus_points = 0

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

        #Enemy snake-related
        self.enemy_snake = None
        self.player_entry_side = None
        self.penalty_points = 0
        self.smoke_effects = []
        self.last_enemy_spawn_time = pygame.time.get_ticks() # Timestamp ("Now") of last enemy spawn

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
        self.bonus_points = 0
        self.last_bonus_spawn_time = pygame.time.get_ticks() # Timestamp ("Now") of last bonus spawn

        self.popups = []

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

# endregion INIT & RESET


# region FLOW
# === FLOW ===

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
        time_since_last_enemy = current_time - self.last_enemy_spawn_time
        
        if self.enable_enemy_snake and self.enemy_snake:
            player_head = to_cell(self.snake.body[0])
            result = self.enemy_snake.update(len(self.snake.body), self.snake.body)
            
            # Check if enemy snake died by hitting player or itself
            if result is True:  # Enemy died, reward player
                reward = self.level
                self.score += reward
                
                # Create reward popup
                if hasattr(self.enemy_snake, '_death_position'):
                    px = self.enemy_snake._death_position.x * CELL_SIZE
                    py = self.enemy_snake._death_position.y * CELL_SIZE + HUD_HEIGHT
                    self.popups.append({
                        "text": f"+{reward}",
                        "color": WHITE,
                        "position": (px + CELL_SIZE // 2, py + CELL_SIZE // 2),
                        "timer": EFFECT_LIFETIME_LONG
                    })
                    self.bonus_sound.play()  # Play reward sound effect
            
        self.check_player_enemy_collision() # Still check if player hit enemy

        # Check if the enemy snake has been removed from the game.
        if self.enemy_snake and not self.enemy_snake.body:
            if hasattr(self.enemy_snake, "_death_position"):
                self.smoke_effects.append({"pos": self.enemy_snake._death_position, 
                                            "timer": EFFECT_LIFETIME_LONG, 
                                            "initial": EFFECT_LIFETIME_LONG})

            print_debug("enemy", f"Enemy snake moved offscreen and died at {self.enemy_snake._death_position}.")
            self.enemy_snake = None

        if (self.enable_enemy_snake and
            (self.enemy_snake is None or not self.enemy_snake.body) and 
            time_since_last_enemy >= ENEMY_SPAWN_INTERVAL and
            not self.transitioning):
                
            print_debug("enemy", f"Enemy check triggered after {time_since_last_enemy} ms")
            self.last_enemy_spawn_time = current_time  # Reset timer

            random_roll_for_enemy = random.random()
            print_debug("enemy", f"Random roll for enemy: {random_roll_for_enemy:.3f}")

            if random_roll_for_enemy <= ENEMY_SPAWN_PROBABILITY:
                print_debug("enemy", f"[SPAWN PROBABILITY DEBUG] random_roll_for_enemy={random_roll_for_enemy:.3f} <= ENEMY_SPAWN_PROBABILITY={ENEMY_SPAWN_PROBABILITY}")
                print_debug("enemy", "Enemy will spawn.")
                available_sides = ["left", "right", "top", "bottom"]
                if self.player_entry_side in available_sides:
                    available_sides.remove(self.player_entry_side)
                spawn_side = random.choice(available_sides)
                print_debug("enemy", f"[SPAWN FILTER] player_entry_side={self.player_entry_side}, available_sides={available_sides}, chosen={spawn_side}")
                length = len(self.snake.body)
                enemy_body, direction = EnemySnake._generate_enemy_snake_offscreen(spawn_side, length)
                if enemy_body is not None and direction is not None:
                    self.enemy_snake = EnemySnake(enemy_body, direction)

                print_debug("enemy",
                            f"Spawned from {spawn_side} with length {len(enemy_body)} and direction {direction}")
                
                print_debug("enemy", 
                            f"[AFTER SPAWN] EnemySnake.direction = {self.enemy_snake.direction}")

            else:
                print_debug("enemy","Enemy spawn skipped.")

        if (
            not self.transitioning and
            not self.bonus_active and  # No existing bonus
            self.snake_speed_ms <= self.mouse_bonus_unlock_ms and
            time_since_last_bonus >= BONUS_SPAWN_INTERVAL):
            
            print_debug("bonus", f"Bonus check triggered after {time_since_last_bonus} ms")
            self.last_bonus_spawn_time = current_time  # Reset timer

            random_roll_for_bonus = random.random()
            print_debug("bonus", f"Random roll for bonus: {random_roll_for_bonus:.3f}")
            
            if random_roll_for_bonus <= BONUS_SPAWN_PROBABILITY:
                print_debug("bonus", "Bonus will spawn.")
                self.spawn_bonus()
            else:
                print_debug("bonus", "Bonus spawn skipped.")
    
        if self.bonus_active:
            self.bonus_timer -= 1
            if self.bonus_timer <= 0:
                self.bonus_active = False
                self.bonus_position = None
        
        hx, hy = get_snake_head_cell(self.snake)
        if not (0 <= hx < NUM_CELLS) or not (0 <= hy < NUM_CELLS):
            print_debug("snake", f"FATAL: Snake head moved out of bounds: {hx}, {hy}")

        if (not self.food_voice_channel.get_busy() 
            and self.food_voice_queue 
            and current_time >= self.voice_queue_ready_time
            and self.voice_enabled):
                food_name_key, next_sound = self.food_voice_queue.pop(0)

                # Temporarily reduce background music volume
                pygame.mixer.music.set_volume(0.50)

                self.food_voice_channel.play(next_sound)
                print_debug("food", f"Played: {food_name_key} from voice: {os.path.basename(self.voice_folder)}")

                # Schedule background volume restoration after food sound finishes
                food_sound_duration_ms = int(next_sound.get_length() * 1000)
                pygame.time.set_timer(RESTORE_VOLUME_AFTER_FOOD_SOUND, food_sound_duration_ms, loops=1)

    def game_over(self):
        if self.game_over_already_ran:
            return
        self.game_over_already_ran = True

        self.end_time = pygame.time.get_ticks()
        if self.score > 0:
            entry_timestamp = update_leaderboard(
                self.player_name, self.score, len(self.snake.body), self.level, 
                self.bonus_points, self.penalty_points, self.game_duration(),
                self.tournament_mode)
            self.highlight_entry_ts = entry_timestamp
            
            if self.tournament_mode and entry_timestamp:
                save_active_leaderboard(
                    self.player_name,
                    load_active_leaderboard(self.player_name, tournament_mode=True),
                    tournament_mode=True
                    )
        
        pygame.mixer.music.fadeout(500)
        print_debug("game_over", "Game Over - resetting everything")
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

    def start_level(self):
        """Initialize a new level after transition while preserving snake length."""
        pygame.mixer.music.fadeout(500) # Fade out over 0.5 seconds
        track_path = get_level_track_path(self.music_folder, self.level)
        print_debug("music", f"Now playing: {track_path}")
        pygame.mixer.music.load(track_path)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play(-1, fade_ms=1000)

        self.enemy_snake = None
        self.last_enemy_spawn_time = pygame.time.get_ticks()  # Optional, restart cooldown
        self.smoke_effects = []

        previous_index = self.background_index
        while (new_index := random.randint(0, len(backgrounds) - 1)) == previous_index:
            pass
        self.background_index = new_index

        self.background = backgrounds[self.background_index]
        
        snake_length = len(self.snake.body) # Store snake length before reset

        if self.level > 1 and self.last_portal_position and self.last_portal_side:
            x = self.last_portal_position.x
            y = self.last_portal_position.y

            if self.last_portal_side == "left":
                starting_pos = Vector2(NUM_CELLS - 1, y)  # enter from right
                direction = Vector2(-1, 0)
            elif self.last_portal_side == "right":
                starting_pos = Vector2(0, y)  # enter from left
                direction = Vector2(1, 0)
            elif self.last_portal_side == "top":
                starting_pos = Vector2(x, NUM_CELLS - 1)  # enter from bottom
                direction = Vector2(0, -1)
            elif self.last_portal_side == "bottom":
                starting_pos = Vector2(x, 0)  # enter from top
                direction = Vector2(0, 1)
            else:
                print_debug("portal", "Unexpected self.last_portal_side. Defaulting to center spawn.")
                starting_pos = Vector2(NUM_CELLS // 2, NUM_CELLS // 2)
                direction = Vector2(1, 0)
        else:
            starting_pos = Vector2(NUM_CELLS // 2, NUM_CELLS // 2)
            direction = Vector2(1, 0)

        if self.level > 1 and self.last_portal_side in ("left", "right", "top", "bottom"):
            portal_entry_map = {
            "left": "right",
            "right": "left",
            "top": "bottom",
            "bottom": "top"
            }
            self.player_entry_side = portal_entry_map.get(self.last_portal_side)
        else:
            self.player_entry_side = None

        self.snake = Snake(self.head_color, self.snake_body_image)
        self.snake.direction = direction
        self.snake.last_direction = direction
        self.snake.body = [starting_pos]
        portal_side = getattr(self, "last_portal_side", "N/A")
        print_debug("snake", f"Snake spawned at {starting_pos} facing {direction} (opposite '{portal_side}' wall).")

        # Build out the snake and enemysnake in lock step ie enemy snake length matched snake length
        for i in range(1, snake_length):
            segment_pos = starting_pos - direction * i
            self.snake.body.append(segment_pos)

        self.food_name, self.food_image = self.current_food()
        self.food = Food(self.snake.body, self.food_image)
        self.level_score = 0 
        self.points_to_portal = 4 * self.level
        self.food_point_value = self.level
        self.portal_open = False
        self.portal_position = None
        pygame.time.set_timer(TICK, self.snake_speed_ms)

    def show_victory(self):
        self.transitioning = False  # ensure level doesn’t accidentally start
        if self.victory_start_time is None:
            self.victory_start_time = pygame.time.get_ticks()
            self.victory_extra = 88
            self.score += self.victory_extra
            self.portal_sound.play()
            print_debug("game_over", f"Triggered victory screen at {self.victory_start_time}")
            return

        victory_y = SCREEN_SIZE // 4

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
            rendered = FONTS.body_large.render(line, True, BLACK)
            screen.blit(rendered, rendered.get_rect(center=(
                SCREEN_SIZE // 2, victory_y + i * (SCREEN_SIZE // 15)))
                )

        pygame.display.update()

        # After 15 seconds, go to leaderboard
        elapsed = pygame.time.get_ticks() - self.victory_start_time
        print_debug("game_over", f"Victory screen shown for {elapsed} ms")
        if elapsed >= 15000:
            self.game_over()
            self.show_victory_screen = False

# endregion FLOW


# region EVENTS
# === EVENTS ===
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
                print_debug("food", f"Queued: {food_name_key}") # debug

            print_debug("food", f"Ate: {self.food_name}")

            self.food_name, self.food_image = self.current_food()
            self.food = Food(self.snake.body, self.food_image)

            # Open portal when reaching required points in the current level
            if not self.portal_open and self.level_score >= self.points_to_portal:
                self.generate_random_portal()

    def current_food(self):
        """Return a random (food name, food image) pair."""
        index = random.randint(0, len(food_images) - 1)
        image = food_images[index]
        name = os.path.splitext(os.path.basename(valid_food_paths[index]))[0].lower()
        return name, image

    def check_collisions_and_portals(self):
        hx, hy = get_snake_head_cell(self.snake)
        head = to_cell(self.snake.body[0])

        if self.portal_open and head == self.portal_position:
            px, py = int(self.portal_position.x), int(self.portal_position.y)
            if (hx, hy) == (px, py):
                self.portal_sound.play()
                print_debug("portal", f"Portal entered at level {self.level}")
                print_debug("snake", f"Snake entered portal at {self.portal_position} on '{self.last_portal_side}' wall.")

            if self.level == self.final_level - 1:
                print_debug("game_over", f"Triggering victory screen for final_level={self.final_level}")
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

            self.popups = []

            return

        if head.x < 0 or head.x >= NUM_CELLS or head.y < 0 or head.y >= NUM_CELLS:
            print_debug("snake", f"Wall collision at {head} — triggering game over")
            if self.portal_open:
                print_debug("portal", f"Portal open at: {self.portal_position}")
            self.penalty_sound.play()
            self.game_over()

    def check_player_enemy_collision(self):
        if self.enable_enemy_snake and self.enemy_snake:
            player_head = self.snake.body[0]
            enemy_snake = self.enemy_snake.body
            
            # Check if any part of enemy snake hits player's head (enemy dies)
            for enemy_segment in enemy_snake:
                if enemy_segment.x == player_head.x and enemy_segment.y == player_head.y:
                    collision_location = enemy_segment
                    print_debug("enemy", f"Enemy snake died at {collision_location}.")
                    self.smoke_effects.append({"pos": collision_location, 
                                               "timer": EFFECT_LIFETIME_LONG, 
                                               "initial": EFFECT_LIFETIME_LONG})
                    penalty = self.level
                    self.score -= penalty
                    self.penalty_points += penalty
                    self.enemy_snake = None
                    px = enemy_segment.x * CELL_SIZE
                    py = enemy_segment.y * CELL_SIZE + HUD_HEIGHT
                    popup_pos = (px + CELL_SIZE // 2, py + CELL_SIZE // 2)

                    self.popups.append({
                        "text": f"-{self.level}",
                        "color": RED,
                        "position": popup_pos,
                        "timer": EFFECT_LIFETIME_LONG
                        })
                    
                    self.penalty_sound.play()
                    print_debug("enemy",f"Collision! Player penalized {self.level} points.")
                    break

    def check_tail(self):
        """Check if the snake has collided with itself."""
        hx, hy = get_snake_head_cell(self.snake)
        body_positions = {(segment.x, segment.y) for segment in self.snake.body[1:]} # set of tuples
        head_pos = (hx, hy)
        if head_pos in body_positions:
            self.penalty_sound.play()
            self.game_over()
        
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

            portal_position = Vector2(x, y)
            if portal_position != self.food.position:

                self.portal_position = portal_position # portal position in current level
                self.portal_open = True

                # Store portal metadata for use in next level spawn
                self.last_portal_position = portal_position # "saved copy" of most recent portal position 
                self.last_portal_side = wall

                print_debug("portal", f"\U0001f6aa Portal spawned at ({x}, {y})")
                break

            attempts += 1
            if attempts > 3:
                print_debug("portal", "⚠️ Did not find portal position not occupied by food after 3 tries (~1 in 72 million)")
                self.portal_position = portal_position # portal and food overlap
                self.portal_open = True
                self.last_portal_position = portal_position
                self.last_portal_side = wall
                break  

        if attempts > 0 and self.portal_open:
            print_debug("portal", f"🔁 Portal placement took {attempts} additional attempt{'s' if attempts != 1 else ''}")

# endregion EVENTS


# region DRAWING
# === DRAWING ===

    def draw_smoke_effects(self, surface):

        for effect in self.smoke_effects:
            
            # Convert grid coordinates to pixel coordinates
            px = effect["pos"].x * CELL_SIZE
            py = effect["pos"].y * CELL_SIZE + HUD_HEIGHT

            # How many frames left before smoke puff circle disappears
            initial = effect.get("initial")
            time_left = effect["timer"]
            shrink_factor = time_left / initial
            shrink_factor = max(0, min(1.0, shrink_factor))   # clamp to [0, 1]

            # Radius of the smoke puff circle (starts large, shrinks to 0)
            base_radius = CELL_SIZE * 5.0
            radius = int(base_radius * shrink_factor)
            radius = max(0, min(radius, int(base_radius)))

            # Alpha controls transparency of smoke puff circle
            # It’s the 4th value in an RGBA color tuple (Red, Green, Blue, Alpha)

            # Fades linearly: starting at 255 (fully opaque = completely visible);
            # ending at 0 (fully transparent = completely invisible)
            alpha = max(0, min(255, int(255 * shrink_factor))) # clamp btw 0 and 255 to be safe

            if radius > base_radius:
                print_debug("enemy", f"Radius too large! radius={radius}, base_radius={base_radius}")
                continue
            elif radius <= 0 or alpha == 0:
                continue

            # Create a transparent surface large enough to contain the full smoke puff circle
            surface_diameter = radius * 2
            
            # SRCALPHA enables per-pixel transparency for RGBA colors
            # A in RGBA controls transparency of each pixel
            smoke_surface = pygame.Surface((surface_diameter, surface_diameter), pygame.SRCALPHA)

            # Draw smoke puff circle on surface
            center = (radius, radius)
            
            # color = (SMOKE[0], SMOKE[1], SMOKE[2], alpha)  # Explicit RGBA tuple unpacking
            # color = (*SMOKE, alpha)
            color = Color(*SMOKE, alpha) # use pygame.Color for guaranteed safety

            try:
                pygame.draw.circle(smoke_surface, color, center, radius)

            except ValueError as e:
                print_debug("enemy", f"Color error with color={color}, radius={radius}, center={center}")
                raise e
            
            # Find center of smoke puff circle
            top_left_snake_head = (px, py)
            center_snake_head = (
                top_left_snake_head[0] + CELL_SIZE // 2, 
                top_left_snake_head[1] + CELL_SIZE // 2
                )
            top_left_smoke_puff_circle = (
                center_snake_head[0] - radius,
                center_snake_head[1] - radius
                )
            
            # Blit smoke puff circle to the main screen
            surface.blit(smoke_surface, top_left_smoke_puff_circle)

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
        if self.enable_enemy_snake and self.enemy_snake:
            self.enemy_snake.draw(screen)

        self.draw_smoke_effects(screen)

        if self.transitioning:
            message = FONTS.title_large.render(f"LEVEL {self.level}", True, WHITE)
            text_height = message.get_height()
            center_x = SCREEN_SIZE // 2
            center_y = (SCREEN_SIZE // 2) + HUD_HEIGHT - (text_height // 2)
            text_rect = message.get_rect(center=(center_x, center_y))
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
            # Dim the entire screen
            pause_overlay = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE + HUD_HEIGHT))
            pause_overlay.fill(BLACK)
            pause_overlay.set_alpha(256/4)
            screen.blit(pause_overlay, (0, 0))

            # Get screen dimensions
            screen_width, screen_height = screen.get_size()

            # Gameplay area (exclude HUD)
            gameplay_top = HUD_HEIGHT
            gameplay_height = screen_height - HUD_HEIGHT

            # Center X and gameplay center Y
            center_x = screen_width // 2
            center_y = gameplay_top + (gameplay_height // 2)

            # Render text
            pause_text = FONTS.body_large.render("PAUSED", True, WHITE)
            instruct_text = FONTS.body_large.render("PRESS P TO RESUME", True, WHITE)

            # Total height of the two lines
            pause_height = pause_text.get_height()
            instruct_height = instruct_text.get_height()
            total_height = pause_height + instruct_height
            
            # Top of the two-line block
            block_top = center_y - (total_height // 2)

            # First line
            pause_rect = pause_text.get_rect(midtop=(center_x, block_top))
            # Second line — immediately below first
            instruct_rect = instruct_text.get_rect(midtop=(center_x, block_top + pause_height))

            # Blit both
            screen.blit(pause_text, pause_rect)
            screen.blit(instruct_text, instruct_rect)

        if not self.paused and self.bonus_active and self.bonus_position:
            px = self.bonus_position.x * CELL_SIZE
            py = self.bonus_position.y * CELL_SIZE + HUD_HEIGHT
            bonus_rect = pygame.Rect(px, py, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(screen, (0, 0, 255), bonus_rect)

        for popup in self.popups[:]:  # Copy to avoid modifying list while iterating
        # if self.bonus_popup:
            if not self.paused: 
                color = popup.get("color", WHITE)
                popup_text = FONTS.label.render(popup["text"], True, color)
                popup_rect = popup_text.get_rect(center=popup["position"])
                screen.blit(popup_text, popup_rect)
                popup["timer"] -= 1
                if popup["timer"] <= 0:
                    self.popups.remove(popup)

            # Update smoke effect timers and remove finished ones
        for effect in self.smoke_effects:
            effect["timer"] -= 1
        self.smoke_effects = [e for e in self.smoke_effects if e["timer"] > 0]

    def draw_score(self):
        # Draw HUD background
        hud_bg = pygame.Rect(0, 0, SCREEN_SIZE, HUD_HEIGHT)
        pygame.draw.rect(screen, BLACK, hud_bg)

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

            label_surf = FONTS.body_small.render(label.upper(), True, WHITE)
            label_rect = label_surf.get_rect(center=(x_center, HUD_HEIGHT // 3))

            value_surf = FONTS.body_small.render(value, True, WHITE)
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

        # Draw Title
        if self.tournament_mode:
            title_text = FONTS.title_medium.render(f"{self.player_name}'s Top Scores", True, BLACK)
        else:
            title_text = FONTS.title_medium.render(f"Python Portals Leaderboard", True, BLACK)

        # Trophy emoji (Unicode: 🏆) is rendered on either side of the title for visual appeal
        trophy_unicode = "\U0001F3C6"
        trophy_emoji_surf, _ = FONTS.emoji.render(trophy_unicode, BLACK)

        # Calculate positions for the title and emojis to center them horizontally
        emoji_spacing = CELL_SIZE // 2
        emoji_width = trophy_emoji_surf.get_width()
        title_width = title_text.get_width()
        total_width = emoji_width + emoji_spacing + title_width + emoji_spacing + emoji_width
        
        # Center the row (emoji + title + emoji) horizontally on the screen
        row_start_x = SCREEN_SIZE // 2 - total_width // 2
        left_emoji_center_x = row_start_x + emoji_width // 2
        title_center_x = left_emoji_center_x + emoji_width // 2 + emoji_spacing + title_width // 2
        right_emoji_center_x = title_center_x + title_width // 2 + emoji_spacing + emoji_width // 2
        
        # Draw the title and emojis, centered on the screen
        left_emoji_rect = trophy_emoji_surf.get_rect(center=(left_emoji_center_x, TITLE_MARGIN_TOP))
        title_rect = title_text.get_rect(center=(title_center_x, TITLE_MARGIN_TOP))
        right_emoji_rect = trophy_emoji_surf.get_rect(center=(right_emoji_center_x, TITLE_MARGIN_TOP))
        screen.blit(trophy_emoji_surf, left_emoji_rect)
        screen.blit(title_text, title_rect)
        screen.blit(trophy_emoji_surf, right_emoji_rect)

        # Headers and row keys for the leaderboard table
        all_headers = ["Rank", "Name", "Pts", "Size", "Lvl", "Bns", "Pen", "Dur", "Date"]

        # Lambdas to extract data for each column from a leaderboard entry
        all_row_keys = [
            lambda idx, entry: f"{idx+1}",
            lambda idx, entry: entry["name"],
            lambda idx, entry: str(entry.get("score", 0)),
            lambda idx, entry: str(entry.get("size", "N/A")),
            lambda idx, entry: str(entry.get("level", "N/A")),
            lambda idx, entry: f"{int(100 * entry.get('bonus', 0) / entry.get('score', 1))}%",
            lambda idx, entry: f"{int(100 * entry.get('penalty', 0) / entry.get('score', 1))}%",
            lambda idx, entry: entry.get("duration", "N/A"),
            lambda idx, entry: entry.get("date", "N/A")[:5],
        ]
        
        # Exclude the "Name" column in tournament mode
        if self.tournament_mode:
            headers = [h for h in all_headers if h != "Name"]
            row_keys = [rk for h, rk in zip(all_headers, all_row_keys) if h != "Name"]
        else:
            headers = all_headers
            row_keys = all_row_keys

        # Calculate horizontal spacing between columns
        spacing = SCREEN_SIZE // len(headers)

        # Render each header and center it within its column
        for i, header in enumerate(headers):
            header_surf = FONTS.body_small.render(header, True, BLACK)
            header_rect = header_surf.get_rect(center=(spacing * i + spacing // 2, 
                                                       HEADER_MARGIN_TOP))
            screen.blit(header_surf, header_rect)


        # Load leaderboard data (global or player-specific, depending on mode)
        leaderboard = load_active_leaderboard(self.player_name, self.tournament_mode)
        entries_start_y = ENTRY_MARGIN_TOP

        # Render each leaderboard entry as a row
        for idx, entry in enumerate(leaderboard):
            row = [rk(idx, entry) for rk in row_keys]

            # Highlight the row if it matches the highlighted timestamp
            is_highlight = self.highlight_entry_ts and entry.get("ts") == self.highlight_entry_ts
            row_color = GOLD if is_highlight else WHITE

            # Calculate row position and dimensions
            row_height = FONTS.body_small.get_height()
            row_y = entries_start_y + idx * ENTRY_LINE_SPACING
            row_top = row_y - row_height // 2 

            # Draw the row background
            row_rect = pygame.Rect(0, row_top, SCREEN_SIZE, row_height)
            pygame.draw.rect(screen, row_color, row_rect)

            # Render each column in the row
            for i, item in enumerate(row):
                entry_surf = FONTS.body_small.render(item, True, BLACK)
                entry_rect = entry_surf.get_rect(center=(
                    spacing * i + spacing // 2,
                    entries_start_y + idx * ENTRY_LINE_SPACING
                ))
                screen.blit(entry_surf, entry_rect)
        
        # Render footer instructions at the bottom of the screen
        instructions_text = FONTS.body_small.render(
            "Press ENTER to Play,", True, BLACK)
        instructions_rect = instructions_text.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - INSTRUCTION_MARGIN_BOTTOM*2))
        screen.blit(instructions_text, instructions_rect)

        instructions_text_2 = FONTS.body_small.render(
            "H for How to Play, N for New Player", True, BLACK)
        instructions_rect_2 = instructions_text_2.get_rect(
            center=(SCREEN_SIZE // 2, SCREEN_SIZE + HUD_HEIGHT - INSTRUCTION_MARGIN_BOTTOM))
        screen.blit(instructions_text_2, instructions_rect_2)

# endregion DRAWING

# endregion GAME CLASS


# region INITIALIZATION & MAIN LOOP
# === INITIALIZATION & MAIN LOOP ===

def main():
    git_pull_leaderboard()
    game, snake_skin, chosen_skin_name = initialize_game_session()

    # Main game loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                print_debug("UI", f"Key pressed: {pygame.key.name(event.key)}")

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
                        player_name, snake_skin, skin_index, selected_music_index, selected_voice_index, selected_speed, voice_enabled, tournament_mode = prompt_player_name_skin_music_voice_speed()
                        
                        game.tournament_mode = tournament_mode
                        game.player_name = player_name
                        game.show_leaderboard = True

                        # Apply skin and player name
                        game.apply_player_name_and_skin(player_name, skin_index)
                        
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

                    elif event.key == pygame.K_u:
                        merged_count = merge_named_leaderboards()

                        # Fill screen with Yellow
                        flash_overlay = pygame.Surface((SCREEN_SIZE, SCREEN_SIZE + HUD_HEIGHT))
                        flash_overlay.fill(BLACK)

                        # Render centered message
                        message = FONTS.title_large.render("LEADERBOARD REFRESH", True, WHITE)
                        message_rect = message.get_rect(center=(SCREEN_SIZE // 2, (SCREEN_SIZE + HUD_HEIGHT) // 2))
                        flash_overlay.blit(message, message_rect)

                        # Blit overlay and update display
                        screen.blit(flash_overlay, (0, 0))
                        pygame.display.flip()
                        pygame.time.delay(1500)

                        # Redraw leaderboard
                        game.draw_leaderboard()
                        pygame.display.flip()

                        if merged_count == None:
                            print_debug("leaderboard", "No new entries to merge.")

                        else:
                            print_debug("leaderboard", f"Merged {merged_count} entries!")

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
                        print_debug("UI", f"Game {'paused' if game.paused else 'resumed'}")
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
                            print_debug("snake", "=== Snake Debug Dump ===")
                            for i, segment in enumerate(game.snake.body):
                                print_debug("snake", f"[{i}] {segment}")

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
                                bonus_points = game.level
                                game.score += bonus_points
                                game.bonus_points += bonus_points
                                game.bonus_sound.play()
                                print_debug("bonus", f"Bonus clicked: + {bonus_points}")
                                game.bonus_active = False
                                px = game.bonus_position.x * CELL_SIZE
                                py = game.bonus_position.y * CELL_SIZE + HUD_HEIGHT
                                
                                game.popups.append({
                                    "text": f"+{bonus_points}",
                                    "color": WHITE,
                                    "position": (px + CELL_SIZE // 2, py + CELL_SIZE // 2),
                                    "timer": EFFECT_LIFETIME_LONG
                                    })

        if game.show_victory_screen:
            game.show_victory()

            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    print_debug("UI", "Skipping to leaderboard early")
                    game.game_over()
                    game.show_victory_screen = False
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()

            continue

        game.draw()
        pygame.display.update()
        clock.tick(60)

# endregion GAME INITIALIZATION & MAIN LOOP


if __name__ == "__main__":
    main()