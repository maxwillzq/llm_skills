---
name: vllm-on-tpu
description: >-
  Guides developing vLLM on GCloud TPU VMs. Covers environment setup references,
  code synchronization, and remote execution. Use when you need to develop,
  test, or benchmark vLLM on a remote TPU VM.
---

This skill guides Jetski on developing vLLM on TPU VMs. It covers code
synchronization and remote execution as basic functions. It handles both
`tpu-inference` and `vllm` repositories automatically.

### Prerequisites

Before using this skill, verify that your project directory exists on the
Cloudtop under `~/projects/`.

**If the directory does not exist, STOP work immediately and ask the user to**
**set it up.** It should be a Git clone or a directory you want to sync.

On the **Remote TPU VM**:

-   Verify that the remote host exists and is reachable (e.g., by running `ssh
    ${USER}-tpu-v7 "echo OK"`).
-   **If it does not exist or is not reachable, STOP work and ask the user to**
    **set up the TPU VM first.**
-   The sync script will automatically create the destination directory on the
    remote VM if it does not exist.

### Context

-   **Local Directory**: `/usr/local/google/home/$USER/projects/<project_name>/`
-   **Remote TPU VM**: `$USER-tpu-v7` (default, or as specified by user)
-   **Remote TPU VM Directory**: `/mnt/pd/projects/<project_name>/`

### Environment Setup Guidance

Use this guidance when asked to help set up the GCloud TPU VM environment for
vLLM development.

**Example Prompt**:

> "Help me set up the gcloud TPU VM"

**Guidance**:

