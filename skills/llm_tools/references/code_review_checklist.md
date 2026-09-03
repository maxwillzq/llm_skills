# Code Review Checklist for vllm-torchtpu

This document outlines the code review criteria and guidelines for the `vllm-torchtpu` repository. Use this checklist when reviewing pull requests (PRs) or preparing code for submission to ensure correctness, performance, consistency, and clean review communication.

---

## PR Review Flow

When reviewing a PR, ensure changes are:
*   **Correct**: Resolves the issue or implements the feature without bugs or unintended side effects.
*   **Performant**: Meets baseline performance targets without latency/throughput regressions.
*   **Aligned**: Conforms to repository directory layout, naming conventions, and styling rules.
*   **Tested**: Covered by relevant unit/integration tests and verified against valid model checkpoints.
*   **CI-Gated**: Validated by Buildkite presubmit CI with the `ready` label applied.

---

## 1. Functionality & Architecture

### Directory & Layer Conventions
- [ ] **Are changes placed in the correct directories?**
  - **`src/vllm_torchtpu/layers/`**:
    - `common/`: Shared layers, attention interfaces, sequence layout, and quantization utilities across models.
    - `vllm/`: Layer implementations and custom operators specific to vLLM (PyTorch) models (e.g. attention, fused MoE, linear, router top-k, sampling, token padding).
  - **`src/vllm_torchtpu/models/`**:
    - `vllm/`: Model architectures and model wrapper contexts specific to vLLM (e.g. DeepSeek-V4, Kimi-K3).
- [ ] **Are package inits present?**
  - Verify that any new subdirectory under `src/vllm_torchtpu/` contains an `__init__.py` file (enforced by `detect-missing-init` hook).

### Bugs & Correctness
- [ ] **Are edge cases covered?**
  - Handle null/None values, empty input strings, zero batch sizes, and empty token arrays.
- [ ] **Is error handling implemented?**
  - Graceful degradation or meaningful error messages when TPU compilation, device initialization, or weight loading fails.
- [ ] **Are device-specific workarounds documented?**
  - Any monkey-patches or workarounds for libtpu/Pallas/Dynamo are documented and gated (e.g. in `src/vllm_torchtpu/env_override.py`).

---

## 2. Style, Formatting & Conventions

### Pre-commit Compliance
- [ ] **Have all pre-commit hooks passed?**
  - **Python formatting**: Run `yapf` (Google style) and `isort` for import order.
  - **Python lints**: Pass `ruff` checks (`--output-format github --fix`).
  - **Static type checking**: Pass `pyrefly check` (preset `basic`).
  - **C++ / CUDA formatting**: Pass `clang-format` for native C++ / CUDA kernels.
  - **Markdown formatting**: Pass `pymarkdown` linting.
  - **Shell scripts**: Pass `shellcheck` linting.
  - **CI configurations**: Pass `actionlint` check for GitHub Actions YAMLs.
  - **Package inits**: Pass `detect-missing-init` check across `src/vllm_torchtpu`.
  - **Filenames**: Pass `check-filenames` (filenames must not contain spaces).
  - **General hygiene**: Pass `check-yaml`, `end-of-file-fixer`, and `trailing-whitespace`.

### Commit & Licensing (DCO)
- [ ] **Is every commit signed off?**
  - Every commit message must contain a `Signed-off-by: Author Name <email@example.com>` line.
  - Handled automatically by the pre-commit `signoff-commit` hook (`pre-commit install --hook-type commit-msg`) or manually via `git commit -s`.
  - If DCO check fails on GitHub during the pre-public phase, run `git commit --amend --signoff --no-edit && git push origin HEAD --force-with-lease`, or use the UI override "Set DCO to PASS".

