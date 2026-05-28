# One-Pager: Docker & CI/CD Optimization for torchtpu-vllm

## Problem Statement
The current CI/CD pipeline for `torchtpu-vllm` suffers from long execution times, primarily due to the need to fetch and compile large dependencies (like vLLM and torch-tpu) from source on every run. Additionally, local development requires a flexible way to switch between editable mode and production-like environments.

## Implemented Solution
After this PR https://github.com/google-pytorch/torchtpu-vllm/pull/138 by Parker Holloway, it opens the door to improve the CICD docker build time. Here we will continue improve it for CICD.

We have refactored the Docker build system and updated the CI/CD workflows to address these issues:

*   **Multi-Stage Dockerfile**: Refactored `docker/Dockerfile` to support targeted builds:
    *   `base`: Contains only heavy dependencies (vLLM, torch-tpu). Used as CI base image.
    *   `dev`: Installs `torchtpu-vllm` in editable mode for local development.
    *   `prod`: Installs `torchtpu-vllm` normally for deployment (default).
*   **Updated Build Script**: Updated `docker/build_image.sh` to use the `--target` flag, mapping directly to Docker stages.
*   **Optimized CI/CD Workflows**: Updated `.github/workflows/tests.yml` and `.github/workflows/perf.yml` to use the `base` image, removing redundant installation steps and reducing CI time by an estimated 5-10 minutes per run.

## Key Benefits
*   **Faster CI/CD**: Drastically reduces PR validation time by skipping heavy dependency builds.
*   **Cleaner Architecture**: Decouples dependency installation from application installation in Docker.
*   **Better Developer Experience**: Standardized `--target dev` for local editable development, mapped to standard Docker concepts.

## Next Steps
*   **Build and Push Base Image**: Build the image targeting `base` and push it to the Artifact Registry path specified in the YAML files (`us-docker.pkg.dev/ml-oss-artifacts-transient/torch-tpu-docker-container/torchtpu-vllm:base`).
    *   *Note: CI will fail to pull the image until it is pushed.*

## Historical Context / Notes
*   **Prototype change**: `https://paste.googleplex.com/6405027984965632`
*   **Process**: Saved as patch file and recreated the commit via `git am 0001-Refactor-Docker-build-and-optimize-CI-CD.patch`.
*   *(Note: The user noted they did not have written permission to `torchtpu-vllm` to create PR directly, but I assisted in creating PR #160).*
