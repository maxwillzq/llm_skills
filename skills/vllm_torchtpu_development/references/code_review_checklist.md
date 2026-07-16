# Code Review Checklist for torchtpu-vllm

This document outlines the code review criteria and guidelines for the `torchtpu-vllm` repository. Use this checklist when reviewing pull requests (PRs) or preparing code for submission to ensure correctness, performance, consistency, and clean review communication.

---

## PR Review Flow

When reviewing a PR, ensure changes are:
*   **Correct**: Resolves the issue or implements the feature without bugs.
*   **Performant**: Meets baseline performance targets without regressions.
*   **Aligned**: Conforms to repository directory layout and styling rules.
*   **Tested**: Covered by relevant unit tests and valid GCS test checkpoints.

---

## 1. Functionality & Architecture

### Directory & Layer Conventions
- [ ] **Are changes placed in the correct directories?**
  - **`tpu_inference/layers/`**:
    - `common/` for layers and utilities shared across models.
    - `vllm/` for layers used exclusively by vLLM (PyTorch) models.
  - **`tpu_inference/models/`**:
    - `vllm/` for model architectures specific to vLLM (PyTorch) models.
- [ ] **Are package inits present?**
  - Verify that any new subdirectory under `tpu_inference/` contains an `__init__.py` file (enforced by `detect-missing-init` hook).

### Bugs & Correctness
- [ ] **Are edge cases covered?**
  - Handle null/None values, empty input strings, and empty token arrays.
- [ ] **Is error handling implemented?**
  - Graceful degradation or meaningful error messages when TPU compilation or loading fails.

---

## 2. Style, Formatting & Conventions

### Pre-commit Compliance
- [ ] **Have all pre-commit hooks passed?**
  - **Python formatting**: Run `yapf` (Google style) and `isort` for import order.
  - **Lints**: Pass `ruff` checks.
  - **Shell scripts**: Pass `shellcheck` linting.
  - **CI configurations**: Pass `actionlint` check for GitHub Actions YAMLs.
  - **Filenames**: Check for spaces in filenames (must not contain spaces).

### Commit & Licensing (DCO)
- [ ] **Is every commit signed off?**
  - Every commit message must contain a `Signed-off-by: Author Name <email@example.com>` line. Run `git commit -s` when committing.

### Pull Request Title Conventions
- [ ] **Does the PR title use standard classification prefixes?**
  - Recommended prefixes (inspired by [upstream vLLM Contribution Guidelines](https://docs.vllm.ai/en/latest/contributing/)):
    - `[Bugfix]`: For bug fixes.
    - `[CI/Build]`: For build/CI workflow updates.
    - `[Doc]`: For documentation improvements.
    - `[Model]`: For new model implementations or updates (model name in title).
    - `[Kernel]`: For compute kernels (e.g., Pallas or TPU-specific kernels).
    - `[Core]`: For core engine logic changes (e.g., LLMEngine, Scheduler).
    - `[Misc]`: For PRs that do not fit the above categories.

---

## 3. Testing and CI/CD Validation

### Unit Tests
- [ ] **Are there unit tests for the changes?**
  - New features or bug fixes must include unit tests placed under the `tests/` directory.
  - Run and verify tests locally on the TPU VM before submitting.

### Model Checkpoints Verification
- [ ] **Are evaluation checkpoints ready in GCS?**
  - If adding a new model or expanding test configs, verify that the corresponding model checkpoint files are uploaded to the GCS bucket `gs://tpu-inference-hf-llm-model-checkpoints/` in a flat directory layout. Refer to the [GCS Checkpoint Management Guide](managing_checkpoint_bucket.md) for details.

---

## 4. Performance & Baseline Parity

### Baseline Verification
- [ ] **Does the PR introduce performance regressions?**
  - Verify performance metrics (throughput, latency) on a remote TPU VM using `./scripts/vllm/benchmarking/run_eval_flow.sh` against the established baselines.
  - Ensure nightly performance checks pass.

---

## 5. Review Feedback Guidelines (For Reviewers)

When commenting on PRs, use clear severity markers to help authors prioritize updates:

*   **🔴 Blocker**: Critical issue (bugs, regression, DCO sign-off missing, failing tests) that **must** be resolved before merging.
*   **🟡 Important**: Architectural design improvements or code structure issues that should be addressed.
*   **🟢 Nit**: Minor styling preferences, typos, or optional changes.
*   **💡 Suggestion**: Optional ideas for future improvements.
*   **❓ Question**: Seeking clarification on code logic or decisions.
*   **✅ Praise**: Highlight clean code, clever solutions, or good work.

### Communication Tone
*   Be constructive and explain the *why* behind feedback (e.g., "Consider X because it prevents compilation overhead").
