---
name: sglang_jax_inference_development
description: Guidelines for using, debugging, and extending SGL-JAX for high-performance LLM inference on JAX/TPU.
---

# SGL-JAX Inference & Development

This skill provides guidelines for understanding, using, and extending SGL-JAX.

## 1. Overview
SGL-JAX is a high-performance JAX-based inference engine for LLMs on TPUs, featuring continuous batching, Radix Tree KV cache, and OpenAI API compatibility.

## 2. Architecture & JAX Patterns
SGL-JAX uses a multi-process architecture (Tokenizer, Scheduler, ModelRunner) and specific JAX patterns (NNX Graph-State separation, Pallas kernels for in-place updates).
- See [architecture.md](references/architecture.md) for details.

## 3. Common Workflows
- **Serving**: Launch the server with `sgl_jax.launch_server`.
- **Benchmarking**: Use `sgl_jax.bench_serving`.
- **Testing**: Run `python test/srt/run_suite.py`.
- **Docker Dev**: See [docker_development.md](references/docker_development.md) for setup instructions.
- See [serving.md](references/serving.md) for example commands.

## 4. Developer Guidelines
- **Adding Models**: Implement in `python/sgl_jax/srt/models/` (e.g., `qwen.py`).
- **Debugging**: Adjust `--max-prefill-tokens` or `--mem-fraction-static` for OOM.

## 5. Configuration
- **TPU IP & GCS Bucket**: Check the `config.json` file at the root of the `llm_skills` repository for user-specific configuration.

---
*Refer to the official documentation in `<local_projects_dir>/sglang-jax/docs/` (see `local_projects_dir` in `config.json`) for the full source of truth.*
