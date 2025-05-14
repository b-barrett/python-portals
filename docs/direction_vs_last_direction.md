# Direction vs Last Direction

## Preventing Instant Reverse Crashes (Direction Guard)

This logic prevents the snake from instantly reversing direction and crashing into itself, even if the player presses keys in **rapid succession** between movement ticks.

**Example**:  
If the snake is moving **RIGHT**, and the player quickly presses **UP** then **LEFT**,  
- `UP` is accepted as a temporary change to `direction`,  
- but `LEFT` is **rejected**, because it would instantly reverse the last true movement (`RIGHT`).

---

### Key Distinctions

- `direction` updates **immediately** when input is allowed (before movement).
- `last_direction` updates **only after** a movement tick, when the snake has actually moved.
- A **tick** occurs every `snake_speed_ms` milliseconds (e.g., 150ms), *not* every frame.
- **FPS** (frames per second) affects how often the screen redraws — it does **not** control movement logic.
- IOW: FPS has nothing to do with snake crashing in above UP-then-LEFT scenario
- IOW: FPS affects visual smoothness only — not movement logic.

---

### Why It Works

By comparing player input to `last_direction` instead of `direction`, we ensure that only valid direction changes are allowed. This eliminates edge cases like:

> "I turned UP then LEFT quickly... why did I die?"

Because **LEFT** would reverse the last move (`RIGHT`), even though `direction` was briefly `UP`.

