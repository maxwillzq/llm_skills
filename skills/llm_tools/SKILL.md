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

### 3. `find_idle_tpu.sh`
A Bash script (using `gbash`) to search for and list idle Cloud TPU VM resources across multiple Google Cloud projects. It checks if `libtpu.so` is mapped by any running processes on the VM, determines connection health (SSH/Timeout status), and reports last login info in CSV format.

**Usage**:
```bash
bash ~/.gemini/config/skills/llm_tools/scripts/find_idle_tpu.sh --projects="tpu-prod-env-one-vm,cloud-tpu-inference-test" --user="<ssh_username>"
```
- `--projects`: Comma-separated list of GCP Projects to scan.
- `--user`: SSH username (defaults to `<whoami>_google_com`).
- `--shared`: Filter by shared label `true/false` (defaults to `false`).
- `--list_all`: List all idle TPUs instead of stopping at the first one (defaults to `true`).

---

## General References

- [TPU VM Setup](references/tpu_vm_setup.md): General steps for setting up Docker and environment on a TPU VM.
- [GKE TPU Setup Guide](references/set_dev_env_using_gke.md): Reference guide to set up a GKE cluster with multi-TPU types and deploy/test workloads on GKE.
- [GitHub CLI Guide for PR Reviews](references/gh_cli_guide.md): Quick commands and JQ pattern references for accessing PR diffs, review comments, and status checks using GitHub CLI.

