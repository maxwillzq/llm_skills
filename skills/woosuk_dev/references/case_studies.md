# Case Studies in Woosuk Kwon Serving Systems

---

## Case Study 1: The BlockSpaceManager & Physical Block Allocator
**Domain**: vLLM Core Memory Subsystem (`vllm/core/block_manager.py`)

### The Architecture:
Woosuk decomposed memory management into two distinct layers mirroring an OS kernel:
1. **`BlockAllocator`**: Manages the physical GPU/CPU memory pools. Keeps a list of free block IDs (`free_blocks: Deque[Block]`). Handles allocation, deallocation, and reference counting (`ref_count`).
2. **`BlockSpaceManager`**: Manages the virtual-to-physical block table for each `Sequence` and `SequenceGroup`.
   - `can_allocate(seq_group)`: Checks if there are enough free blocks to start prefill.
   - `can_append_slots(seq_group)`: Checks if running sequences can allocate new blocks for the next token step.
   - `append_slots(seq)`: If the current block has free capacity, increments slot count. If full, allocates a new physical block from the allocator and appends it to `block_table`.

---

## Case Study 2: Iteration-Level Continuous Batching Scheduler
**Domain**: vLLM Core Scheduler (`vllm/core/scheduler.py`)

### The State Machine:
Requests transition across 3 queues:
- `WAITING`: Arrived requests waiting for initial prefill allocation.
- `RUNNING`: Actively decoding or prefilling in the current GPU batch.
- `SWAPPED`: Preempted requests whose KV blocks reside in host CPU memory.

### The Invariant:
In each step `schedule()`:
1. Prioritize `RUNNING` sequences: ensures requests nearing completion finish as fast as possible to free memory.
2. If memory allows, swap in requests from `SWAPPED` to minimize latency.
3. If memory still allows and no requests were preempted, admit new requests from `WAITING`.
4. If blocks are depleted during step 1, preempt the most recently scheduled `RUNNING` sequences (either swap to CPU or evict to `WAITING` for recomputation).
