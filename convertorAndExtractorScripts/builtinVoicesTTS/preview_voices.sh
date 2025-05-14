#!/bin/bash

# Preview all unique macOS voices saying "apple pie egg plant honeycomb pepperoni tomato wine"
# Skips duplicates and prints voice names before speaking

echo "🔁 Previewing all unique voices..."

for v in $(say -v "?" | awk '{print $1}' | sort -u); do
  echo -e "\nVoice: $v"
  say -v "$v" "apple pie egg plant chicken leg honeycomb pepperoni tomato wine"
done

echo -e "\n✅ Done!"

