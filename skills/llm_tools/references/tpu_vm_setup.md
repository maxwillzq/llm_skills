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
  -v /mnt/pd_<username>/.cache/huggingface:/root/.cache/huggingface \
  -v /dev/vfio:/dev/vfio \
  -e HF_HOME=/root/.cache/huggingface \
  <IMAGE_NAME>
```

### Key Flags Explained:
- `--privileged`: Often needed to access TPU devices.
- `--net=host`: Shares host network, useful for distributed training/serving.
- `--shm-size=16g`: Large shared memory for JAX/PyTorch data loading.
- `-v /mnt/pd_<username>/.cache/huggingface:/root/.cache/huggingface`: Mounts HF cache on persistent disk to avoid re-downloading models.
- `-v /dev/vfio:/dev/vfio`: Grants access to TPU devices.
- `-e HF_HOME=...`: Sets environment variable for HF cache location inside container.

---

## How to temporarily use someone else's TPU VM

If you want to temporarily use an idle Cloud TPU VM owned by someone else, you can attach and mount your own guest Persistent Disk (PD) to the VM. Follow these steps:

### 1. Attach your Persistent Disk to the TPU VM
Run the following command from your local machine (or cloudtop) to attach the disk to the target TPU VM:
```bash
/usr/bin/gcloud alpha compute tpus tpu-vm attach-disk <TPU_NAME> \
  --disk=<PD_NAME> \
  --project=<PROJECT_ID> \
  --zone=<ZONE>
```

### 2. SSH into the VM and mount the disk

1. SSH into the TPU VM:
   ```bash
   ssh <username>_google_com@<TPU_VM_IP>
   ```

2. Identify the new disk device name using `lsblk` or by ID:
   ```bash
   lsblk
   # OR check disk by ID:
   ls -l /dev/disk/by-id/
   ```
   Look for the link pointing to your disk name (e.g., `google-<PD_NAME>`).

3. Mount the disk:
   > [!NOTE]
   > We highly recommend using a distinct mount directory `/mnt/pd_<username>` to avoid conflicts with the TPU VM owner's default mount directory (which is often `/mnt/pd`).

   ```bash
   # Assuming the new disk device name is /dev/<DEVICE_NAME> (e.g., /dev/sdb)
   sudo mkdir -p /mnt/pd_<username>
   sudo mount /dev/<DEVICE_NAME> /mnt/pd_<username>/
   sudo chown -R <username> /mnt/pd_<username>
   # Restrict access to only yourself for security
   sudo chmod 700 /mnt/pd_<username>
   ```

### 3. Clean up and detach disk after use
Once you are done, please make sure to unmount the disk inside the VM and detach it from your local machine so other users can utilize the resources.

**Inside the TPU VM**:
```bash
sudo umount /mnt/pd_<username>
```

**On your local machine (or cloudtop)**:
```bash
/usr/bin/gcloud alpha compute tpus tpu-vm detach-disk <TPU_NAME> \
  --disk=<PD_NAME> \
  --project=<PROJECT_ID> \
  --zone=<ZONE>
```

---

## Mounting and Using the Shared Compilation Cache

To avoid spending hours compiling static graphs for large models (e.g. Qwen3-Coder-480B) on every VM startup, you can mount and use the pre-compiled XLA cache from the shared GCS bucket `torchtpu-vllm-xla-cache` which stores nightly GKE run caches.

### 1. Mount the GCS cache bucket using gcsfuse
On the TPU VM host, mount the GCS bucket to a local directory:
```bash
sudo mkdir -p /mnt/pd_<username>/xla_cache
sudo gcsfuse --allow-other --implicit-dirs torchtpu-vllm-xla-cache /mnt/pd_<username>/xla_cache
```

### 2. Map the cache directory and set VLLM_XLA_CACHE_PATH in Docker
When starting the Docker container, mount the cache directory and set the `VLLM_XLA_CACHE_PATH` environment variable:
```bash
docker run -it --privileged --net=host --shm-size=16g \
  -v /mnt/pd_<username>/.cache/huggingface:/root/.cache/huggingface \
  -v /mnt/pd_<username>/xla_cache:/root/xla_cache \
  -v /dev/vfio:/dev/vfio \
  -e HF_HOME=/root/.cache/huggingface \
  -e VLLM_XLA_CACHE_PATH=/root/xla_cache \
  <IMAGE_NAME>
```
