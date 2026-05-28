#!/bin/bash

# Target directory for skills
TARGET_DIR="$HOME/.gemini/jetski/skills"

# Get the absolute path of the script's directory
REPO_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "Installing skills from $REPO_DIR to $TARGET_DIR"

# Ensure target directory exists
mkdir -p "$TARGET_DIR"

# Find all directories containing SKILL.md
find "$REPO_DIR" -maxdepth 2 -name "SKILL.md" | while read -r skill_file; do
    skill_dir="$(dirname "$skill_file")"
    skill_name="$(basename "$skill_dir")"
    
    # Skip the repo root itself if it somehow matches
    if [ "$skill_dir" == "$REPO_DIR" ]; then
        continue
    fi
    
    target_link="$TARGET_DIR/$skill_name"
    
    echo "Processing $skill_name..."
    
    if [ -L "$target_link" ]; then
        echo "  Link already exists: $target_link"
        current_target=$(readlink "$target_link")
        if [ "$current_target" == "$skill_dir" ]; then
            echo "  Points to correct location. Skipping."
        else
            echo "  Points to $current_target. Updating link."
            ln -sfn "$skill_dir" "$target_link"
        fi
    elif [ -e "$target_link" ]; then
        echo "  Warning: $target_link exists and is not a symlink. Skipping."
    else
        echo "  Creating symlink: $target_link -> $skill_dir"
        ln -s "$skill_dir" "$target_link"
    fi
done

echo "Installation complete."
