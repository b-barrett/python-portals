import glob
import os
import json

def merge_test_leaderboards(): # def merge_named_leaderboards():
    """Merge all named test leaderboards in the high-level testing directory."""
    test_folder = os.path.dirname(__file__) # folder = os.path.dirname(LEADERBOARD_FILE)
    all_jsons = glob.glob(os.path.join(test_folder, "*.json")) # test_folder -> folder

    merged = []
    merged_count = 0

    for path in all_jsons:
        filename = os.path.basename(path)
        if filename.lower() == "merged_test.json": # if filename == "leaderboard.json":
            continue
        print(f"[DEBUG] Merging: {filename}")
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
                            print(f"[WARN] Skipping malformed entry in {path}: {entry}")
        except Exception as e:
            print(f"[ERROR] Failed to read {path}: {e}")

    # Deduplicate and sort
    seen_ts = set()
    unique = []

    for entry in merged:
        if entry["ts"] not in seen_ts:
            seen_ts.add(entry["ts"])
            unique.append(entry)

    if not unique:
        print(f"[WARN] No valid leaderboard entries found — merge skipped.")
        return  # Just exit the function early without saving or pushing

    unique.sort(key=lambda x: (-x["score"], -x["size"], -x["level"],
                               int(-100 * x["bonus"] / x["score"]) if x["score"] > 0 else float("inf")))
    
    top_10 = unique[:10] # top_10 = unique[:MAX_LEADERBOARD_ENTRIES]

    output_path = os.path.join(test_folder, "merged_test.json") # output_path = os.path.join(folder, "leaderboard.json")

    with open(output_path, "w") as f:
        json.dump(top_10, f, indent=4)

    print(f"✅ Merged {len(unique)} unique entries from {merged_count} files → {output_path}")

    # git_push_leaderboard()

    # return len(unique)

if __name__ == "__main__": # remove
    merge_test_leaderboards() # remove