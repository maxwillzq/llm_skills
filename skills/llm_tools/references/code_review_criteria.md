# Code Review Criteria for torchtpu-vllm

This document defines the key standards, conventions, and requirements that must be met when reviewing pull requests (PRs) or developing code in the `torchtpu-vllm` repository.

---

## 1. Commit and Licensing Requirements

### Developer Certificate of Origin (DCO) Sign-off
Every commit in a PR must be signed off to certify its developer origin.
*   **Rule**: The commit message must contain a `Signed-off-by: User Name <user.email@example.com>` line at the very end.
*   **Verification**: This is automatically added/enforced by the pre-commit `signoff-commit` hook. If bypass is needed, use `git commit --no-verify` (discouraged).
*   **Action**: Use `git commit -s` when committing.

---

## 2. Directory and Architecture Conventions

We maintain a strict separation between JAX and vLLM (PyTorch) layers and models to prevent cross-contamination:

*   **`tpu_inference/layers/`**:
    *   `common/`: Layers and utilities shared across models.
    *   `vllm/`: Layers used exclusively by vLLM (PyTorch) models.
*   **`tpu_inference/models/`**:
    *   `vllm/`: Model architectures specific to vLLM (PyTorch).

### Package Init Verification
*   Every subdirectory under `tpu_inference/` must contain an `__init__.py` file. This is enforced automatically by the `detect-missing-init` pre-commit hook to prevent import resolution failures.

---

## 3. Formatting, Linting, and Coding Standards

All code check-ins must comply with the following style enforcement checks (configured via `.pre-commit-config.yaml`):

### Python Style Guide
*   **Formatting**: Python code is formatted according to Google's style using **`yapf`** (`args: [--in-place, --verbose]`).
*   **Imports**: Imports must be sorted alphabetically and grouped using **`isort`**.
*   **Lints & Quality**: Code must pass all lints checked by **`ruff`** (`--fix` is automatically applied on pre-commit).
*   **Filename spacing**: Filenames must not contain spaces (enforced by `check-filenames` hook).

### Shell and CI Scripts
*   **Shell Scripts**: All `.sh` scripts must pass **`shellcheck`** to catch syntax errors and unsafe variable expansions.
*   **GitHub Actions**: All `.github/workflows/*.yml` files must pass **`actionlint`** to ensure valid action syntax.

---

## 4. Testing and CI/CD Expectations

### Unit Testing
*   Any new feature or bug fix must be accompanied by corresponding unit tests under the `tests/` directory.
*   Ensure tests pass locally on the TPU VM before submitting a PR.

### Performance & Baseline Regression Checks
*   For PRs modifying model implementations, kernels, or execution layers, performance must not degrade relative to the established baselines.
*   **Manual Verification**: Use `./scripts/vllm/benchmarking/run_eval_flow.sh` on a development TPU VM to benchmark and verify.
*   **Nightly Checks**: Nightly perf runs evaluate TP8 model checkpoints against regression baselines.

---

## 5. Model Checkpoint Management

*   **Checkpoints location**: Checkpoints used in CI tests or performance evaluations must be stored under `gs://tpu-inference-hf-llm-model-checkpoints/`.
*   **Flat Structure**: Checkpoints should be stored in a flat directory layout (no nested `blobs/` and `snapshots/` subdirectories) to optimize copy time and prevent out-of-disk errors.
*   **GCSFuse Support**: New models must be tested to ensure they support loading from mounted GCSFuse directories as well as direct local copy.
