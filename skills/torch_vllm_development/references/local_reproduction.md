# Local Reproduction and Debugging

If the CI (GitHub Actions) fails or you want to test changes locally before pushing, you can run the exact same evaluation flow on a development TPU VM.

## Prerequisites
- A Cloud TPU VM with Docker installed.
- Your code synced to the TPU VM (e.g., in `/mnt/pd_<username>/projects/torchtpu-vllm`).
- `gcloud` authenticated on the TPU VM or passed from host.
- An alias `tpu-vm-ssh` configured to SSH into your TPU VM (see below).

### Setting up `tpu-vm-ssh` Alias

```bash
alias tpu-vm-ssh="ssh <user_name>@tpu_ip_addr"
```

## Running the Full Flow in Docker

To simulate the CI environment as closely as possible, run the tests inside the designated Docker container on the TPU VM.

> [!NOTE]
> **Dubious Ownership Error**: If you encounter `fatal: detected dubious ownership` error when running `uv pip install` or git commands inside the container, you may need to run the following command inside the container:
>
> ```bash
> git config --global --add safe.directory /root/tpu_inference
> ```
>
> TODO: Move this to Dockerfile to avoid this manual step.

### Option A: Running with the Dev Image (`torchtpu-vllm-dev:latest`)

This is the recommended approach for fast local development and iteration, as the dev image comes with dependencies pre-installed.

First, pull the latest dev Docker image on your TPU VM:

```bash
ssh <TPU_VM_NAME> "gcloud auth configure-docker us-docker.pkg.dev && docker pull us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest"
```

Then, run the following command from your local machine (Cloudtop) to trigger the run on the TPU VM via SSH:

```bash
ssh <TPU_VM_NAME> "docker run --rm --privileged --net=host --ipc=host \
  -v /mnt/pd_<username>/projects/torchtpu-vllm:/root/tpu_inference \
  -v /mnt/pd_<username>/.cache/huggingface:/local_hf_cache \
  us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest \
  bash -c 'cd /root/tpu_inference && bash ./scripts/vllm/benchmarking/run_eval_flow.sh --config <CONFIG_NAME> --run-lm-eval'"
```

Replace `<TPU_VM_NAME>` with your TPU VM hostname and `<CONFIG_NAME>` with one of the available configs.

*(Note: `--ipc=host` is recommended to automatically share the host's entire shared memory `/dev/shm` without limit. If not supported, use `--shm-size=16g` or higher.)*

### Option B: Running with the CI Image (`torchtpu-vllm-ci:latest`)

Use this approach to replicate the exact environment of the GitHub Actions runner. Because the CI image does not pre-install the repository's dependencies, the command will set up a virtual environment and install them before executing the evaluation.

First, pull the latest CI Docker image on your TPU VM:

```bash
ssh <TPU_VM_NAME> "gcloud auth configure-docker us-docker.pkg.dev && docker pull us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-ci:latest"
```

Then, run the following command from your local machine (Cloudtop) to trigger the run on the TPU VM via SSH:

```bash
ssh <TPU_VM_NAME> "docker run --rm --privileged --net=host --ipc=host \
  -v /mnt/pd_<username>/projects/torchtpu-vllm:/root/tpu_inference \
  -v /mnt/pd_<username>/.cache/huggingface:/local_hf_cache \
  -e HF_HOME=/local_hf_cache \
  -e SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0 \
  us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-ci:latest \
  bash -c '
    cd /root/tpu_inference && \
    git config --global --add safe.directory /root/tpu_inference && \
    mkdir -p /tmp/torch_tpu_cache && ln -sfn /tmp/torch_tpu_cache /dev/shm/torch_tpu_cache && \
    (command -v uv || curl -LsSf https://astral.sh/uv/install.sh | sh) && \
    export PATH=\"\$HOME/.local/bin:\$PATH\" && \
    uv venv && \
    . .venv/bin/activate && \
    uv pip install \".[test,benchmarking]\" && \
    bash ./scripts/vllm/benchmarking/run_eval_flow.sh --config <CONFIG_NAME> --run-lm-eval
  '"
```

Replace `<TPU_VM_NAME>` with your TPU VM hostname and `<CONFIG_NAME>` with one of the available configs.

### Available Configurations

You can choose from the following configurations defined in [perf.yml](file:///usr/local/google/home/johnqiangzhang/projects/torchtpu-vllm/.github/workflows/perf.yml):

*   **PR Guard / Fast Runs**:
    *   `qwen3-coder-30b-tp8-ep`
    *   `qwen3-coder-30b-fp8-tp8-ep`
    *   `qwen3.5-35b-fp8-tp4-ep`
*   **Nightly / Deep Benchmarks**:
    *   `qwen3-coder-480b-fp8-tp8-ep`
    *   `qwen3.5-397b-fp8-tp8-ep`

---

## Concrete Examples

**1. PR Guard (e.g., Qwen3-Coder-30B-A3B-Instruct-FP8)**
```bash
tpu-vm-ssh "docker run --rm --privileged --net=host --ipc=host \\
  -v /mnt/pd_<username>/projects/torchtpu-vllm:/root/tpu_inference \\
  -v /mnt/pd_<username>/.cache/huggingface:/local_hf_cache \\
  us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest \\
  bash -c 'cd /root/tpu_inference && bash ./scripts/vllm/benchmarking/run_eval_flow.sh --config qwen3-coder-30b-fp8-tp8-ep --run-lm-eval'"
```

**2. Nightly Benchmark with EvalPlus (e.g., Qwen 3.5-397B)**
```bash
tpu-vm-ssh "docker run --rm --privileged --net=host --ipc=host \\
  -v /mnt/pd_<username>/projects/torchtpu-vllm:/root/tpu_inference \\
  -v /mnt/pd_<username>/.cache/huggingface:/local_hf_cache \\
  -e EVALPLUS_DATASETS=\"humaneval mbpp\" \\
  -e EVALPLUS_PARALLEL=8 \\
  us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest \\
  bash -c 'cd /root/tpu_inference && bash ./scripts/vllm/benchmarking/run_eval_flow.sh --config qwen3.5-397b-fp8-tp8-ep --run-lm-eval --run-evalplus'"
```

**3. Unit Tests**
```bash
tpu-vm-ssh "docker run --rm --privileged --net=host --ipc=host \\
  -v /mnt/pd_<username>/projects/torchtpu-vllm:/root/tpu_inference \\
  -v /mnt/pd_<username>/.cache/huggingface:/local_hf_cache \\
  us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest \\
  bash -c 'cd /root/tpu_inference && bash ./scripts/vllm/benchmarking/run_unit_test.sh false'"
```

## Script Details

### `run_eval_flow.sh`
This is the unified script used by both CI and manual runs. It handles:
1. Initial cleanup of any leaked servers.
2. Starting the vLLM server and running performance benchmarks.
3. Running `lm_eval` (if `--run-lm-eval` is passed).
4. Running `evalplus` (if `--run-evalplus` is passed).
5. Final cleanup.
6. Regression checks against baselines.
