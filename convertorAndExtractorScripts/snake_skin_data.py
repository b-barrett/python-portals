HEAD_COLORS_EXPLICIT = [
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

HEAD_COLORS_COMPACT = [
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

ORIGINAL_NAMES = [
    "Redbrick",
    "Alligatorskin",
    "Cedar",
    "Leaf",
    "Leather",
    "Obsidian",
    "Pine",
    "Rustyiron",
    "Snakeskin",
    "Styrofoam",
    "Topaz",
    "Turquoise",
    "Whitemarble",
    "Yellowturquoise",
]

SKIN_NAMES = [
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
    "Corroscale",
]

# Combined mapping (index-matched)
SKIN_TO_COLOR_EXPLICIT = list(zip(SKIN_NAMES, ORIGINAL_NAMES))

print(SKIN_TO_COLOR_EXPLICIT)
