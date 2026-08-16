---
name: llm-tools
description: Shared utility tools for LLM development workflows.
---

# LLM Development Tools

This folder contains shared utility tools for development workflows. As more tools are added, they will be documented here.

## Available Tools

### 1. `tpu_dev_sync.py`
A Python script to synchronize code between local Cloudtop and remote TPU VMs. It maps a project directory from `~/projects/` locally to `/mnt/pd_<username>/projects/` on the remote VM.

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
### 4. `add_collaborators.sh`
A Bash script to batch add or invite GitHub collaborators with write access (or custom permission roles) to a repository. Automatically detects CSV headers (e.g. `GitHub Handle`, `GitHub Account`, `GitHub Username`) and extracts the target column, or accepts plain handle lists/text. **Note**: Dry-run is active by default to prevent accidental invites; pass `--execute` or `-x` to execute.

**Usage**:
```bash
bash ~/.gemini/config/skills/llm_tools/scripts/add_collaborators.sh [options] [user1 user2 ...]
```
- `-x, --execute`: Perform actual GitHub API invitations (disables dry-run mode).
- `-r, --repo`: Target repository (default: `vllm-project/vllm-torchtpu`).
- `-p, --permission`: Permission level: `push` (write), `pull` (read), `maintain`, `admin`, `triage` (default: `push`).
- `-f, --file`: Input file (supports `.csv` with header columns, text files, or direct username lists).

### 5. `fetch_buildkite_pr.py`
A Python script to inspect failing Buildkite CI checks for a GitHub pull request, clean logs (stripping timestamps and ANSI colors), and download all failure logs & artifacts into `/tmp/<repo_name>/PR_<PR_NUM>/`.

**Usage**:
```bash
python3 ~/.gemini/config/skills/llm_tools/scripts/fetch_buildkite_pr.py <PR_NUMBER_OR_URL> [--repo ORG/REPO] [--no-artifacts]
```
- `<PR_NUMBER_OR_URL>`: PR number (e.g. `383`) or GitHub PR URL.
- `-r, --repo`: Target repo (default: inferred from current git repo or `vllm-project/vllm-torchtpu`).
- `--no-artifacts`: Skip downloading build artifacts (downloads logs only).
- `-o, --output-dir`: Custom output folder (defaults to `/tmp/<repo_name>/PR_<pr_num>`).

---

## General References

- [TPU VM Setup](references/tpu_vm_setup.md): General steps for setting up Docker and environment on a TPU VM.
- [GKE TPU Setup Guide](references/set_dev_env_using_gke.md): Reference guide to set up a GKE cluster with multi-TPU types and deploy/test workloads on GKE.
- [GitHub CLI Guide for PR Reviews](references/gh_cli_guide.md): Quick commands and JQ pattern references for accessing PR diffs, review comments, and status checks using GitHub CLI.
- [Buildkite CLI & API Debugging Guide](references/buildkite_debugging_guide.md): Workflows for headless credential setup, avoiding GraphQL complexity errors, and extracting job execution error logs via REST API.
- [Merged Developers Reference Data](references/merged_developers.csv): Consolidated reference dataset of internal developers and external contributors for vllm-torchtpu.


