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

### 6. `lj` (`llm_jobs` Unified Developer CLI)
Unified CLI for Cloud TPU development, interactive Dev Pods, benchmark job orchestration, and hardware profiling on GKE & GCE.

All authoritative and comprehensive documentation is maintained directly in [`llm_jobs/docs/`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/docs/):
- **Fast ML Developer Loop**: [`01_fast_ml_workflow.md`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/docs/01_fast_ml_workflow.md)
- **TPU Performance & Trace Playbook**: [`02_perf_optimization_guide.md`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/docs/02_perf_optimization_guide.md)
- **CLI & Parameter Reference**: [`03_cli_complete_reference.md`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/docs/03_cli_complete_reference.md)
- **Experiment Artifacts Specification**: [`04_experiment_artifacts.md`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/docs/04_experiment_artifacts.md)

### 7. `audit_repo_governance.py`
A Python automation tool to audit GitHub pull requests and repository governance compliance (DCO sign-off checks, label taxonomy, reviewer assignments, and approval verification).

**Usage**:
```bash
python3 ~/.gemini/config/skills/llm_tools/scripts/audit_repo_governance.py --repo <owner>/<repo> [--pr <PR_NUMBER>]
```

### 8. `lj pr sync` (Mandatory PR Source Packaging Standard)
When updating, uploading, or syncing `vllm-torchtpu` (or other repo) PR source code to GCS for remote CDK jobs, benchmark workloads, or cluster execution:
- **ALWAYS use `lj pr sync <pr_number>`**.
- **NEVER manually run `git archive` or `gcloud storage cp`** with custom tar prefixes.

**Usage**:
```bash
# Package and sync local vllm-torchtpu branch for PR to GCS (Always Overwrites)
lj pr sync <pr_number>
```
* **GCS Target**: `gs://llm-jobs-runs/repos/vllm-torchtpu/prs/pr<pr_number>.tar.gz`
* **Guarantees**: Standard root-level flat archive (no nested prefix bugs), strict git-ref validation, and automated GCS overwrite.

### 9. `export_markdown_to_gdoc.py`
A Python utility to extract all Mermaid diagrams from a Markdown document, render them into high-resolution PNGs via Kroki, save them to a local `images/` directory, and generate a `*_for_gdocs.md` file with explicit visual anchor placeholders ready for `codemind:create_document`.

**Usage**:
```bash
python3 ~/.gemini/config/skills/llm_tools/scripts/export_markdown_to_gdoc.py <path_to_markdown_file> [--img-dir <dir>] [--output-md <file>]
```

---

## CDK Local-Only Policy & Confidentiality Rule

> [!IMPORTANT]
> **Strict Local-Only Policy for Cloud DevKit (CDK) Changes**:
> - **NEVER commit or push CDK recipes, configurations, or workflow changes to remote repositories** (`cloud-devkit`).
> - All CDK experiments, JobSet YAML files, recipes, and benchmarking scripts must remain **strictly within the local repository** (e.g. `cloud-devkit/recipes/experimental/johnqiangzhang/`).
> - Submit jobs directly from the local file path using `cdk job submit <local_recipe.yaml>`.
> - Do not share or push proprietary recipes/configs to prevent unauthorized copying.

---

## General References

### Infrastructure & Cloud TPU Environment
- [TPU VM Setup](references/tpu_vm_setup.md): General steps for setting up Docker and environment on a TPU VM.
- [Docker Data Directory Migration](references/docker_migration.md): Moving Docker data root (`/var/lib/docker`) to persistent disk (`/mnt/pd_<username>/docker`) on Cloud TPU VMs.
- [Managing GCS Checkpoint Buckets](references/managing_checkpoint_bucket.md): Managing, syncing, and organizing model weights in GCS buckets.
- [GKE TPU Setup Guide](references/set_dev_env_using_gke.md): Reference guide to set up a GKE cluster with multi-TPU types and deploy/test workloads on GKE.

### GitHub, Code Review & Governance
- [Disciplined Engineering & Problem Solving](references/collaborative_problem_solving.md): Action tier matrix (Tier 1/2/3), blast radius control, and disciplined debugging loop.
- [Karpathy LLM Coding Guidelines](references/karpathy_guidelines.md): Behavioral guidelines to reduce LLM pitfalls (Simplicity First, Surgical Changes, Goal-Driven Loops).
- [GitHub CLI Guide & PR Commit Standards](references/gh_and_git_guide.md): Commands for accessing PR diffs, review comments, commit organization principles, and conventional commit message templates.
- [PR Code Review Checklist](references/code_review_checklist.md): Standard criteria and severity markers (🔴 Blocker, 🟡 Important, 🟢 Nit) for structured code reviews.
- [Pre-Public Development Guide (`vllm-torchtpu`)](file:///usr/local/google/home/johnqiangzhang/projects/vllm-torchtpu/docs/PRE_PUBLIC_DEV_GUIDE.md): Binding developer workflow, DCO sign-offs, reviewer assignments, and guarded merge SOP for the pre-public phase.
- [General Contribution Guide (`vllm-torchtpu`)](file:///usr/local/google/home/johnqiangzhang/projects/vllm-torchtpu/CONTRIBUTING.md): Core contribution guidelines, pre-commit formatting, directory layout, and testing standards.
- [Merged Developers Reference Data](references/merged_developers.csv): Consolidated reference dataset of internal developers and external contributors.

### Profiling & CI Debugging
- [CDK Job & Tracegen Debugging Guide](references/cdk_debugging_guide.md): Cloud DevKit (CDK) log inspection, Perfetto trace analysis, and custom trace instrumentation.
- [`lj` (`llm_jobs`) Documentation Index](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/docs/): Fast ML workflows, TPU performance playbooks, CLI reference, and experiment artifacts.
- [Buildkite CLI & API Debugging Guide](references/buildkite_debugging_guide.md): Headless credential setup, avoiding GraphQL errors, and extracting job logs.

### Technical Writing & Design Documentation
- [Design Documents & Technical Reports Style Guide](references/design_docs_and_reports_style_guide.md): Standards for engineering design docs, RFCs, and technical reports. Strictly prohibits emojis and marketing fluff; enforces objective, data-driven, and concise engineering prose.
- [Creating Google Docs from Markdown with Diagrams](references/create_google_doc_from_markdown.md): Standard operating procedure (SOP) to export Markdown with Mermaid diagrams to Google Docs. Automatically extracts and renders Mermaid diagrams to local PNGs, injects visual anchors, generates a native Google Doc via `codemind:create_document`, and guides the user to drag-and-drop the images. **Trigger when user asks to "create google doc based on my markdown"**.






