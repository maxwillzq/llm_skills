# Managing the CI/CD Checkpoint Bucket

This document guides how to manage and use the GCS bucket
`gs://tpu-inference-hf-llm-model-checkpoints/` used for caching Hugging Face
models in CI/CD.


## 1. Upload the model checkpoint directly to the CI/CD bucket

The recommended way to populate the CI/CD bucket is to download the model on your **Cloudtop** (where you have working credentials) and then upload it directly to GCS. This avoids authentication issues often encountered on remote TPU VMs.

### Step 1: Download the model on Cloudtop

Use the `hf` CLI (Hugging Face Hub CLI) with the `--local-dir` option to download the model files directly to a local folder. This avoids the complex symlink structure of the default cache.

Example:
```bash
# Create a dedicated directory if needed
mkdir -p ~/hf_downloads/

# Download the model
hf download Qwen/Qwen3-0.6B --local-dir ~/hf_downloads/models--Qwen--Qwen3-0.6B
```

### Step 2: Upload to GCS

Use `gcloud storage rsync` to upload the downloaded directory to the CI/CD bucket.

Example:
```bash
gcloud storage rsync -r ~/hf_downloads/models--Qwen--Qwen3-0.6B gs://tpu-inference-hf-llm-model-checkpoints/models--Qwen--Qwen3-0.6B/
```

### Step 3: Clean up

Remove the local files to save space on your Cloudtop.
```bash
rm -rf ~/hf_downloads/models--Qwen--Qwen3-0.6B
```

> [!NOTE]
> Everyone in the project has permission to upload directly to the CI/CD bucket.


