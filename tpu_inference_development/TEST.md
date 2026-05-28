# Test Plan for vLLM on TPU Skill

This document outlines the steps to verify that the `vllm-on-tpu` skill and its
associated script work correctly.

## Prerequisites

Ensure you have completed the setup described in `SKILL.md`:

-   Project directory exists on Cloudtop under `~/projects/`.
-   Remote TPU VM accessible.

## Test Cases

### 1. Verify Remote Host Reachability

Run the following command to verify that you can reach the remote host:

```bash
ssh ${USER}-tpu-v7 "echo OK"
```

**Expected Output**: `OK` (and potentially a warning about adding to known hosts
if it's the first time).

### 2. Verify Remote Projects Directory

Run the following command to verify that you can write to `/mnt/pd/`:

```bash
ssh ${USER}-tpu-v7 "mkdir -p /mnt/pd/projects && echo OK"
```

**Expected Output**: `OK`

### 3. Verify Sync Script (Safe Sync)

Run the safe sync command with a dummy project name (e.g., `my-project`) to
ensure it completes without errors. Assume you have a directory
`~/projects/my-project`.

```bash
bash learning/infra/mira/experimental/vllm_on_tpu/agents/skills/\
vllm_on_tpu/scripts/tpu_dev_sync.sh both my-project
```

**Expected Output**: - Should print `=== Ensuring Remote Directory Exists
===`. - Should print `=== Safe Bidirectional Sync (NO Deletions) ===`. - Should
list files being synced or show completed messages for `my-project`. - Should
end with `=== Sync Complete ===`.

### 4. Verify Remote Execution

Run a simple command on the remote VM to verify execution works:

```bash
ssh ${USER}-tpu-v7 "ls /mnt/pd/projects/my-project"
```

**Expected Output**: Should list the contents of the remote `my-project`
directory.

### 5. Negative Test: Missing Project Name

Run the script without arguments and not inside a project directory to verify it
fails:

```bash
cd ~
bash learning/infra/mira/experimental/vllm_on_tpu/agents/skills/\
vllm_on_tpu/scripts/tpu_dev_sync.sh push
```

**Expected Output**: The script should fail with: `ERROR: Project name not
specified and could not be inferred from current directory.`
