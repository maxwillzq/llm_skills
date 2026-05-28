#!/bin/bash

# Usage Instructions:
#
# 1. Code Synchronization
#    This script keeps code in sync between the local Cloudtop development
#    environment and the remote TPU VM. It maps a project directory from
#    ~/projects/ locally to /mnt/pd/projects/ on the remote VM.
#
#    - Push Changes (Local -> Remote):
#      ./tpu_dev_sync.sh push [project_name]
#      Warning: This will delete files on the remote TPU VM that are not present locally.
#
#    - Pull Changes (Remote -> Local):
#      ./tpu_dev_sync.sh pull [project_name]
#      Warning: This will delete files on the local Cloudtop that are not present on the remote TPU VM.
#
#    - Bidirectional Sync:
#      ./tpu_dev_sync.sh both [project_name]
#      or simply:
#      ./tpu_dev_sync.sh
#
#    If project_name is omitted, it will try to infer it from the current directory
#    if it is under ~/projects/.
#
# 2. Remote Execution
#    To run tests or commands on the TPU VM, use SSH.
#    Example:
#      ssh ${USER}-tpu-v7 "cd /mnt/pd/projects/my-project && pytest tests/"

# How it works:
#
# This script uses `rsync` (remote sync) to handle file transfers. `rsync` is
# highly efficient because it uses a delta-transfer algorithm, breaking files
# down into chunks and only transferring the parts that have actually changed.
#
# Modes:
#
# - Push/Pull: Uses `rsync -avz --delete`. Aims to make the destination an
#   exact mirror of the source. Files on the destination that do not exist
#   on the source will be DELETED.
#
# - Bidirectional Sync (Safe Sync): Uses `rsync -avzu`.
#   1. Pushes files that are newer on local to remote.
#   2. Pulls files that are newer on remote to local.
#   Does not use `--delete`, so no files are removed.


# Configuration
USER_NAME=$(whoami)
REMOTE_HOST="${REMOTE_HOST:-${USER_NAME}-tpu-v7}"

ACTION=$1
PROJECT_NAME=$2

# Infer project name if not provided
if [[ -z "$PROJECT_NAME" ]]; then
    CURRENT_DIR=$(pwd)
    if [[ "$CURRENT_DIR" =~ ^/usr/local/google/home/[^/]+/projects/([^/]+) ]]; then
        PROJECT_NAME="${BASH_REMATCH[1]}"
        echo "Inferred project name: $PROJECT_NAME"
    fi
fi

if [[ -z "$PROJECT_NAME" ]]; then
    echo "ERROR: Project name not specified and could not be inferred from current directory."
    echo "Usage: $0 <action> <project_name>"
    exit 1
fi

LOCAL_DIR="/usr/local/google/home/${USER_NAME}/projects/${PROJECT_NAME}/"
REMOTE_DIR="/mnt/pd/projects/${PROJECT_NAME}/"

EXCLUDES=(
    "--exclude=__pycache__/"
    "--exclude=*.pyc"
    "--exclude=*.egg-info/"
    "--exclude=.venv/"
    "--exclude=.pytest_cache/"
    "--exclude=.ruff_cache/"
    "--exclude=.gemini/"
)

ensure_remote_dir() {
    echo "=== Ensuring Remote Directory Exists ==="
    ssh "$REMOTE_HOST" "mkdir -p $REMOTE_DIR"
}

push_changes() {
    ensure_remote_dir
    echo "=== Pushing Local -> Remote (Including Deletions) ==="
    if [[ -t 0 ]]; then
        read -p "Are you sure you want to push and delete files on remote? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 1
        fi
    fi
    echo "Syncing $PROJECT_NAME..."
    rsync -avz --delete --filter='P .git' "${EXCLUDES[@]}" "$LOCAL_DIR" "$REMOTE_HOST:$REMOTE_DIR"
}

pull_changes() {
    echo "=== Pulling Remote -> Local (Including Deletions) ==="
    if [[ -t 0 ]]; then
        read -p "Are you sure you want to pull and delete files locally? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 1
        fi
    fi
    echo "Syncing $PROJECT_NAME..."
    rsync -avz --delete --filter='P .git' "${EXCLUDES[@]}" "$REMOTE_HOST:$REMOTE_DIR" "$LOCAL_DIR"
}

safe_sync() {
    ensure_remote_dir
    echo "=== Safe Bidirectional Sync (NO Deletions) ==="
    echo "Pushing newer local edits for $PROJECT_NAME..."
    rsync -avzu "${EXCLUDES[@]}" "$LOCAL_DIR" "$REMOTE_HOST:$REMOTE_DIR"
    echo "Pulling newer remote edits for $PROJECT_NAME..."
    rsync -avzu "${EXCLUDES[@]}" "$REMOTE_HOST:$REMOTE_DIR" "$LOCAL_DIR"
}

case $ACTION in
    "push")
        push_changes
        ;;
    "pull")
        pull_changes
        ;;
    "both"|"")
        safe_sync
        ;;
    *)
        echo "Usage: $0 [push|pull|both]"
        exit 1
        ;;
esac

echo "=== Sync Complete ==="
