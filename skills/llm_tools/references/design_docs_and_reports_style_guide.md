# Design Documents & Technical Reports Style Guide

This guide establishes the mandatory writing and organizational standards for engineering design documents, Request for Comments (RFCs), one-pagers, post-mortem/benchmark reports, and pull request descriptions.

---

## 1. Core Writing Invariants

### 1.1 Strict Prohibition of Emojis
* **Rule**: Never use emojis (e.g., rocket, lightning, checkmark, cross, party, lightbulb, chart, broom, target, etc.) in design documents, RFCs, PR descriptions, commit messages, or technical reports.
* **Rationale**: Emojis appear unprofessional, distract from technical content, and degrade readability in text-based diffs and terminal tools.
* **Alternative**: Use standard markdown typography, clean tables, bullet points, and plain text markers (e.g., `PASSED`, `FAILED`, `[Test 1]`). Use ASCII box-drawing characters (`┌`, `─`, `│`, `└`, `▼`) exclusively for architecture flowcharts.

### 1.2 Elimination of Fluff, Buzzwords, and Hyperbole
* **Strict Prohibition of Grandstanding and Promotional Jargon ("拒绝大话套话")**:
  * Never use sensationalist adjectives: *"surgical stack"*, *"catastrophic collapse"*, *"deadly trap"*, *"slashed bubbles"*, *"quantum leap"*, *"blazing fast"*.
  * Never use consulting or business jargon in technical RFCs: *"harvesting low-hanging fruits"*, *"pragmatic, high-velocity strategy"*, *"paradigm shift"*, *"synergy"*.
  * Never anthropomorphize hardware: avoid *"starving the compute cores"*, use *"leaving compute cores idle"*.
* **Use precise, objective systems engineering language**:
  * Instead of: *"Our six-step surgical stack completely crushed the latency bottleneck..."*
  * Write: *"Through a six-stage optimization pipeline, we eliminated host-side memory allocations and fused elementwise unpacking, reducing per-token latency from 4.04 ms to 1.03 ms (-74.5%)."*
  * Instead of: *"We adopted a pragmatic high-velocity strategy to harvest low-hanging fruits rather than rewriting in Pallas assembly..."*
  * Write: *"Rather than implementing custom Pallas TPU kernels, optimizations were implemented across host memory management and XLA compiler fusions using standard PyTorch/XLA abstractions."*
  * Preferred: *"This optimization eliminates redundant Python bytecode evaluation, reducing cold compilation latency by 2.30x (-56.6%)."*
  * Preferred: *"Sub-function compilation partitions the StableHLO graph into N disconnected executables, increasing HBM memory traffic and preventing cross-layer operator fusion."*

### 1.3 Strict Division of Labor: Executive Main Body vs. Heavy Appendix ("深入浅出，主附分离")
* **Main Body Accessibility ("深入浅出，简洁明了")**:
  * The main text must be readable end-to-end in 3 to 5 minutes by Tech Leads and Staff+ reviewers.
  * Code snippets in the main body must be **high-contrast and minimal (3 to 6 lines max)**, displaying strictly the *Anti-Pattern* vs. *Optimized* diff. Never dump full production class implementations, multi-line row loops, or schema definitions into the main body.
* **Appendix Offloading Rule**:
  * Offload all exhaustive assets to labeled Appendices: full step-by-step git diffs, complete JSON/AST grammar specs, verification test suites, benchmark harness code, and profiling traces.
  * Main body subsections must provide explicit markdown links to their corresponding Appendix (e.g., `*(Full code diff: [Appendix B.1](#appendix-b1))*`).

### 1.4 Data-Driven and Verifiable Metrics
* **Never use vague quantifiers** (*"much faster"*, *"insignificant overhead"*, *"drastically improved"*).
* **Always provide exact, reproducible measurements**:
  * Cold compilation duration before and after (e.g., `105.68s -> 45.83s`).
  * Relative speedup and percentage delta (`2.30x speedup / -56.6% latency reduction`).
  * Hardware environment, pod topology, chip count, and test scripts (e.g., `Cloud TPU v7x-8, 8 chips / 16 cores, scripts/vllm/integration/run_compilation_cache_e2e.sh`).
* Distinguish between **empirically measured** numbers and **theoretical projections**.

### 1.5 Self-Contained and Verified Code Snippets
* Code examples in design docs must be **syntactically valid, self-contained, and tested**:
  * Do not leave unused imports, dummy variables, or dead code.
  * Use actual hardware backend and device identifiers (e.g., `backend="tpu"` and `device="tpu"` in TorchTPU instead of legacy `openxla`).
  * Accompany code snippets with exact output shapes or assertion checks.

---

## 2. Standard Structural Template for Design Docs / RFCs

A high-quality technical RFC or One-Pager should follow a top-down executive structure:

```
1. Title & Metadata (Author, Date, Status, Target Systems)
2. Problem Context & Architectural Questions (Pain point & root cause in 1-2 paragraphs)
3. Underlying Mechanism / Theory (Why systems behave this way, with minimal verified code)
4. Failure Modes / Counterexamples (Why intuitive/naive fixes fail, with concrete code)
5. Architectural Solutions: Optimization Stages (Direct engineering evolution)
6. Lessons Learned & Upstream Roadmap (Universal rules vs Case specializations + Compact PR stack)
---
Appendices (Offload all secondary details here to keep the main text executive and crisp):
- Appendix A: Subsystem Architecture & Flowcharts
- Appendix B: Full Implementation Details & Code Modifications (Complete git diffs)
- Appendix C: Grammar / Schema Verification Oracle Specifications
- Appendix D: Full Hardware Benchmark Tables & Methodology
- Appendix E: Quantitative Diagnostics & Bubble Calculations
- Appendix F: Upstream Pull Request & Commit Lineage
- Appendix G: Test Suite & Real-Hardware Verification Logs
```

### 2.1 Anti-Patterns in Structural Organization
* **Prohibit Conversational FAQ Sections**:
  * Avoid conversational `Frequently Asked Questions (FAQ)` sections. Counterexamples and naive compilation questions belong in **Section 4 (Failure Modes & Counterexamples)**. Architectural invariants belong in **Section 6 (Lessons Learned)**.
* **Prohibit Strawman and Redundant Tradeoff Tables**:
  * Do NOT create comparison tables that merely duplicate bullet points in the same section.
  * Do NOT create strawman tradeoff tables comparing against unbuilt hypothetical solutions (e.g., comparing against a hypothetical unwritten kernel). If an alternative path was rejected early, state the technical rationale in 1–2 sentences and keep the section focused on the real solution.
* **Keep Upstream Roadmaps Compact**:
  * Roadmaps in the main body should be a concise bullet list of PR numbers, commit links, and 1–2 immediate future milestones, referencing Appendix F for detailed changelogs.

---

## 3. Pre-Publication Review Checklist

Before finalizing any design doc, RFC, or PR description, verify:

- [ ] Are all emojis removed?
- [ ] Are all grandstanding buzzwords, promotional marketing phrases, and AI clichés ("surgical", "catastrophic", "harvesting low-hanging fruits", "slashed") eliminated?
- [ ] Are all benchmark numbers verified with explicit units, deltas, and test hardware?
- [ ] Are code snippets runnable with real backend names and zero dead variables?
- [ ] Is the main body readable in 3–5 minutes with code snippets <= 6 lines, and all complete diffs/schemas pushed to Appendices?
- [ ] Are conversational FAQs and redundant/strawman tradeoff tables avoided?
- [ ] Is the roadmap a compact PR list referencing the commit history appendix?
