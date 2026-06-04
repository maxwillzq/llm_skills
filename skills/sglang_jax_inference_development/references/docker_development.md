# Docker Development Flow for SGL-JAX

This document outlines how to set up a Docker container for developing SGL-JAX on TPU VMs.

## Base Image

We use the official Google Cloud TPU JAX image that matches the project's pinned dependency:
`us-docker.pkg.dev/cloud-tpu-images/jax-ai-image/tpu:jax0.8.1-rev1`

## Running the Container

Run the container interactively on your TPU VM, mounting your local code directory and Hugging Face cache:

```bash
docker run -it --privileged --net=host --shm-size=16g \
  -v /mnt/pd/.cache/huggingface:/root/.cache/huggingface \
  -v /mnt/pd/projects/sglang-jax:/app \
  -v /dev/vfio:/dev/vfio \
  -e HF_HOME=/root/.cache/huggingface \
  us-docker.pkg.dev/cloud-tpu-images/jax-ai-image/tpu:jax0.8.1-rev1 \
  bash
```

### Key Flags:
- `-v /mnt/pd/projects/sglang-jax:/app`: Mounts the project folder for live editing.
- `-v /dev/vfio:/dev/vfio`: Grants access to TPU devices.

## Inside the Container

Once inside the container, set up the environment in editable mode:

```bash
cd /app
uv venv --python 3.12 && source .venv/bin/activate
uv pip install -e "python[all]"
```

This allows you to modify code on your host (or via IDE) and see changes immediately in the container without rebuilding.
