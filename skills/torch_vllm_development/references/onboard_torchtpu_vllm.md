# Create CloudTop IDE env

We will use jetski on cloudtop.


## 1. Get and Sync Code

On your **Cloudtop**:
```bash
cd ~/projects
git clone git@github.com:google-pytorch/torchtpu-vllm.git

# Run from repo root to sync to TPU VM
SYNC_SCRIPT="skills/llm_tools/tpu_dev_sync.py"
python3 $SYNC_SCRIPT push torchtpu-vllm
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

For general Docker setup on TPU VM (permissions, auth), see [TPU VM Setup](file:///usr/local/google/home/johnqiangzhang/projects/llm_skills/tools/references/tpu_vm_setup.md).

On your **TPU VM**, pull the specific image for `torchtpu-vllm`:
```bash
docker pull us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm-dev:latest
```

Or build it locally:
```bash
cd /mnt/pd/projects/torchtpu-vllm
./docker/build_image.sh --torch-tpu-registry --target dev -t torchtpu-vllm-dev:local
```

## 4. Run Container

Run the container with the specific project volume mount. Refer to [TPU VM Setup](file:///usr/local/google/home/johnqiangzhang/projects/llm_skills/tools/references/tpu_vm_setup.md) for details on general flags.

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
