def extract_fruit_index(path):
    """Extract the fruit index from a file path."""
    match = re.search(r"fruit_(\d+)\.png$", os.path.basename(path))
    return int(match.group(1)) if match else None
