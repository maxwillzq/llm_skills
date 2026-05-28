# General TPU VM Setup for LLM Development

This document outlines general setup steps for development on GCloud TPU VMs, common to many LLM libraries.

## Docker Setup on TPU VM

To use Docker without `sudo` and configure access to Google Container Registry:

```bash
# Add user to docker group (reconnect SSH after running this)
sudo usermod -aG docker $USER

# Configure gcloud for docker (adjust region if needed)
gcloud auth configure-docker us-central1-docker.pkg.dev
```

## Running Docker for TPU

When running a Docker container for LLM development on TPU, you typically need these flags to access hardware and cache models efficiently:

```bash
docker run -it --privileged --net=host --shm-size=16g \
  -v /mnt/pd/.cache/huggingface:/root/.cache/huggingface \
  -v /dev/vfio:/dev/vfio \
  -e HF_HOME=/root/.cache/huggingface \
  <IMAGE_NAME>
```

### Key Flags Explained:
- `--privileged`: Often needed to access TPU devices.
- `--net=host`: Shares host network, useful for distributed training/serving.
- `--shm-size=16g`: Large shared memory for JAX/PyTorch data loading.
- `-v /mnt/pd/.cache/huggingface:/root/.cache/huggingface`: Mounts HF cache on persistent disk to avoid re-downloading models.
- `-v /dev/vfio:/dev/vfio`: Grants access to TPU devices.
- `-e HF_HOME=...`: Sets environment variable for HF cache location inside container.
