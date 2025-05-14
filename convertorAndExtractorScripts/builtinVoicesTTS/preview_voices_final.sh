#!/bin/bash

# Preview selected macOS voices saying a sample phrase

echo "🔊 Previewing selected voices..."

voices=(
  "Bahh"
  "Carmit"
  "Cellos"
  "Daniel"
  "Flo"
  "Good"
  "Karen"
  "Organ"
  "Ralph"
  "Reed"
  "Rishi"
  "Rocko"
  "Whisper"
  "Wobble"
  "Zarvox"
)

for v in "${voices[@]}"; do
  echo -e "\nVoice: $v"
  say -v "$v" "apple pie egg plant chicken leg honeycomb pepperoni tomato wine"
done

echo -e "\n✅ Done!"

