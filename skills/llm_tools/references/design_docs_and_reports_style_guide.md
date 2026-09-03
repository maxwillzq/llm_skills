# Design Documents & Technical Reports Style Guide

This guide establishes the mandatory writing and organizational standards for engineering design documents, Request for Comments (RFCs), one-pagers, post-mortem/benchmark reports, and pull request descriptions.

---

## 1. Core Writing Invariants

### 1.1 Strict Prohibition of Emojis
* **Rule**: Never use emojis (e.g., rocket, lightning, checkmark, cross, party, lightbulb, chart, broom, target, etc.) in design documents, RFCs, PR descriptions, commit messages, or technical reports.
* **Rationale**: Emojis appear unprofessional, distract from technical content, and degrade readability in text-based diffs and terminal tools.
* **Alternative**: Use standard markdown typography, clean tables, bullet points, plain text markers (e.g., `PASSED`, `FAILED`, `[Test 1]`), and native Mermaid diagrams (` ```mermaid `) for architecture, flowcharts, and sequence diagrams. Mermaid renders as clean, responsive vector graphics across all standard Markdown previewers (VSCode, GitHub, GitLab) without ASCII text wrapping or font misalignment.

### 1.2 Elimination of Fluff, Buzzwords, and Hyperbole
* **Strict Prohibition of Grandstanding and Promotional Jargon ("拒绝大话套话")**:
  * Never use sensationalist adjectives: *"surgical stack"*, *"catastrophic collapse"*, *"deadly trap"*, *"slashed bubbles"*, *"quantum leap"*, *"blazing fast"*.
  * Never use consulting or business jargon in technical RFCs: *"harvesting low-hanging fruits"*, *"pragmatic, high-velocity strategy"*, *"paradigm shift"*, *"synergy"*.
  * Never anthropomorphize hardware: avoid *"starving the compute cores"*, use *"leaving compute cores idle"*.
* **Use precise, objective systems engineering language**:
  * Instead of: *"Our surgical multi-step stack completely crushed the latency bottleneck..."*
  * Write: *"Through a multi-stage optimization pipeline, we eliminated host-side memory allocations and fused elementwise passes, reducing per-request latency from 4.04 ms to 1.03 ms (-74.5%)."*
  * Instead of: *"We adopted a pragmatic strategy to harvest low-hanging fruits rather than rewriting in raw assembly..."*
  * Write: *"Rather than implementing custom device assembly kernels, optimizations were implemented across host memory management and compiler passes using standard abstractions."*
  * Preferred: *"This optimization eliminates redundant AST bytecode evaluation, reducing cold compilation latency by 2.30x (-56.6%)."*
  * Preferred: *"Partitioning the execution graph into N disconnected modules increases off-chip memory traffic and prevents cross-layer operator fusion."*

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
  * Cold compilation duration before and after (e.g., `105.68 s -> 45.83 s`).
  * Relative speedup and percentage delta (`2.30x speedup / -56.6% latency reduction`).
  * Hardware environment, pod topology, chip count, and test scripts (e.g., `Server Node (8 accelerators / 64 cores), scripts/benchmarks/run_perf_e2e.sh`).
* Distinguish between **empirically measured** numbers and **theoretical projections**.

### 1.5 Unit Formatting and Intranet Auto-Link Prevention ("单位斜杠空格法则")
* **Rule**: When writing compound engineering units with slashes (such as milliseconds per step, milliseconds per token, or tokens per second), **always place spaces around the slash**:
  * Write: `ms / step`, `ms / tok`, `tok / s`
  * Avoid: `ms/step`, `ms/tok`, `tok/s`
* **Rationale**:
  * In many enterprise document systems (such as Google Docs, Quip, Confluence) and internal Markdown parsers, `<word>/<path>` (such as `ms/step`, `ms/tok`, `req/s`) is aggressively auto-linked as an intranet URL if the prefix matches internal corporate hostnames or custom URI schemes.
  * Without spaces, documents frequently convert `ms/step` into an unwanted corporate hyperlink.
  * Adding spaces (`ms / step`) breaks URL autolink regexes, preventing false-positive hyperlinking while maintaining clean, standard scientific unit notation.

### 1.6 Author & Contributor Metadata: GitHub Profile Links ("作者与贡献者账号规范")
* **Rule**: In design documents, RFCs, and technical one-pagers, **never use internal corporate emails** (e.g., `user@google.com`). Always format authors and contributors with their name and clickable GitHub profile link.
* **Optionality Rule for Contributors ("只有存在实际协作者时才添加")**:
  * `Contributors` is **strictly optional**. Only include the `**Contributors:**` field when there are explicit, actual co-authors or collaborating engineers on the specific work.
  * For solo-authored PRs, RFCs, or technical one-pagers, **do NOT add a dummy, empty, or speculative `Contributors` line**—only include `Author`, `Date`, and `Status`.
* **Formatting Examples**:
  * **Solo Author (Standard / Default)**:
    ```markdown
    **Author:** Alice Smith ([@alicesmith](https://github.com/alicesmith))  
    **Date:** August 31, 2026  
    **Status:** In Review  
    ```
  * **Multiple Contributors (Only When Actually Applicable)**:
    ```markdown
    **Author:** Alice Smith ([@alicesmith](https://github.com/alicesmith))  
    **Date:** August 31, 2026  
    **Contributors:** Bob Jones ([@bobjones](https://github.com/bobjones)), Carol Wu ([@carolwu](https://github.com/carolwu))  
    **Status:** In Review  
    ```
  * **Incorrect**:
    ```markdown
    **Author:** Alice Smith (alice@corp-domain.com)  
    **Contributors:** Bob, Carol  
    ```
* **Rationale**:
  * *Open-Source & Cross-Organizational Alignment*: Modern engineering projects frequently span multiple organizations, open-source communities, and external partners. Readers and reviewers interact via public GitHub/GitLab handles rather than organization-specific internal email addresses.
  * *Privacy & Information Leakage Prevention*: Prevents accidental exposure of private corporate email addresses or internal team aliases in documents that may be shared externally or archived in public repositories.
  * *Direct Attribution & Ownership*: Enables one-click navigation to inspect author/contributor commits, PRs, and repository ownership without misattributing solo work.

### 1.7 Self-Contained and Verified Code Snippets
* Code examples in design docs must be **syntactically valid, self-contained, and tested**:
  * Do not leave unused imports, dummy variables, or dead code.
  * Use actual hardware backend and device identifiers (e.g., `backend="tpu"` and `device="tpu"` in TorchTPU instead of legacy `openxla`).
  * Accompany code snippets with exact output shapes or assertion checks.

### 1.8 Editor-Safe PR Citation & RGBA Decoration Prevention ("杜绝编辑器注入 RGBA 装饰字符法则")
* **Rule**:
  * In pure Markdown documents, **never write `#` immediately followed by digits** (e.g., avoid `PR #123`, `#123`, or inline `[PR #123](...)` in narrative text).
  * In the main body, TL;DR, and tables, write PR citations as clean, pure plain text: **`PR 123`** (or `PR-123`), omitting the `#` prefix:
    * *Correct*: `PR 123`, `PRs 101–105`, `PR 108 / PR 109`
    * *Incorrect*: `PR #123`, `PR #101 to PR #105`, `[PR #123](...)`
  * In document header metadata, **never attach PR numbers or GitHub links to the `Status:` field**:
    * *Correct*: `**Status:** Production Implementation` or `**Status:** In Review` or `**Status:** Drafted`
    * *Incorrect*: `**Status:** Production Implementation (PR #123)` or `**Status:** ([PR #123](url))`
  * All full repository URLs must be offloaded cleanly to **Appendix F: Upstream Pull Request & Commit Lineage**, formatted using standard path syntax:
    * *Correct*: `* **Pull Request**: [org/repo/pull/123](https://github.com/org/repo/pull/123)`
    * *Incorrect*: `* **Pull Request**: [org/repo#123](...)` or `[PR #123](...)`
* **Rationale**:
  * *VS Code / Monaco Decoration Injection*: Modern IDEs and editors with GitHub extensions (such as VS Code's *GitHub Pull Requests and Issues* extension) parse `#\d+` regex patterns and dynamically inject inline HTML/CSS RGBA-colored status widgets (colored SVG circles representing PR open/merged/closed states) directly between `PR ` and `#<number>`.
  * *Markdown Plain-Text Purity*: A markdown document must remain pure, clean, predictable plain text across all viewing contexts (terminal, raw git diffs, web readers, and IDEs) without being hijacked by editor-specific DOM decoration widgets.
  * *Separation of Concerns*: High-level executive text remains uncluttered, while Appendix F provides the single source of truth for full upstream URL lineages.

### 1.9 Strict Separation of Problem Space (Background) vs. Solution Space (Design) ("背景现状与方案设计严格隔离")
* **Rule**: The Background section must describe strictly **what currently exists, why it is insufficient, and historical context** (*"Background describes what is, not what will be"*). Never leak future design proposals, new API signatures, or solution details into Background.
* **Rationale**: Reviewers must first align on the reality of the bottleneck, prior art limitations, and quantitative baseline measurements before evaluating the merit of a proposed solution. Mixing solution details into the problem statement causes premature design debates before the problem is agreed upon.

### 1.10 Explicit Goals and Non-Goals Boundary Invariant ("显式目标与非目标边界法则")
* **Rule**: Every design doc, RFC, and technical one-pager must feature an explicit **Goals & Non-Goals** section immediately following the Problem Context / Motivation:
  * **Goals**: Must be strictly verifiable, measurable, and tied to concrete engineering criteria (e.g., *"Achieve zero host-accelerator roundtrip stalls during jump token verification"*, *"Reduce end-to-end P99 latency by >= 40% under structured decoding workloads"*). Avoid vague goals like *"Improve developer productivity"* or *"Make the engine faster"*.
  * **Non-Goals**: Must explicitly articulate **what is intentionally excluded or deferred to future iterations** (e.g., *"This design does NOT alter the CPU-side FSM grammar parser core"*, *"Multi-token speculative rollback across dynamic batch boundaries is out of scope for this phase"*).
* **Rationale**: Explicit Non-Goals protect the author by establishing hard boundaries against scope creep and preempting irrelevant reviewer tangents.

### 1.11 High-Signal Alternatives Considered & Rejection Rationale ("高信息密度备选方案与否决权衡")
* **Rule**: Document real, technical alternatives that were genuinely evaluated and rejected during design exploration.
  * For each alternative, state: (1) The approach name and architecture summary, and (2) The concrete, technical reason it was rejected (e.g., *"Alternative A: Host CPU Fallback Verification — Rejected because roundtrip PCIe latency (1.8 ms) exceeds single-step token compute budget, creating execution bubbles"*).
  * **Prohibition**: Do not invent trivial "strawman" alternatives just to fill space. If an obvious industry baseline exists (e.g., naive recompilation vs. static graph padding), state why it fails to meet the target constraints in 2 to 3 sentences.

### 1.12 Multi-Tiered Verification & Test Strategy ("分层验证与测试契约")
* **Rule**: Verification sections must define a concrete, multi-layered validation strategy rather than a vague *"tests will be added"* statement:
  * **Layer 1: Unit & Grammar Safety**: Fast CPU-side mock tests verifying state machine transitions, boundary checks, and rollback invariants.
  * **Layer 2: Kernel & Data Plane Invariant**: Device-level memory integrity tests verifying KV Cache slicing, shape consistency, and device buffer synchronization.
  * **Layer 3: End-to-End Accuracy & Benchmark Regression**: Full model serving tests ensuring 100% token output fidelity (e.g., exact JSON schema adherence) and reproducing target throughput/latency numbers.

### 1.13 Progressive Disclosure & Happy Path Separation ("渐进式呈现与主干流程分离法则")
* **Core Philosophy ("核心主干极简，防御容灾下沉")**:
  High-quality engineering design documents must strictly follow the principle of **Progressive Disclosure (渐进式信息呈现)**:
  * **Core Proposed Design (Happy Path Focus)**: The introductory design section must be minimalist, intuitive, and immediate. The reader must grasp the fundamental mental model within 1 to 2 minutes without cognitive overload. Code snippets and diagrams in the core section must present strictly the *Happy Path* (uncluttered by defensive error-recovery loops, rollback logic, exception handling, or boundary clamping).
  * **Advanced Topics Section (Edge Cases & Safety Invariants)**: Complex real-world failure modes (e.g., tokenization boundary divergences, greedy subword merge mismatches, bidirectional validation barriers, atomic state rollbacks, C++ stack overflow clamping, hardware exception fallbacks) must be systematically offloaded to a dedicated *Advanced Topics / Production Safety Invariants* section immediately following the core design.
* **Dual Value**:
  * *Executive & Cross-Team Accessibility*: Reviewers, Tech Leads, and engineers from other teams can rapidly comprehend the system's breakthrough value and core dataflow without getting lost in defensive boilerplate.
  * *Engineering Rigor*: Domain experts, reliability engineers, and staff reviewers find all deep safety invariants, corner cases, and mathematical failure bounds rigorously articulated in the advanced topics section.
* **Structural Template for Section 1 vs. Section 2**:
  * *Section 1 (Core Design / Happy Path)*:
    1. Plain-English Mental Model (e.g., deterministic linear subgraphs as a one-way chain).
    2. High-level 3-step execution pipeline (e.g., compile -> extract string -> tokenize and advance).
    3. Pure Happy-Path executable snippet (<= 40 lines, zero defensive boilerplate).
    4. Clean, minimal Mermaid flowchart showing only valid state transitions.
  * *Section 2 (Advanced Topics & Production Safety Invariants)*:
    1. Edge Case 1: Tokenizer / BPE greedy merge divergence (character validity != token validity).
    2. Safety Invariant 1: Bidirectional validation barrier (`accept_token` dry-run check).
    3. Safety Invariant 2: Atomic rollback mechanism ensuring zero state pollution on divergence.
    4. Mathematical Bound: Stack capacity expansion and runtime candidate clamping (<= M_rollback).

---

## 2. Standard Structural Templates for Design Docs & One-Pagers

Engineering documents in our ecosystem generally serve one of two distinct purposes. Authors must select the corresponding structure:

---

### 2.1 Template A: New Feature & System Capability RFC / One-Pager (新特性与新架构设计)

Use this template when introducing a **new capability, new subsystem, or functional feature** (e.g., Structured Jump Decoding, Speculative Decoding, Chunked Prefill, Disaggregated Serving):

```
1. Title & Metadata (Author, Date, Status, Optional Contributors if applicable)
2. Executive Summary & Value Proposition (Motivation, problem solved, primary performance/capability gains)
3. Goals & Non-Goals (Explicit in-scope targets vs. deliberate out-of-scope boundaries)
4. Background, Principles & Prior Art (Current state, FSM/algorithmic theory, existing engine comparisons)
5. System Architecture & Lifecycle Execution Flow (Control Plane vs. Data Plane, state transitions, sequence flow)
6. Key Engineering Innovations & Safety Invariants (BPE boundary validation, rollback safety, fallback handling)
7. Alternatives Considered & Technical Trade-offs (Evaluated approaches and concrete rejection rationale)
8. Live Hardware Verification & Empirical Benchmarks (Multi-tier tests, step compression ratios, throughput/latency)
---
Appendices (Offload all secondary assets to maintain executive main-body readability):
- Appendix A: Subsystem Architecture & Sequence Diagrams
- Appendix B: Full Implementation Code Modifications (Complete git diffs)
- Appendix C: Formal Specifications & Interface Contracts (Schemas, grammars, public APIs)
- Appendix D: Full Benchmark Harness & Experimental Methodology
- Appendix E: Quantitative Resource & Energy/Compute Savings Calculations
- Appendix F: Upstream Pull Request & Commit Lineage
- Appendix G: Automated Test Suite & Verification Results
- Appendix H: Architectural Lessons Learned & Design Principles
- Appendix I: Interactive Hardware Profile & Trace Catalog
```

---

### 2.2 Template B: Performance Optimization & Bottleneck Remediation (性能攻坚与瓶颈治理)

Use this template when documenting **latency profiling, bug remediation, memory tuning, or bottleneck elimination** (e.g., host allocation removal, DMA synchronization, kernel fusion):

```
1. Title & Metadata (Author, Date, Status, Optional Contributors if applicable)
2. Executive Summary & Measured Performance Progression (Table comparing Baseline vs. Step 1 ... Step N)
3. Goals & Non-Goals (Exact performance targets, hardware configurations in-scope vs. out-of-scope)
4. Problem Context & Profiling Analysis (Baseline measurement, stall attribution, trace analysis)
5. Failure Modes & Root Cause Analysis (Naive anti-patterns, why simple fixes fail, memory/hardware bounds)
6. Architectural Solutions: Multi-Stage Engineering Evolution (Systematic optimization stages)
7. Alternatives Considered & Rejected Paths (Why alternative tuning or workarounds were dismissed)
8. Verification, Regression Testing & Rollback Safety (Correctness proof, degradation safeguards)
---
Appendices (Same comprehensive appendix structure A–I as Template A).
```

---

### 2.3 Structural Anti-Patterns across all Document Types
* **Prohibit Gratuitous Architecture Diagrams ("拒绝为了画图而画图")**:
  * Do NOT insert generic ASCII box diagrams (e.g., `Host CPU -> PCIe Bus -> Accelerator`) that merely restate standard system dataflow already described in the text.
  * Every diagram must convey non-obvious technical insight (e.g., asynchronous execution timeline bubbles, pipeline stalls). When present, complex timeline flowcharts belong in the Appendix.
* **Prohibit Conversational FAQ Sections**:
  * Avoid conversational `Frequently Asked Questions (FAQ)` sections. Architectural invariants belong in **Section 5 / Section 6** or **Appendix H (Lessons Learned & Design Principles)**.
* **Prohibit Strawman and Redundant Tradeoff Tables**:
  * Do NOT create comparison tables that merely duplicate bullet points in the same section.
  * Do NOT create strawman tradeoff tables comparing against unbuilt hypothetical solutions. Use Section 7 (Alternatives Considered) to succinctly articulate real rejected alternatives with explicit technical reasons.
* **Keep PR Lineage and Roadmaps in Appendices**:
  * PR stack lineages and upstream commit histories belong in **Appendix F**, keeping the executive body strictly focused on the architectural design and technical solution.

---

## 3. Pre-Publication Review Checklist

Before finalizing any design doc, RFC, or PR description, verify:

- [ ] Are all emojis removed?
- [ ] Are editor-injected RGBA decoration characters eliminated by using clean PR references (e.g., `PR 123` without `#`) in the main text, with full URLs offloaded to Appendix F?
- [ ] Is metadata `Status` clean without inline PR numbers or links?
- [ ] Are all grandstanding buzzwords, promotional marketing phrases, and AI clichés ("surgical", "catastrophic", "harvesting low-hanging fruits", "slashed") eliminated?
- [ ] Are Problem Space (Background) and Solution Space (Design) strictly separated without premature design leakage into Background?
- [ ] Are Goals (verifiable, measurable) and Non-Goals (explicit scope boundaries) clearly stated?
- [ ] Are real Alternatives Considered documented with concrete technical rejection rationale?
- [ ] Is the verification plan multi-tiered (Unit, Data Plane / Kernel Invariant, End-to-End Accuracy)?
- [ ] Are all benchmark numbers verified with explicit units, deltas, and test hardware (using standard hardware names without promotional/commercial prefixes)?
- [ ] Are authors (and optional contributors, included strictly when actually present) formatted with clickable GitHub profile links instead of corporate emails?
- [ ] Are compound engineering units spaced (e.g., `ms / step`, `ms / tok`, `tok / s`) to prevent enterprise document tool URL auto-linkification?
- [ ] Are code snippets runnable with production-accurate runtime targets and zero dead variables?
- [ ] Is the main body readable in 3–5 minutes with code snippets <= 6 lines, and all complete diffs/schemas pushed to Appendices?
- [ ] Are gratuitous diagrams eliminated, with execution timeline charts reserved for the Appendix?
- [ ] Are conversational FAQs and redundant/strawman tradeoff tables avoided?
- [ ] Is the roadmap a compact PR list referencing the commit history appendix?
- [ ] Is Progressive Disclosure applied (Happy Path kept clean and intuitive in the core design, with defensive error recovery, edge cases, and safety invariants offloaded to Advanced Topics)?
