# SGL-JAX Serving & Benchmarking References

Derived from `docs/basic_usage/qwen.md`.

## Launching the Server

Example for Qwen-7B-Chat on TPU:

```bash
JAX_COMPILATION_CACHE_DIR=/tmp/jit_cache uv run python -u -m sgl_jax.launch_server \
    --model-path Qwen/Qwen-7B-Chat \
    --trust-remote-code \
    --dist-init-addr=0.0.0.0:10011 \
    --nnodes=1 \
    --tp-size=4 \
    --device=tpu \
    --random-seed=3 \
    --node-rank=0 \
    --mem-fraction-static=0.8 \
    --max-prefill-tokens=8192 \
    --download-dir=/tmp \
    --dtype=bfloat16 \
    --skip-server-warmup
```

### Key Flags:
- `--mem-fraction-static`: Set to `0.8` for optimal TPU memory utilization.
- `--attention-backend fa`: Use FlashAttention backend.
- `--tp-size`: Match your TPU core count.

## Benchmarking

### Throughput Testing
```bash
uv run python -m sgl_jax.bench_serving \
    --backend sgl-jax \
    --dataset-name random \
    --num-prompts 100 \
    --random-input 512 \
    --random-output 128 \
    --max-concurrency 8 \
    --random-range-ratio 1 \
    --warmup-requests 0
```
