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
   ssh <LDAP>_google_com@<TPU_VM_IP>
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
   > We highly recommend using a distinct mount directory `/mnt/pd_<LDAP>` to avoid conflicts with the TPU VM owner's default mount directory (which is often `/mnt/pd`).

   ```bash
   # Assuming the new disk device name is /dev/<DEVICE_NAME> (e.g., /dev/sdb)
   sudo mkdir -p /mnt/pd_<LDAP>
   sudo mount /dev/<DEVICE_NAME> /mnt/pd_<LDAP>/
   sudo chown -R <LDAP> /mnt/pd_<LDAP>
   # Restrict access to only yourself for security
   sudo chmod 700 /mnt/pd_<LDAP>
   ```

### 3. Clean up and detach disk after use
Once you are done, please make sure to unmount the disk inside the VM and detach it from your local machine so other users can utilize the resources.

**Inside the TPU VM**:
```bash
sudo umount /mnt/pd_<LDAP>
```

**On your local machine (or cloudtop)**:
```bash
/usr/bin/gcloud alpha compute tpus tpu-vm detach-disk <TPU_NAME> \
  --disk=<PD_NAME> \
  --project=<PROJECT_ID> \
  --zone=<ZONE>
```
