# `lj` (llm_jobs) CLI & Performance Toolchain Reference

> [!NOTE]
> Primary and active documentation is maintained directly within the [`llm_jobs`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs) repository under `docs/`. This page acts as a centralized directory to navigate those core documents.

---

## 📚 Primary `llm_jobs` Documentation Index

| Topic | Document Link | Description |
| :--- | :--- | :--- |
| **CLI Complete Reference** | [`03_cli_complete_reference.md`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/docs/03_cli_complete_reference.md) | Full manual of all `lj` subcommands (`job`, `trace`, `sync`, `diff`, `perfetto`). |
| **Profiling & Trace Analysis Guide** | [`structured_decoding_profiling_guide.md`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/docs/structured_decoding_profiling_guide.md) | Deep profiling guide: Trace targeting, Perfetto UI, A/B diffing (`-f`), and TPU hardware bubble diagnostics. |
| **Performance Optimization Journey** | [`structured_decoding_optimization_journey.md`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/docs/structured_decoding_optimization_journey.md) | Step-by-step optimization log (PR #596 baseline, PR #610 low-hanging fruits, and CDK trace importing). |
| **Fast ML Workflow** | [`01_fast_ml_workflow.md`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/docs/01_fast_ml_workflow.md) | Iterative GKE/GCE/CDK job launch and profiling loop. |
| **Hardware Optimization Guide** | [`02_perf_optimization_guide.md`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/docs/02_perf_optimization_guide.md) | TPU execution graphs, kernel breakdown, and bubble elimination. |

---

## ⚡ Quick Command Cheatsheet

```bash
# 1. Trace Discovery & Management
lj trace list -n 20                          # List all GCS & local profiles
lj trace tag <target> <alias>                # Create semantic alias tag (e.g. lj trace tag jrh44:json opt-v1)

# 2. CDK Trace Bridge
lj trace import-cdk <JOB_ID> [ALIAS]         # Import Perfetto trace from CDK (e.g. lj trace import-cdk j-37b59b4b base)

# 3. A/B Performance Diff
lj trace diff <trace_A> <trace_B>            # Compare 2 traces (e.g. lj trace diff base opt)
lj trace diff base opt -f "structured,MapDmaBuffer,argmax" # Filter by specific kernels / DMA transfers

# 4. Interactive Visual Profiling
lj trace perfetto <target>                   # Open interactive Perfetto UI in browser
lj trace xprof <target>                      # Generate internal Google XProf link
```

---

## 🛠️ Main Source Locations
* CLI Entrypoint: [`llm_jobs/core/cli.py`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/core/cli.py)
* Trace Manager: [`llm_jobs/core/trace_manager.py`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/core/trace_manager.py)
* Perf Analyzer: [`llm_jobs/core/perf_analyzer.py`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/core/perf_analyzer.py)
* Standalone Benchmark Script: [`llm_jobs/jobs/scripts/benchmark_structured_decoding.py`](file:///usr/local/google/home/johnqiangzhang/projects/llm_jobs/jobs/scripts/benchmark_structured_decoding.py)
