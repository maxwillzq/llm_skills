---
name: vllm-torchtpu-development
description: >-
  Develops and tests vllm-torchtpu on TPU VMs. Use when setting up the Python environment on a TPU VM, running verification tests like offline inference, or mocking HuggingFace downloads in the test environment to use GCS instead.
---

# Developing vllm-torchtpu on TPU

use "ssh johnqiangzhang-tpu-v7" or alias "tpu-vm-ssh" to ssh login to tpu.
use "python3 ~/.gemini/config/skills/llm_tools/scripts/tpu_dev_sync.py" to push and sync vllm-torchtpu folder between cloudtop "~/projects/vllm-torchtpu"  and 
tpu VM "/mnt/pd_<username>/projects/vllm-torchtpu".

## Local Environment Setup (Cloudtop)

For IDE support and pre-commit hooks on your Cloudtop:
```bash
cd ~/projects/vllm-torchtpu
uv venv
source .venv/bin/activate
uv pip install --no-config --index-url https://pypi.org/simple pre-commit pytest
pre-commit install
```

## Environment Setup

We use Docker for development to ensure a consistent environment and easy dependency management. The Dockerfile supports multi-stage builds, allowing you to target a `dev` environment for editable mode.

If docker image is already there, you can skip rebuild.

### 1. Get Docker Image

use "ssh johnqiangzhang-tpu-v7" or alias "tpu-vm-ssh" to ssh login to TPU VM first.
You can pull the pre-built dev image instead of building it locally:

On your **TPU VM**:
```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
docker pull us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest
```


> [!TIP]
> **Docker Disk Space**: Building Docker images can consume a lot of space on the root partition (`/`). If you need to migrate the Docker data directory to the larger `/mnt/pd_<username>` disk, see the [Docker Migration Guide](references/docker_migration.md).





### 2. Run Container

> [!TIP]
> **Verifying Disk Mounts**: On some TPU VMs, a plain `df -h` command may not display the `/mnt/pd_<username>` persistent disk due to mount namespace isolation. 
> **Always use `lsblk`** as the source of truth to verify all attached block devices and their active mount points before assuming a disk is missing or unmounted.

Mount your local code directory for real-time sync and persistent HuggingFace cache if not:
```bash
docker run -it --privileged --net=host --shm-size=16g \
  -v /mnt/pd_<username>/.cache/huggingface:/root/.cache/huggingface \
  -v /mnt/pd_<username>/projects/vllm-torchtpu:/root/tpu_inference \
  -v /dev/vfio:/dev/vfio \
  -e HF_HOME=/root/.cache/huggingface \
  us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest
```

## Code Synchronization and Remote Execution

Refer to the `vllm-on-tpu` skill for detailed instructions on how to use TPU VMs and synchronize code using the `python3 ~/.gemini/config/skills/llm_tools/scripts/tpu_dev_sync.py` script.

### Source Code Location
*   **Local Cloudtop**: `~/projects/vllm-torchtpu`
*   **Remote TPU VM**: `/mnt/pd_<username>/projects/vllm-torchtpu`

### Usage Summary
*   **Syncing Code**: Use the `python3 ~/.gemini/config/skills/llm_tools/scripts/tpu_dev_sync.py` script as described in the `vllm-on-tpu` skill to push local changes from Cloudtop to the remote TPU VM.
*   **Remote Execution**: Use `ssh` (or the `tpu-vm-ssh` alias) to run tests and examples on the TPU VM.

## Local Reproduction and CI Debugging

If the user explicitly requests you to locally reproduce a GitHub Actions (CI/CD) workflow failure, or when you are asked to debug or validate PR Guard / Nightly runs on a development TPU VM:
- Refer to the [Local Reproduction and Debugging](references/local_reproduction.md) reference guide for template commands and concrete examples of pulling the dev container, mounting local caches, and running evaluation benchmarks or unit tests.

## Pull Request Code Reviews

When the user explicitly requests you to review a GitHub Pull Request (e.g., "Please review PR #123" or "Perform a code review of my branch"):
1.  **Retrieve PR Data**: Use the [GitHub CLI Guide for PR Reviews](../llm_tools/references/gh_cli_guide.md) to query the PR's details, diff, files changed, and comments.
2.  **Evaluate against Checklist**: Systematically review the diff and changes against the [Code Review Checklist](references/code_review_checklist.md).
3.  **Construct & Present Report**: Create a structured markdown review report categorizing your findings using the specified severity markers (🔴 Blocker, 🟡 Important, 🟢 Nit, 💡 Suggestion, ❓ Question, ✅ Praise) and present it to the user in the chat. **Do not submit anything to GitHub at this stage.**
4.  **Prompt for Confirmation**: After presenting the report, explicitly ask the user: "Would you like me to submit these review comments/ratings directly to the GitHub PR?"
5.  **Submit Comments**: Only if the user explicitly confirms, use the `gh` CLI commands in [gh_cli_guide.md](../llm_tools/references/gh_cli_guide.md) to post the inline reviews or general comments directly to the pull request on GitHub.

## Developer Workflow & Code Governance

During the pre-public phase (July 2026 – Oct 2026), automated branch protection rulesets are disabled. All pull request creations, test waiting, review approvals, and merges must strictly follow the pre-public code governance SOP:
- Refer to the [Developer Workflow & Code Governance Guide](references/developer_workflow_governance.md) for full rationale, 4-step submission lifecycle, `gh` CLI commands, and pre-merge verification checklist.

## Verification

You can verify the setup by running the test from the TPU VM host (outside the container) using a one-liner:
```bash
docker run --rm --privileged --net=host --shm-size=16g \
  -v /mnt/pd_<username>/.cache/huggingface:/root/.cache/huggingface \
  -v /mnt/pd_<username>/projects/vllm-torchtpu:/root/tpu_inference \
  -v /dev/vfio:/dev/vfio \
  -e HF_HOME=/root/.cache/huggingface \
  us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest \
  python3 examples/offline_inference.py \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --max-model-len 256 \
  --max-num-batched-tokens 256
```

## References

- [Developer Workflow & Code Governance Guide](references/developer_workflow_governance.md): Special pre-public governance SOP for PR creation, DCO sign-offs, reviewer assignments, CI tracking, guarded merges, and post-merge validation.
- [Local Reproduction and Debugging](references/local_reproduction.md): Detailed instructions on simulating GitHub Actions runs and debugging failures locally on a TPU VM.
- [Code Review Checklist](references/code_review_checklist.md): Comprehensive checklist for pull requests, covering JAX/vLLM separation, static analysis, styling, baseline evaluations, and checkpoints.



