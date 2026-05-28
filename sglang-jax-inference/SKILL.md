---
name: sglang-jax-inference
description: Guidelines for using, debugging, and extending SGL-JAX for high-performance LLM inference on JAX/TPU.
---

# SGL-JAX Inference & Development

This skill provides guidelines for understanding, using, and extending SGL-JAX, a high-performance inference engine optimized for Google TPUs.

## 1. Overview

SGL-JAX is a JAX-based implementation of the SGLang serving framework. It features:
- **High-Throughput Continuous Batching**
- **Radix Tree KV Cache** for prefix sharing.
- **FlashAttention** integration.
- **OpenAI-Compatible API**.

## 2. Core Architecture

SGL-JAX uses a multi-process architecture:
1.  **TokenizerManager** (`python/sgl_jax/srt/managers/tokenizer_manager.py`): Handles text tokenization.
2.  **Scheduler** (`python/sgl_jax/srt/managers/scheduler.py`): Manages request scheduling and batching.
3.  **DetokenizerManager** (`python/sgl_jax/srt/managers/detokenizer_manager.py`): Handles output token decoding.
4.  **ModelRunner** (`python/sgl_jax/srt/model_executor/model_runner.py`): Executes the JAX/Flax model.

## 3. Key JAX/TPU Patterns

When developing or debugging SGL-JAX, keep these patterns in mind:
- **JIT Compilation & Shape Bucketing**: To avoid runtime compilation overhead, SGL-JAX uses shape bucketing for inputs.
- **NNX Graph-State Separation**: Uses `nnx.split()` to handle mutable state (like KV cache) in a functional JAX environment.
- **Pallas Kernels**: Uses custom Pallas kernels for in-place KV cache updates to overcome JAX immutability constraints.

## 4. Common Workflows

### Serving
To launch a server (e.g., for Qwen):
```bash
JAX_COMPILATION_CACHE_DIR=/tmp/jit_cache uv run python -u -m sgl_jax.launch_server \
    --model-path Qwen/Qwen-7B-Chat \
    --device=tpu \
    --tp-size=4 \
    --mem-fraction-static=0.8
```

### Testing
Run the full test suite:
```bash
python test/srt/run_suite.py
```

### Benchmarking
Run throughput tests:
```bash
uv run python -m sgl_jax.bench_serving --backend sgl-jax --dataset-name random --num-prompts 100
```

## 5. Developer Guidelines

### Adding New Models
- Model definitions are located in `python/sgl_jax/srt/models/` (e.g., `qwen.py`, `llama.py`).
- To add a new model, implement it in this directory, ensuring it uses JAX/Flax and supports tensor parallelism (sharding).
- Register the model in the appropriate factory or registry (usually in `models/__init__.py` or inferred by name).

### Debugging
- **OOM Errors**: Reduce `--max-prefill-tokens` or `--mem-fraction-static`.
- **Compilation Timeout**: Ensure `JAX_COMPILATION_CACHE_DIR` is properly configured.
- **Low Throughput**: Verify `--tp-size` matches your TPU configuration.
