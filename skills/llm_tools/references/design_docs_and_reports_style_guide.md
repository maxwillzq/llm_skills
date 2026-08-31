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

### 1.5 Unit Formatting and Intranet Auto-Link Prevention ("单位斜杠空格法则")
* **Rule**: When writing compound engineering units with slashes (such as milliseconds per step, milliseconds per token, or tokens per second), **always place spaces around the slash**:
  * Write: `ms / step`, `ms / tok`, `tok / s`
  * Avoid: `ms/step`, `ms/tok`, `tok/s`
* **Rationale**:
  * In corporate Google environments, Google Docs and internal Markdown parsers treat `<word>/<path>` (e.g., `ms/step`, `ms/tok`) as an internal intranet URL because `ms` is a registered corporate host (`ms.corp.google.com`).
  * Without spaces, Google Docs automatically converts `ms/step` into an unwanted corporate hyperlink (`https://ms.corp.google.com/step`).
  * Adding spaces (`ms / step`) breaks the URL regex pattern, preventing false-positive auto-linking while maintaining clean, standard scientific notation.

### 1.6 Author & Contributor Metadata: GitHub Profile Links ("作者与贡献者账号规范")
* **Rule**: In design documents, RFCs, and technical one-pagers, **never use internal corporate emails** (e.g., `user@google.com`). Always format authors and contributors with their name and clickable GitHub profile link:
  * **Correct**:
    ```markdown
    **Author:** John Zhang ([@maxwillzq](https://github.com/maxwillzq))  
    **Date:** August 31, 2026  
    **Contributors:** Yuhao Ge ([@Geyuhao](https://github.com/Geyuhao)), Haotian Xue ([@haotianxue-google](https://github.com/haotianxue-google))  
    ```
  * **Incorrect**:
    ```markdown
    **Author:** John Zhang (johnqiangzhang@google.com)  
    **Contributors:** Yuhao Ge, Haotian Xue  
    ```
* **Rationale**:
  * *Open-Source & Multi-Org Alignment*: `vllm-torchtpu` is an open-source collaboration hosted on GitHub. Readers and reviewers interact via GitHub handles rather than internal corporate email addresses.
  * *Privacy & Information Leakage Prevention*: Prevents unintentional exposure of internal corporate email domains in documents that may be shared across teams or made public.
  * *One-Click Navigation*: Allows readers to immediately inspect the author's and contributors' upstream PRs, branches, and code ownership.

### 1.7 Self-Contained and Verified Code Snippets
* Code examples in design docs must be **syntactically valid, self-contained, and tested**:
  * Do not leave unused imports, dummy variables, or dead code.
  * Use actual hardware backend and device identifiers (e.g., `backend="tpu"` and `device="tpu"` in TorchTPU instead of legacy `openxla`).
  * Accompany code snippets with exact output shapes or assertion checks.

### 1.8 Pull Request (PR) Citation Standards: Mandatory Hyperlinks ("PR 引用超链接标准化")
* **Rule**: In design documents, RFCs, worklogs, and technical reports, **never leave PR numbers as unlinked plain text** (e.g., `PR #596`, `PR #667 to PR #686`, `PR #685/#686`). Every mention of a PR must be formatted as a direct, clickable markdown link pointing to the upstream GitHub PR URL:
  * **Single PR**:
    * *Correct*: `[PR #596](https://github.com/vllm-project/vllm-torchtpu/pull/596)`
    * *Incorrect*: `PR #596` or `#596`
  * **PR Stack or Continuous Range**:
    * *Correct*: `PRs [#667](https://github.com/vllm-project/vllm-torchtpu/pull/667)–[#686](https://github.com/vllm-project/vllm-torchtpu/pull/686)` or `[PR #667](https://github.com/vllm-project/vllm-torchtpu/pull/667) through [PR #686](https://github.com/vllm-project/vllm-torchtpu/pull/686)`
    * *Incorrect*: `PR #667 to PR #686`, `PR #667-PR #686`, `PRs 667-686`
  * **Multiple Discrete PRs**:
    * *Correct*: `[PR #685](https://github.com/vllm-project/vllm-torchtpu/pull/685) / [PR #686](https://github.com/vllm-project/vllm-torchtpu/pull/686)` or `[PR #685](url) and [PR #686](url)`
    * *Incorrect*: `PR #685/#686` or `PR 685 & 686`
  * **Section Headings & Benchmark Tables**:
    * In table rows and section headers, always embed the link inside the bold/heading text:
      * `| **Baseline ([PR #596](https://github.com/vllm-project/vllm-torchtpu/pull/596))** | ... |`
      * `1. **Step 1 ([PR #667](https://github.com/vllm-project/vllm-torchtpu/pull/667)) - Device-Resident arange Pre-allocation**:`
      * `### 1. Step 1 ([PR #667](https://github.com/vllm-project/vllm-torchtpu/pull/667)): Device-Resident arange Pre-Allocation`
* **Rationale**:
  * *Immediate Verification*: Reviewers and engineers can click directly through to the upstream GitHub implementation, discussions, and CI test results without manual searching.
  * *Disambiguation Across Repositories*: Explicit full URLs eliminate ambiguity when working across multiple repositories (`vllm-torchtpu`, `vllm`, `torch_xla`, etc.).
  * *Professionalism & Traceability*: Establishes an unbroken audit trail connecting design RFC decisions directly to merged git commits.

---

## 2. Standard Structural Template for Design Docs / RFCs

A high-quality technical RFC or One-Pager should follow a top-down executive structure:

```
1. Title & Metadata (Author, Date, Contributors with GitHub links, Status, Target Systems)
2. Problem Context & Architectural Questions (Pain point & root cause in 1-2 paragraphs)
3. Failure Modes / Counterexamples (Why intuitive/naive fixes fail, with concrete code)
4. Architectural Solutions: Optimization Stages (Direct engineering evolution)
5. Lessons Learned & Upstream Roadmap (Universal rules vs Case specializations + Compact PR stack)
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
* **Prohibit Gratuitous Architecture Diagrams ("拒绝为了画图而画图")**:
  * Do NOT insert generic ASCII box diagrams (e.g., `Host CPU -> PCIe Bus -> Accelerator`) that merely restate standard system dataflow already described in the text.
  * Every diagram must convey non-obvious technical insight (e.g., asynchronous execution timeline bubbles, pipeline stalls). When present, complex timeline flowcharts belong in the Appendix.
* **Prohibit Conversational FAQ Sections**:
  * Avoid conversational `Frequently Asked Questions (FAQ)` sections. Counterexamples and naive compilation questions belong in **Failure Modes & Counterexamples**. Architectural invariants belong in **Lessons Learned**.
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
- [ ] Are authors and contributors formatted with clickable GitHub profile links instead of corporate emails?
- [ ] Are all PR citations (single, pairs, ranges, tables, headings) formatted as clickable GitHub markdown links with zero unlinked plain text?
- [ ] Are compound engineering units spaced (e.g., `ms / step`, `ms / tok`, `tok / s`) to prevent Google Docs intranet URL auto-linkification?
- [ ] Are code snippets runnable with real backend names and zero dead variables?
- [ ] Is the main body readable in 3–5 minutes with code snippets <= 6 lines, and all complete diffs/schemas pushed to Appendices?
- [ ] Are gratuitous diagrams eliminated, with execution timeline charts reserved for the Appendix?
- [ ] Are conversational FAQs and redundant/strawman tradeoff tables avoided?
- [ ] Is the roadmap a compact PR list referencing the commit history appendix?
