---
name: torch-vllm-development
description: >-
  Develops and tests torchtpu-vllm on TPU VMs. Use when setting up the Python environment on a TPU VM, running verification tests like offline inference, or mocking HuggingFace downloads in the test environment to use GCS instead.
---

# Developing torchtpu-vllm on TPU

use "ssh johnqiangzhang-tpu-v7" or alias "tpu-vm-ssh" to ssh login to tpu.
use "skills/llm_tools/scripts/tpu_dev_sync.py" to push and sync torchtpu-vllm folder between cloudtop "~/project/torchtpu-vllm"  and 
tpu VM "/mnt/pd/projects/torchtpu-vllm".

## Local Environment Setup (Cloudtop)

For IDE support and pre-commit hooks on your Cloudtop:
```bash
cd ~/projects/torchtpu-vllm
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

### Alternative: Build Dev Image Locally
If you prefer to build the dev image locally (e.g., to include latest changes in `pyproject.toml` or `Dockerfile`):

On your **TPU VM**:
```bash
cd /mnt/pd/projects/torchtpu-vllm
./docker/build_image.sh --torch-tpu-registry --target dev -t torchtpu-vllm-dev:local
```

> [!TIP]
> **Docker Disk Space**: Building Docker images can consume a lot of space on the root partition (`/`). If you need to migrate the Docker data directory to the larger `/mnt/pd` disk, see the [Docker Migration Guide](references/docker_migration.md).




### 2. Run Container

Mount your local code directory for real-time sync and persistent HuggingFace cache if not:
```bash
docker run -it --privileged --net=host --shm-size=16g \
  -v /mnt/pd/.cache/huggingface:/root/.cache/huggingface \
  -v /mnt/pd/projects/torchtpu-vllm:/root/tpu_inference \
  -v /dev/vfio:/dev/vfio \
  -e HF_HOME=/root/.cache/huggingface \
  us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest
```

## Code Synchronization and Remote Execution

Refer to the `vllm-on-tpu` skill for detailed instructions on how to use TPU VMs and synchronize code using the `skills/llm_tools/scripts/tpu_dev_sync.py` script.

### Source Code Location
*   **Local Cloudtop**: `~/projects/torchtpu-vllm`
*   **Remote TPU VM**: `/mnt/pd/projects/torchtpu-vllm`

### Usage Summary
*   **Syncing Code**: Use the `skills/llm_tools/scripts/tpu_dev_sync.py` script as described in the `vllm-on-tpu` skill to push local changes from Cloudtop to the remote TPU VM.
*   **Remote Execution**: Use `ssh` (or the `tpu-vm-ssh` alias) to run tests and examples on the TPU VM.

## Local Reproduction and CI Debugging

If the user explicitly requests you to locally reproduce a GitHub Actions (CI/CD) workflow failure, or when you are asked to debug or validate PR Guard / Nightly runs on a development TPU VM:
- Refer to the [Local Reproduction and Debugging](references/local_reproduction.md) reference guide for template commands and concrete examples of pulling the dev container, mounting local caches, and running evaluation benchmarks or unit tests.

## Verification

You can verify the setup by running the test from the TPU VM host (outside the container) using a one-liner:
```bash
docker run --rm --privileged --net=host --shm-size=16g \
  -v /mnt/pd/.cache/huggingface:/root/.cache/huggingface \
  -v /mnt/pd/projects/torchtpu-vllm:/root/tpu_inference \
  -v /dev/vfio:/dev/vfio \
  -e HF_HOME=/root/.cache/huggingface \
  us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest \
  python3 examples/offline_inference.py \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --max-model-len 256 \
  --max-num-batched-tokens 256
```

## References

- [Local Reproduction and Debugging](references/local_reproduction.md): Detailed instructions on simulating GitHub Actions runs and debugging failures locally on a TPU VM.

