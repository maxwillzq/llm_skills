# Create CloudTop IDE env

We will use jetski on cloudtop.


## 1. Get and Sync Code

On your **Cloudtop**:
```bash
cd ~/projects
git clone git@github.com:google-pytorch/torchtpu-vllm.git

# Run from google3 workspace to sync to TPU VM
SYNC_SCRIPT="learning/infra/mira/experimental/vllm_on_tpu/agents/skills/vllm_on_tpu/scripts/tpu_dev_sync.sh"
bash $SYNC_SCRIPT push torchtpu-vllm
```

## 2. Setup Local Environment (Cloudtop)

We will use jetski on cloudtop.
Assumes basic TPU VM setup is done (mounting storage, etc.).


For IDE support and pre-commit hooks:
```bash
cd ~/projects/torchtpu-vllm
uv venv
source .venv/bin/activate
uv pip install --no-config --index-url https://pypi.org/simple pre-commit pytest
pre-commit install
```

## 3. Get Docker Image

On your **TPU VM**:
```bash
# Docker setup (reconnect SSH after usermod)
sudo usermod -aG docker $USER
gcloud auth configure-docker us-central1-docker.pkg.dev

# Pull the pre-built dev image instead of building it locally:
docker pull us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest
```

or build by yourself

```bash
./docker/build_image.sh --torch-tpu-registry --target dev -t torchtpu-vllm-dev:local
```



## 4. Run Container

Mount your local code directory for real-time sync:
```bash
docker run -it --privileged --net=host --shm-size=16g \
  -v /mnt/pd/.cache/huggingface:/root/.cache/huggingface \
  -v /mnt/pd/projects/torchtpu-vllm:/root/tpu_inference \
  -v /dev/vfio:/dev/vfio \
  -e HF_HOME=/root/.cache/huggingface \
  us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest
```

## 5. Verify

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
