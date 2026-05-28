# SGL-JAX Architecture References

Derived from `docs/architecture/project-core-structure.md`.

## Core Components

SGL-JAX adopts a multi-process architecture with three core components:

1.  **TokenizerManager** (`python/sgl_jax/srt/managers/tokenizer_manager.py`): Runs in the main process, handles text tokenization.
2.  **Scheduler** (`python/sgl_jax/srt/managers/scheduler.py`): Runs in a subprocess, manages request scheduling, batching, and model forward passes.
3.  **DetokenizerManager** (`python/sgl_jax/srt/managers/detokenizer_manager.py`): Runs in a subprocess, handles output token decoding.

## Key Files to Know

-   **Engine**: `python/sgl_jax/srt/entrypoints/engine.py`
-   **HTTP Server**: `python/sgl_jax/srt/entrypoints/http_server.py` (OpenAI compatible).
-   **ModelRunner**: `python/sgl_jax/srt/model_executor/model_runner.py` (Handles JIT and padding).
-   **RadixCache**: `python/sgl_jax/srt/mem_cache/radix_cache.py` (Prefix caching).

## JAX/TPU Specifics

-   **NNX Graph-State Separation**: Uses `nnx.split()` to separate static computation graphs from mutable state (like KV cache).
-   **Pallas Kernels**: Custom Pallas kernels for efficient in-place cache updates, overcoming JAX's immutability constraints.
-   **Shape Bucketing**: Strategic input shape bucketing to minimize compilation variants.