### Pull Request Title Conventions
- [ ] **Does the PR title use standard classification prefixes?**
  - Recommended prefixes:
    - `[Bugfix]`: For bug fixes.
    - `[CI/Build]`: For build, CI pipeline, or Docker workflow updates.
    - `[Doc]`: For documentation improvements.
    - `[Model]`: For new model implementations or updates (model name in title).
    - `[Kernel]`: For compute kernels (e.g., Pallas or TPU-specific kernels).
    - `[Core]`: For core engine logic changes (e.g., LLMEngine, Scheduler, Runner).
    - `[fixit]`: For Fixit maintenance tasks, cleanups, and technical debt.
    - `[Misc]`: For PRs that do not fit the above categories.

---

## 3. Testing and CI/CD Validation

### Presubmit CI (`ready` Label)
- [ ] **Is the `ready` label applied to the PR?**
  - Presubmit test pipelines on Buildkite only execute on PRs labeled `ready`:
    ```bash
    gh pr edit <PR_NUMBER> --add-label ready
    ```
  - Without this label, CI jobs fail fast within seconds (`Missing 'ready' label`).

### Unit Tests
- [ ] **Are there unit tests for the changes?**
  - New features or bug fixes must include unit tests placed under the `tests/` directory.
  - Run and verify tests locally or in the dev container before submitting:
    ```bash
    pytest -v -m "not nightly and not multichip" tests/
    ```

### Model Checkpoints Verification
- [ ] **Are evaluation checkpoints ready in GCS?**
  - If adding a new model or expanding test configs, verify that the corresponding model checkpoint files are uploaded to the GCS bucket `gs://tpu-inference-hf-llm-model-checkpoints/` in a flat directory layout. Refer to the [GCS Checkpoint Management Guide](managing_checkpoint_bucket.md) for details.

---

## 4. Performance & Baseline Parity

### Baseline Verification
- [ ] **Does the PR introduce performance regressions?**
  - Verify PR guard configs using `./scripts/vllm/benchmarking/run_benchmarks.sh`:
    ```bash
    ./scripts/vllm/benchmarking/run_benchmarks.sh --config qwen3-coder-30b-fp8-tp8-ep
    ```
  - Check regression metrics against baselines:
    ```bash
    python3 scripts/vllm/benchmarking/check_regression.py \
      --mode perf \
      --results-dir <DIR> \
      --baseline scripts/vllm/benchmarking/baselines/perf/<config>.baseline.json
    ```
  - For full evaluation flows, use `./scripts/vllm/benchmarking/run_eval_flow.sh`.

---

## 5. Review Feedback & Pre-Merge Guidelines

### Review Feedback Severity Markers
When commenting on PRs, use clear severity markers to help authors prioritize updates:

*   **🔴 Blocker**: Critical issue (bugs, regressions, DCO sign-off missing, failing tests) that **must** be resolved before merging.
*   **🟡 Important**: Architectural design improvements or code structure issues that should be addressed.
*   **🟢 Nit**: Minor styling preferences, typos, or optional changes.
*   **💡 Suggestion**: Optional ideas for future improvements.
*   **❓ Question**: Seeking clarification on code logic or decisions.
*   **✅ Praise**: Highlight clean code, clever solutions, or good work.

### Communication Tone
*   Be constructive and explain the *why* behind feedback (e.g., "Consider X because it prevents compilation overhead").

### Pre-Merge Verification Checklist (Guarded Merge)
Before merging any PR into `main`:
- [ ] Review approval verified: `latestReviews` has at least 1 `APPROVED`.
- [ ] Discussions checked: All comment threads marked as resolved.
- [ ] Presubmit CI verified: `gh pr checks <PR_NUMBER>` returns **ALL GREEN**.
- [ ] Execute guarded merge:
  ```bash
  [ "$(gh pr view <PR_NUMBER> --json latestReviews | jq '[.latestReviews[] | select(.state == "APPROVED")] | length')" -gt 0 ] && gh pr checks <PR_NUMBER> && gh pr merge <PR_NUMBER> --squash --delete-branch
  ```
