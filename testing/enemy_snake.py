import pygame
from pygame.math import Vector2
import random

pygame.init()
info = pygame.display.Info()
screen_width = info.current_w
screen_height = info.current_h
print(screen_width, screen_height)

CELL_SIZE = 30
NUM_CELLS = min(int(screen_width * 0.82) // CELL_SIZE, 
                int(screen_height * 0.82) // CELL_SIZE)
SCREEN_SIZE = CELL_SIZE * NUM_CELLS

HUD_HEIGHT = int(screen_height * 0.08)

print(NUM_CELLS)
print(SCREEN_SIZE)
print(HUD_HEIGHT)




#     if side in ("left", "right"):
#         y = random.randint(1, NUM_CELLS - 2)  # Avoid corners for fairness
#         x = -1 if side == "left" else NUM_CELLS
#         head = Vector2(x, y)
#     else:
#         x = random.randint(1, NUM_CELLS - 2)
#         y = -1 if side == "top" else NUM_CELLS
#         head = Vector2(x, y)

#     # Extend the body behind the head, still off-screen
#     body = [head + (-i * direction) for i in range(length)]
#     return body


def generate_enemy_snake_offscreen(side, length):
    """
    Generate an enemy snake off-screen on the given side, facing inward.
    
    Args:
        side (str): One of "left", "right", "top", "bottom"
        length (int): Total number of segments to generate (same as player snake)
    
    Returns:
        List[Vector2]: Full body of the enemy snake, starting just off-screen
    """

    # Defines direction enemy snake will move after spawning, 
    # depending on which side it spawns from.

    direction_map = {
        "left": Vector2(1, 0),
        "right": Vector2(-1, 0),
        "top": Vector2(0, 1),
        "bottom": Vector2(0, -1),
    }

    direction = direction_map[side]

    if side in ("left", "right"):
        y = random.randint(1, NUM_CELLS - 2)
        x = -1 if side == "left" else NUM_CELLS
        head = Vector2(x, y)
    else:
        x = random.randint(1, NUM_CELLS - 2)
        y = -1 if side == "top" else NUM_CELLS
        head = Vector2(x, y)

    body = [head + (-i * direction) for i in range(length)]
    print(body)

    # Debug output
    print(f"🟥 Enemy Snake Spawn Side: {side}")
    print(f"➡️  Direction: {direction}")
    print(f"👾 Head Position (offscreen): {head}")
    print(f"🐍 Full Body Segments: {[tuple(seg) for seg in body]}")

    return body

generate_enemy_snake_offscreen("left", 5)
