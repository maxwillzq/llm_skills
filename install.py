#!/usr/bin/env python3
import os
from pathlib import Path

def main():
    # Target directory for skills
    home = Path.home()
    target_dir = home / ".gemini" / "config" / "skills"
    
    # Get the absolute path of the script's directory
    repo_dir = Path(__file__).resolve().parent
    
    print(f"Installing skills from {repo_dir} to {target_dir}")
    
    # Ensure target directory exists
    target_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all directories containing SKILL.md
    patterns = ["skills/*/SKILL.md"]
    for pattern in patterns:
        for skill_file in repo_dir.glob(pattern):
            skill_dir = skill_file.parent
            skill_name = skill_dir.name
            
            target_link = target_dir / skill_name
            
            print(f"Processing {skill_name}...")
            
            if target_link.is_symlink():
                print(f"  Link already exists: {target_link}")
                current_target = target_link.resolve()
                if current_target == skill_dir:
                    print("  Points to correct location. Skipping.")
                else:
                    print(f"  Points to {current_target}. Updating link.")
                    target_link.unlink()
                    target_link.symlink_to(skill_dir)
            elif target_link.exists():
                print(f"  Warning: {target_link} exists and is not a symlink. Skipping.")
            else:
                print(f"  Creating symlink: {target_link} -> {skill_dir}")
                target_link.symlink_to(skill_dir)
            
    print("Installation complete.")

if __name__ == "__main__":
    main()
