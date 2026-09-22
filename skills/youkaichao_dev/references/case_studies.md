# Case Studies in youkaichao GPU Optimization

---

## Case Study 1: Zero-Overhead Speculative Decoding Pipelines
**Commits**: `#10007`, `#10177`, `#23041`  
**Domain**: vLLM Speculative Decoding Subsystem

### The Architecture:
In speculative decoding, a lightweight model (or MLP speculator) proposes $K$ draft tokens per step, and the primary model verifies all $K$ candidates in a single forward execution.
1. **Draft Generation**: Run draft forward pass asynchronously on a separate stream, outputting candidate token sequences and associated draft KV cache blocks.
2. **Target Verification (Tree / Flat Attention)**: The target model scores all candidates in parallel using a combined verification mask.
3. **Branch Rejection & KV Rollback**:
   - Count accepted tokens $M \le K$.
   - For rejected tokens ($K - M$), simply rewind the `Sequence` logical length:
     ```python
     seq.data.output_token_ids = seq.data.output_token_ids[:accepted_len]
     # Trim logical block table; free trailing unneeded physical blocks:
     block_manager.trim_physical_blocks(seq, accepted_len)
     ```
   - Avoids memory reallocation, copy operations, or CUDA graph invalidations.

---

## Case Study 2: Custom CudaMemoryPool vs PyTorch Allocator
**Commit**: `2ce95a761`  
**Title**: *Auto-disable expandable_segments around cumem memory pool (#40812)*

### The Collision:
When vLLM allocates large contiguous virtual address spaces via CUDA driver VMM APIs (`cuMemAddressReserve`, `cuMemMap`) for PagedAttention KV caches, PyTorch's internal caching allocator feature `expandable_segments` (which relies on splitting virtual segments) attempted to map into conflicting address regions. This triggered memory corruption and unpredictable `CUDA error: invalid argument`.

### The youkaichao Resolution:
Explicitly detect and disable `expandable_segments` during virtual memory pool initialization, guaranteeing clean separation between the PyTorch tensor memory space and the low-level PagedAttention virtual block pool.