1.  Read the
    [Onboarding Guide](file:///google/src/cloud/johnqiangzhang/jetski/google3/learning/infra/mira/experimental/vllm_on_tpu/docs/dive-deep/onboard_gcloud_tpu_vm.md).
2.  Guide the user through the **Part 1: Step-by-Step Guide** interactively.
3.  **Do NOT** run the commands automatically unless the user explicitly asks
    you to do so and provides all necessary parameters.
4.  Infer LDAP from ${USER}. Ask the user to provide values for other variables
    in Step 1 (e.g., PROJECT_ID) if they cannot be inferred.
5.  Warn the user that some steps (like creating the disk or TPU) might incur
    costs and need appropriate permissions.
6.  Pay special attention to **Step 8** of the guide to help the user set up the
    Python virtual environment and repositories on the TPU VM.
7.  **Enforce HF Cache Location**: Instruct the user to set `export HF_HOME=/mnt/pd/.cache/huggingface` to ensure models are cached on the persistent disk.

### End-to-End Testing Guidance

Use this guidance when asked to perform a quick end-to-end test of the
development flow.

**Example Prompt**:

> "Quick test the vllm-on-tpu jetski development end2end flow"

**Guidance**:

1.  **Verify SSH**: Check if `tpu-vm-ssh "echo OK"` works. If not, report to
    user.
2.  **Verify Repositories**: Check if `/usr/local/google/home/$USER/projects/`
    contains both `tpu-inference` and `vllm` directories.
3.  **Select Commits**: Ask the user which commit IDs or branches of
    `tpu-inference` and `vllm` they want to use, or use current state.
4.  **Verify HuggingFace Auth**: Check if `hf` authentication is working on the
    TPU VM (e.g., by running `hf auth login` or checking for a token).
5.  **Run Verification Test**: Run the offline inference example on the remote
    VM using the configured venv: `bash tpu-vm-ssh "cd
    /mnt/pd/projects/tpu-inference && /mnt/pd/vllm-venv/bin/python3
    examples/offline_inference.py"`
6.  Report the results to the user.

### Benchmarking and Profiling Guidance

Use this guidance when asked to perform benchmarking, reporting, and code
analysis for a model on TPU.

**Example Prompt**:

> "Benchmark the Qwen/Qwen2.5-7B-Instruct model, summarize a perf report on
> google doc, list which part of jax codes we can improve"

**Guidance**:

1.  **Acknowledge Complexity**: This is a complex task. Break it down and
    confirm steps with the user.
2.  **Server Setup**: Guide the user to start the `vLLM` server with the
    specified model on the TPU VM. Ensure `USE_JAX_PROFILER_SERVER=True` is set
    if profiling is needed.
3.  **Run Benchmark**: Use the vLLM benchmarking tool as described in the
    Onboarding Guide (Step 9).
4.  **Capture Profile**: If needed, ensure the server is started with
    `PHASED_PROFILING_DIR` to automatically dump profiles. Ensure the benchmark
    runs long enough (e.g., by increasing number of prompts) to capture a valid
    trace.
5.  **Report Generation**: Use the Google Docs skill (if available) or output a
    markdown report to be converted. Summarize latency, throughput, and any
    bottlenecks identified. Always include the commit IDs of the repositories
    (`vllm` and `tpu-inference`), the exact command lines used, and the
    `xprof.corp.google.com` link to ensure reproducibility and allow for deep
    analysis.
6.  **Code Improvement Analysis**: Perform a deep dive analysis using `xprof`
    tools:
    -   Use `get_overview` to check duty cycle and goodput.
    -   Use `get_memory_profile` to analyze memory bandwidth bottlenecks.
    -   Use `get_top_hlo_ops` to find time-consuming operations.
    -   Use `get_hlo_module_content` with `--print_metadata=True` to find
        `op_name` and map back to specific lines in the codebase (e.g.,
        identifying specific projection layers in Attention or MLP).
7.  **Rule of Thumb**: Always check if the model fits in memory and if the batch
    size is optimized for TPU.

### Key Tool

Script: `skills/llm_tools/scripts/tpu_dev_sync.py` (in repo)

### Usage Instructions

**General Rule for Long-Running Commands**: When running large commands on the
backend (like sync, test, or benchmark) that require the user to wait,
**always** provide the user with the command to tail the log file (e.g., `tail
-f <log_path>`) so they can monitor progress.

**General Rule for gcloud**: If the `gcloud` command fails or is not found
(often due to Python version incompatibilities on Cloudtop), always try using
the absolute path `/usr/bin/gcloud`.

#### 1. Code Synchronization

Jetski must run the sync script to keep code in sync. You need to specify the
project name or be inside the project directory under `~/projects/`.

*   **Push Changes (Local -> Remote)**: `skills/llm_tools/scripts/tpu_dev_sync.py push [project_name]` *Warning: This will delete files on the remote TPU VM
    that are not present locally.*

*   **Pull Changes (Remote -> Local)**: `skills/llm_tools/scripts/tpu_dev_sync.py pull [project_name]` *Warning: This will delete files on the local Cloudtop
    that are not present on the remote TPU VM.*

*   **Bidirectional Sync**: `skills/llm_tools/scripts/tpu_dev_sync.py both [project_name]`

#### 2. Remote Execution

To run tests or commands on the TPU VM, Jetski should use `tpu-vm-ssh` from the
Cloudtop.

**Alias Setup**: You can assume the following alias is available. To make it
persistent on your Cloudtop, you can add it to your `~/.bashrc`:

```bash
echo 'alias tpu-vm-ssh="ssh ${USER}-tpu-v7"' >> ~/.bashrc
source ~/.bashrc
```

Or set it manually in your current session if needed:

```bash
alias tpu-vm-ssh='ssh ${USER}-tpu-v7'
```

**Example Usage**:

```bash
tpu-vm-ssh "cd /mnt/pd/projects/my-project && pytest tests/"
```

Always ensure you have synced the code before running remote commands.

### References

-   [Onboarding Guide](file:///google/src/cloud/johnqiangzhang/jetski/google3/learning/infra/mira/experimental/vllm_on_tpu/docs/dive-deep/onboard_gcloud_tpu_vm.md):
    Step-by-step guide for environment setup on TPU VM.
-   [Troubleshooting](file:///google/src/cloud/johnqiangzhang/vllm7/google3/learning/infra/mira/experimental/vllm_on_tpu/agents/skills/vllm_on_tpu/references/troubleshooting.md):
    Common troubleshooting steps and best practices for vLLM on TPU.
-   **Markdown Standards**: See `md_lint/SKILL.md` for formatting guidelines.
    *Tip: Always leave a blank line before lists to prevent `mdformat` from*
    *merging them.*
-   **Python Standards**: See `python_readability/SKILL.md` for style
    guidelines.

### Testing the Skill

To verify that this skill and the sync script are working correctly, refer to
the test plan in [TEST.md](TEST.md).
