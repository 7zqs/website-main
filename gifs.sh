#!/usr/bin/env bash

JSON_FILE="pkmn.json"
GIF_DIR="static/gifs"

jq -r '.[] | "\(.dex)|\(.name)"' "$JSON_FILE" | while IFS="|" read -r dex name; do
    # pad dex to 3 digits (1 -> 001)
    dex_padded=$(printf "%03d" "$dex")

    # lowercase name
    name_lower=$(echo "$name" | tr '[:upper:]' '[:lower:]')

    old_file="$GIF_DIR/${dex_padded}.gif"
    new_file="$GIF_DIR/${name_lower}.gif"

    if [[ -f "$old_file" ]]; then
        mv "$old_file" "$new_file"
        echo "Renamed: ${dex_padded}.gif -> ${name_lower}.gif"
    else
        echo "Missing: ${old_file}"
    fi
done
