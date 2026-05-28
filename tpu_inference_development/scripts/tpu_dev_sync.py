#!/usr/bin/env python3
import argparse
import getpass
import os
import re
import subprocess
import sys

def get_inferred_project_name():
    cwd = os.getcwd()
    # Match /usr/local/google/home/<user>/projects/<project_name>
    match = re.match(r"^/usr/local/google/home/[^/]+/projects/([^/]+)", cwd)
    if match:
        return match.group(1)
    return None

def ensure_remote_dir(remote_host, remote_dir):
    print("=== Ensuring Remote Directory Exists ===")
    try:
        subprocess.run(["ssh", remote_host, f"mkdir -p {remote_dir}"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error ensuring remote directory: {e}")
        sys.exit(1)

def confirm_action(prompt):
    if sys.stdin.isatty():
        response = input(prompt + " (y/N) ").strip().lower()
        return response == 'y'
    return True # Assume yes if non-interactive

def run_rsync(args):
    try:
        subprocess.run(["rsync"] + args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running rsync: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Sync code between local and remote TPU VM.")
    parser.add_argument("action", choices=["push", "pull", "both", ""], nargs="?", default="both",
                        help="Action to perform: push, pull, or both (default)")
    parser.add_argument("project_name", nargs="?", default=None,
                        help="Name of the project in ~/projects/")
    
    args = parser.parse_args()
    
    user_name = getpass.getuser()
    remote_host = os.environ.get("REMOTE_HOST", f"{user_name}-tpu-v7")
    
    project_name = args.project_name
    if not project_name:
        project_name = get_inferred_project_name()
        if project_name:
            print(f"Inferred project name: {project_name}")
            
    if not project_name:
        print("ERROR: Project name not specified and could not be inferred from current directory.")
        print(f"Usage: {sys.argv[0]} [push|pull|both] <project_name>")
        sys.exit(1)
        
    local_dir = f"/usr/local/google/home/{user_name}/projects/{project_name}/"
    remote_dir = f"/mnt/pd/projects/{project_name}/"
    
    excludes = [
        "--exclude=__pycache__/",
        "--exclude=*.pyc",
        "--exclude=*.egg-info/",
        "--exclude=.venv/",
        "--exclude=.pytest_cache/",
        "--exclude=.ruff_cache/",
        "--exclude=.gemini/",
    ]
    
    if args.action == "push":
        ensure_remote_dir(remote_host, remote_dir)
        print("=== Pushing Local -> Remote (Including Deletions) ===")
        if not confirm_action("Are you sure you want to push and delete files on remote?"):
            print("Aborted.")
            sys.exit(1)
        print(f"Syncing {project_name}...")
        rsync_args = ["-avz", "--delete", "--filter=P .git"] + excludes + [local_dir, f"{remote_host}:{remote_dir}"]
        run_rsync(rsync_args)
        
    elif args.action == "pull":
        print("=== Pulling Remote -> Local (Including Deletions) ===")
        if not confirm_action("Are you sure you want to pull and delete files locally?"):
            print("Aborted.")
            sys.exit(1)
        print(f"Syncing {project_name}...")
        rsync_args = ["-avz", "--delete", "--filter=P .git"] + excludes + [f"{remote_host}:{remote_dir}", local_dir]
        run_rsync(rsync_args)
        
    elif args.action == "both" or args.action == "":
        ensure_remote_dir(remote_host, remote_dir)
        print("=== Safe Bidirectional Sync (NO Deletions) ===")
        print(f"Pushing newer local edits for {project_name}...")
        rsync_args_push = ["-avzu"] + excludes + [local_dir, f"{remote_host}:{remote_dir}"]
        run_rsync(rsync_args_push)
        
        print(f"Pulling newer remote edits for {project_name}...")
        rsync_args_pull = ["-avzu"] + excludes + [f"{remote_host}:{remote_dir}", local_dir]
        run_rsync(rsync_args_pull)
        
    print("=== Sync Complete ===")

if __name__ == "__main__":
    main()
