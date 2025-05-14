#!/bin/bash

# Preview all Yummy WAV files
CLIP_DIR="assets/sounds/yummy_clips"

echo "🔁 Previewing all WAV clips in $CLIP_DIR"

for f in "$CLIP_DIR"/*.wav; do
  filename=$(basename "$f")
  echo -e "\n🔊 Playing: $filename"
  afplay "$f"
done

echo -e "\n✅ Done!"

