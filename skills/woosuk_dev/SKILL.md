---
name: woosuk_dev
description: LLM serving systems architecture, PagedAttention virtual memory KV cache management, continuous batching, and iteration-level scheduling distilled from Woosuk Kwon's foundational vLLM design.
---

# Woosuk Kwon Engineering Standard: Virtual Memory Paging & LLM Serving Systems

This skill distills the systems architecture, memory management, and iteration-level scheduling principles extracted from **Woosuk Kwon's foundational work as creator and lead author of vLLM** (UC Berkeley SkyLab, PagedAttention).

When designing high-throughput LLM serving engines, managing KV cache memory under dynamic generation lengths, or building request schedulers:
> **"What would Woosuk Kwon do?"**
> 1. Treat GPU memory like an Operating System: decouple logical token sequences from physical memory blocks using Page Tables (PagedAttention).
> 2. Eliminate internal and external memory fragmentation: allocate fixed-size blocks (e.g. 16 or 32 tokens) on-demand.
> 3. Implement iteration-level continuous batching: schedule at the token level, not the request level.
> 4. Support stateful preemption and eviction: swap inactive blocks to CPU host memory or recompute tokens deterministically.
> 5. Enable zero-copy prefix caching: share prompt KV blocks across requests using cryptographic or structural block hashing.

---

## 🏛️ The 5 Pillars of the Woosuk Kwon Serving Mindset

### Pillar 1: PagedAttention & Virtual Memory Abstraction (分页内存与逻辑物理映射)
- **The Fragmentation Crisis**:
  - In naive LLM serving, engines pre-allocate contiguous memory for `max_model_len` (e.g. 8k–128k tokens). Because generation length is unpredictable, 60%–80% of memory is wasted as internal fragmentation, or reserved for requests that terminate early.
- **The Block & Page Table Invariant**:
  - Partition KV cache into fixed-size physical blocks (`block_size`, typically 16 or 32 tokens).
  - Every request maintains a logical-to-physical block table (`block_table: List[int]`).
  - Physical blocks do not need to be contiguous in physical GPU HBM. PagedAttention kernels read blocks via dynamic pointer indirection:
    $$\text{Physical Address} = \text{block\_table}[\lfloor \text{token\_idx} / \text{block\_size} \rfloor] \times \text{block\_stride} + (\text{token\_idx} \bmod \text{block\_size})$$
- **Result**: Memory waste drops to $<4\%$ (only within the very last block of a sequence).

---

### Pillar 2: Continuous Batching & Iteration-Level Scheduling (连续批处理与迭代级调度)
- **Token-Level Scheduling Loop**:
  - Never wait for an entire batch to complete generation before adding new requests.
  - At every decoding iteration (step):
    1. Check completed sequences (EOS token or stop sequence reached); immediately free their allocated physical blocks.
    2. Check available physical blocks: if sufficient, allocate one slot for each running sequence to generate the next token.
    3. If new capacity is available, admit pending requests from the `WAITING` queue into `RUNNING` (Prefill phase).
- **Batch Composition**:
  - A single step batch can seamlessly mix sequences in Prefill (processing prompt tokens) and sequences in Decode (generating single tokens).

---

### Pillar 3: Graceful Preemption, Swapping & Recomputation (抢占、换页与重计算)
- **Overcommitment & OOM Immunity**:
  - When GPU physical memory is exhausted during generation, the engine must **never crash with CUDA OOM**.
- **The Preemption Protocol**:
  - Identify lowest-priority sequence groups in `RUNNING`.
  - **Mode A (Swap-to-CPU)**: Copy physical GPU blocks to CPU RAM via asynchronous host-device streams (`swap_out`), moving request to `SWAPPED` queue. When GPU blocks free up, `swap_in`.
  - **Mode B (Recompute)**: Free all KV blocks except the original prompt, return request to `WAITING`, and re-prefill when memory recovers. Recomputation is often faster than host-device PCIe transfers for short prompts.

---

### Pillar 4: Zero-Copy Prefix Caching (Hash-Based Block Sharing)
- **Structural Block Hashing**:
  - Calculate SHA256 / 64-bit hash of token sequences spanning each block:
    $$H_i = \text{Hash}(H_{i-1}, \text{tokens}[i \cdot B : (i+1) \cdot B])$$
- **Copy-on-Write (CoW)**:
  - If multiple requests share the same system prompt, document context, or few-shot examples, point their block tables to the same physical block with an incremented reference count (`ref_count > 1`).
  - When a sequence mutates the final non-full block during generation, trigger Copy-on-Write to duplicate only the mutated block.

---

### Pillar 5: Static Buffering for CUDA Graph Capture
- **Taming CUDA Graph Dynamic Inputs**:
  - CUDA Graphs eliminate CPU launch overhead (~10–20µs per kernel) during decode, but require completely fixed tensor shapes and memory addresses.
- **The Static Block Table Pattern**:
  - Pre-allocate maximum batch size block tables (`max_batch_size x max_blocks_per_seq`) on GPU.
  - Before launching the graph, copy the current iteration's dynamic block IDs into the static buffer via a fast gather kernel. Never re-capture CUDA graphs per iteration.

---

## 🚦 The Woosuk Kwon Serving Checklist

Before implementing or modifying LLM serving runtime code:

| # | Question | Woosuk Kwon Standard |
|---|---|---|
| 1 | **Memory Allocation** | Is memory pre-allocated contiguously per request, or dynamically managed via fixed-size blocks? |
| 2 | **Fragmentation** | Does the engine suffer from internal fragmentation when output length is short? |
| 3 | **Scheduling Granularity** | Can requests enter and exit the batch on individual token boundaries? |
| 4 | **OOM Defense** | Does the scheduler handle sudden memory exhaustion via preemption/swapping without crashing? |
| 5 | **Prefix Reuse** | Are shared prompt prefix blocks deduplicated in GPU memory via reference counting? |
| 6 | **CUDA Graph Safety** | Are dynamic input metadata (block tables, sequence lengths) routed through pre-allocated static buffers? |

---

## 📚 References & Case Studies

- [Case Studies: BlockSpaceManager, Continuous Batching, & CUDA Graphs](references/case_studies.md)
