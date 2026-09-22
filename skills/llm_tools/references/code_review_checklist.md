# Code Review Checklist for vllm-torchtpu

This document outlines the code review criteria and guidelines for the `vllm-torchtpu` repository. Use this checklist when reviewing pull requests (PRs) or preparing code for submission to ensure correctness, performance, consistency, and clean review communication.

---

## PR Review Flow

When reviewing a PR, ensure changes are:
*   **Correct**: Resolves the issue or implements the feature without bugs or unintended side effects.
*   **Performant**: Meets baseline performance targets without latency/throughput regressions.
*   **Aligned**: Conforms to repository directory layout, naming conventions, and styling rules.
*   **Tested**: Covered by relevant unit/integration tests with adequate edge case assertions.
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
### Code Smell & Architectural Anti-Pattern Inspection
During review, look beyond basic syntax and verify that changes do not introduce insidious software smells:

- [ ] **Contract & State Inconsistency (🔴 Blocker)**:
  - **Non-Idempotent Operations / Return Divergence**: Does a function return different data structures, shapes, or states depending on internal caching, execution order, or call count? (Internal caching optimizations must remain 100% invisible and transparent to callers).
  - **Hidden Side Effects & Temporal Coupling**: Does invoking method `A` secretly mutate global/class state that method `B` implicitly depends on?
- [ ] **Leaky Abstraction & Inappropriate Intimacy (🟡 Important)**:
  - **Layer Inversion & Upward Coupling**: Does a generic high-level manager, scheduler, or orchestrator inspect the internal structure, sub-components, or private flags of its child objects (e.g. `hasattr`, deep member probing)? (Respect the Law of Demeter; components must manage their own readiness).
  - **Shotgun Surgery**: Does adding or modifying a single behavior require small edits scattered across multiple unrelated modules?
- [ ] **Verification & Test Hygiene (🟡 Important)**:
  - **Silent Assertion Erosion**: Are assertions, thresholds, or error boundaries being silently loosened without documented technical/mathematical justification? (Never weaken a test guardrail just to force CI green).
  - **Testing the Implementation, Not Behavior**: Does the test over-assert internal private state or mock out the very logic under test, making harmless refactorings fragile?
- [ ] **Code Simplicity & Hygiene (🟢 Nit / 💡 Suggestion)**:
  - **Premature / Obfuscated Optimization**: Does the change introduce complex micro-optimizations that sacrifice readability before proving a bottleneck via profiler data?
  - **Magic Values & Dead Code**: Are there unexplained literals, commented-out dead code blocks, or unused parameters left behind?

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

### Presubmit CI (`ready` Label & Verification)
- [ ] **Is the `ready` label applied to the PR?**
  - Presubmit test pipelines on Buildkite only execute on PRs labeled `ready`:
    ```bash
    gh pr edit <PR_NUMBER> --add-label ready
    ```
  - Without this label, CI jobs fail fast within seconds (`Missing 'ready' label`).
- [ ] **Are CI checks genuinely passing (Authoritative Source)?**
  - Never infer CI state from local runs or assume pending checks will pass. Confirm actual status:
    ```bash
    gh pr checks <PR_NUMBER>
    ```
  - If Buildkite or GitHub Actions fail, triage logs directly without scrolling through full logs:
    ```bash
    # View only failing steps in GitHub Actions
    gh run view <RUN_ID> --log-failed

    # Or fetch & clean Buildkite failure logs and artifacts (if llm_tools is available)
    python3 <path-to-llm_tools>/scripts/fetch_buildkite_pr.py <PR_NUMBER>
    ```

### Unit Tests & Test Hygiene
- [ ] **Are there unit tests for the changes?**
  - New features or bug fixes must include unit tests placed under the `tests/` directory.
  - Run and verify tests locally or in the dev container before submitting:
    ```bash
    pytest -v -m "not nightly and not multichip" tests/
    ```
- [ ] **Has the test been observed failing first (Red-Green Verification)?**
  - For bug fixes, verify that the test fails against the unpatched code, and passes once the fix is applied. ("A test that has never been red is not evidence.")

---

## 4. Performance & Baseline Parity (For Performance-Critical PRs)

> [!NOTE]
> Standard PRs are automatically guarded by Buildkite's Perf CI pipeline. Manual benchmarking is only required when modifying compute kernels, attention mechanisms, or core scheduling paths.

### Baseline Verification
- [ ] **Does the PR introduce performance regressions?**
  - If manual benchmark verification is needed (requires TPU environment):
    ```bash
    ./scripts/vllm/benchmarking/run_benchmarks.sh --config <CONFIG>  # e.g. qwen3-coder-30b-fp8-tp8-ep
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
