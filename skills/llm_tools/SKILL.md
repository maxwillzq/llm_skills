---
name: llm-tools
description: Shared utility tools for LLM development workflows.
---

# LLM Development Tools

This folder contains shared utility tools for development workflows. As more tools are added, they will be documented here.

## Available Tools

### 1. `tpu_dev_sync.py`
A Python script to synchronize code between local Cloudtop and remote TPU VMs. It maps a project directory from `~/projects/` locally to `/mnt/pd/projects/` on the remote VM.

**Usage**:
```bash
python3 ~/.gemini/config/skills/llm_tools/scripts/tpu_dev_sync.py [push|pull|both] [project_name]
```
- **`push`**: Local -> Remote (Warning: deletes files on remote not present locally).
- **`pull`**: Remote -> Local (Warning: deletes files on local not present on remote).
- **`both`**: Safe bidirectional sync (NO deletions, default).

If `project_name` is omitted, it will try to infer it from the current directory if it is under `~/projects/`.

### 2. `flatten_gcs_checkpoints.py`
A Python script to flatten HuggingFace model checkpoint cache folders in GCS buckets to prevent space duplication. It copies snapshots directly to the model root (resolving symlinks to blobs if they are stored as text pointer files) and deletes redundant `blobs/`, `snapshots/`, `refs/`, and `.no_exist/` subdirectories.

**Usage**:
```bash
python3 ~/.gemini/config/skills/llm_tools/scripts/flatten_gcs_checkpoints.py <bucket_name>
```

---

## General References

- [TPU VM Setup](references/tpu_vm_setup.md): General steps for setting up Docker and environment on a TPU VM.
- [GitHub CLI Guide for PR Reviews](references/gh_cli_guide.md): Quick commands and JQ pattern references for accessing PR diffs, review comments, and status checks using GitHub CLI.
