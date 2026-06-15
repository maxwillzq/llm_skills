#!/bin/bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Script to build local developer docker images from source for torch_tpu and torchtpu-vllm.

set -euo pipefail

# Default values
TORCH_TPU_DIR="${HOME}/projects/torch_tpu"
TORCHTPU_VLLM_DIR="${HOME}/projects/torchtpu-vllm"
IMAGE_TAG="torchtpu-vllm-dev:local"
PUSH_IMAGE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -t|--image-tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    --push)
      PUSH_IMAGE="1"
      shift
      ;;
    --torch-tpu-dir)
      TORCH_TPU_DIR="$2"
      shift 2
      ;;
    --torchtpu-vllm-dir)
      TORCHTPU_VLLM_DIR="$2"
      shift 2
      ;;
    -*)
      echo "Unknown option: $1" >&2
      exit 1
      ;;
    *)
      # Fallback for positional parameters
      if [ -z "${TORCH_TPU_DIR_SET:-}" ]; then
        TORCH_TPU_DIR="$1"
        TORCH_TPU_DIR_SET=1
      elif [ -z "${TORCHTPU_VLLM_DIR_SET:-}" ]; then
        TORCHTPU_VLLM_DIR="$1"
        TORCHTPU_VLLM_DIR_SET=1
      elif [ -z "${IMAGE_TAG_SET:-}" ]; then
        IMAGE_TAG="$1"
        IMAGE_TAG_SET=1
      else
        echo "Unknown argument: $1" >&2
        exit 1
      fi
      shift
      ;;
  esac
done


echo "=========================================================="
echo "🚀 Local Docker Build Coordinator for TPU Inference"
echo "=========================================================="
echo "📂 torch_tpu source:    ${TORCH_TPU_DIR}"
echo "📂 torchtpu-vllm source: ${TORCHTPU_VLLM_DIR}"
echo "🏷️ Target Image Tag:      ${IMAGE_TAG}"
echo "=========================================================="

# Validation
if [ ! -d "${TORCH_TPU_DIR}" ]; then
  # Try without 's' if not found
  ALT_DIR="${HOME}/project/torch_tpu"
  if [ -d "${ALT_DIR}" ]; then
    TORCH_TPU_DIR="${ALT_DIR}"
  else
    echo "❌ Error: torch_tpu source directory not found at ${TORCH_TPU_DIR}" >&2
    exit 1
  fi
fi

if [ ! -d "${TORCHTPU_VLLM_DIR}" ]; then
  # Try without 's' or alternative spelling if not found
  ALT_DIR="${HOME}/project/torchtpu-vllm"
  ALT_DIR2="${HOME}/project/torctpu_vllm"
  ALT_DIR3="${HOME}/projects/torctpu_vllm"
  if [ -d "${ALT_DIR}" ]; then
    TORCHTPU_VLLM_DIR="${ALT_DIR}"
  elif [ -d "${ALT_DIR2}" ]; then
    TORCHTPU_VLLM_DIR="${ALT_DIR2}"
  elif [ -d "${ALT_DIR3}" ]; then
    TORCHTPU_VLLM_DIR="${ALT_DIR3}"
  else
    echo "❌ Error: torchtpu-vllm source directory not found at ${TORCHTPU_VLLM_DIR}" >&2
    exit 1
  fi
# Register cleanup trap to restore modified files on exit
cleanup() {
  if [ -f "${TORCHTPU_VLLM_DIR}/pyproject.toml.bak" ]; then
    echo "🧹 Restoring torchtpu-vllm/pyproject.toml..."
    mv "${TORCHTPU_VLLM_DIR}/pyproject.toml.bak" "${TORCHTPU_VLLM_DIR}/pyproject.toml"
  fi
}
trap cleanup EXIT

# Temporarily patch torchtpu-vllm/pyproject.toml to match local wheel version (0.1.1)
if [ -f "${TORCHTPU_VLLM_DIR}/pyproject.toml" ]; then
  echo "🔧 Temporarily patching torchtpu-vllm/pyproject.toml dependency constraints..."
  # Create a backup
  cp "${TORCHTPU_VLLM_DIR}/pyproject.toml" "${TORCHTPU_VLLM_DIR}/pyproject.toml.bak"
  # Replace pinned dev version with local 0.1.1 version
  sed -i 's/"torch-tpu==0.1.1.dev[0-9]*",/"torch-tpu==0.1.1",/' "${TORCHTPU_VLLM_DIR}/pyproject.toml"
fi

# Step 1: Build local torch-tpu
echo "📦 Step 1: Building local torch_tpu images..."

# Build base image
echo "===> Building torch_tpu Base Image..."
docker build \
  --progress=plain \
  --target base \
  -f "${TORCH_TPU_DIR}/docker/Dockerfile.multistage" \
  -t "torch-tpu-base:local" \
  "${TORCH_TPU_DIR}"

# Build final image
echo "===> Building torch_tpu Final Image..."
docker build \
  --progress=plain \
  -f "${TORCH_TPU_DIR}/docker/Dockerfile.multistage" \
  -t "torch-tpu:local" \
  "${TORCH_TPU_DIR}"

# Step 2: Build local torchtpu-vllm referencing local torch-tpu
echo "📦 Step 2: Building local torchtpu-vllm developer image..."
cd "${TORCHTPU_VLLM_DIR}"
./docker/build_image.sh \
  --base-image torch-tpu-base:local \
  --artifact-source torch-tpu:local \
  --target dev \
  --image-tag "${IMAGE_TAG}"

echo "=========================================================="
echo "✅ Build Successful!"
echo "🐳 Dev Image ready: ${IMAGE_TAG}"
echo "=========================================================="

if [ -n "${PUSH_IMAGE}" ]; then
  echo "📤 Pushing image to registry: ${IMAGE_TAG}..."
  docker push "${IMAGE_TAG}"
  echo "=========================================================="
  echo "✅ Push Successful!"
  echo "=========================================================="
fi





