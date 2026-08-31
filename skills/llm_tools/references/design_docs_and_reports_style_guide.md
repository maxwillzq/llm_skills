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
* **Rule**: In design documents, RFCs, and technical one-pagers, **never use internal corporate emails** (e.g., `user@google.com`). Always format authors and contributors with their name and clickable GitHub profile link:
  * **Correct**:
    ```markdown
    **Author:** Alice Smith ([@alicesmith](https://github.com/alicesmith))  
    **Date:** August 31, 2026  
    **Contributors:** Bob Jones ([@bobjones](https://github.com/bobjones)), Carol Wu ([@carolwu](https://github.com/carolwu))  
    ```
  * **Incorrect**:
    ```markdown
    **Author:** Alice Smith (alice@corp-domain.com)  
    **Contributors:** Bob, Carol  
    ```
* **Rationale**:
  * *Open-Source & Cross-Organizational Alignment*: Modern engineering projects frequently span multiple organizations, open-source communities, and external partners. Readers and reviewers interact via public GitHub/GitLab handles rather than organization-specific internal email addresses.
  * *Privacy & Information Leakage Prevention*: Prevents accidental exposure of private corporate email addresses or internal team aliases in documents that may be shared externally or archived in public repositories.
  * *Direct Attribution & Ownership*: Enables one-click navigation to inspect author/contributor commits, PRs, and repository ownership.

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

---

## 2. Standard Structural Template for Design Docs / RFCs

A high-quality technical RFC or One-Pager should follow a top-down executive structure:

```
1. Title & Metadata (Author, Date, Contributors with GitHub links, Status)
2. Problem Context & Architectural Questions (Pain point & root cause in 1-2 paragraphs)
3. Failure Modes / Counterexamples (Why intuitive/naive fixes fail, with concrete code)
4. Architectural Solutions: Optimization Stages (Direct engineering evolution)
---
Appendices (Offload all secondary details here to keep the main text executive and crisp):
- Appendix A: Subsystem Architecture & Flowcharts
- Appendix B: Full Implementation Details & Code Modifications (Complete git diffs)
- Appendix C: Formal Specifications & Interface Definitions (Schemas, APIs, grammar contracts)
- Appendix D: Full Benchmark Tables, Harness Code & Experimental Methodology
- Appendix E: Quantitative Diagnostics & Resource Profiling Calculations (Stall analyses, memory budgets)
- Appendix F: Upstream Pull Request & Commit Lineage
- Appendix G: Test Suite & Verification Results
- Appendix H: Architectural Lessons Learned & Design Principles
- Appendix I: Interactive Hardware Profile & Trace Catalog (Profiler dumps, trace viewer sessions)
```

### 2.1 Anti-Patterns in Structural Organization
* **Prohibit Gratuitous Architecture Diagrams ("拒绝为了画图而画图")**:
  * Do NOT insert generic ASCII box diagrams (e.g., `Host CPU -> PCIe Bus -> Accelerator`) that merely restate standard system dataflow already described in the text.
  * Every diagram must convey non-obvious technical insight (e.g., asynchronous execution timeline bubbles, pipeline stalls). When present, complex timeline flowcharts belong in the Appendix.
* **Prohibit Conversational FAQ Sections**:
  * Avoid conversational `Frequently Asked Questions (FAQ)` sections. Counterexamples and naive compilation questions belong in **Failure Modes & Counterexamples**. Architectural invariants belong in **Appendix H (Lessons Learned & Design Principles)**.
* **Prohibit Strawman and Redundant Tradeoff Tables**:
  * Do NOT create comparison tables that merely duplicate bullet points in the same section.
  * Do NOT create strawman tradeoff tables comparing against unbuilt hypothetical solutions (e.g., comparing against a hypothetical unwritten kernel). If an alternative path was rejected early, state the technical rationale in 1–2 sentences and keep the section focused on the real solution.
* **Keep PR Lineage and Roadmaps in Appendices**:
  * PR stack lineages and upstream commit histories belong in **Appendix F**, keeping the executive body strictly focused on the architectural problem and technical solution.

---

## 3. Pre-Publication Review Checklist

Before finalizing any design doc, RFC, or PR description, verify:

- [ ] Are all emojis removed?
- [ ] Are editor-injected RGBA decoration characters eliminated by using clean PR references (e.g., `PR 123` without `#`) in the main text, with full URLs offloaded to Appendix F?
- [ ] Is metadata `Status` clean without inline PR numbers or links?
- [ ] Are all grandstanding buzzwords, promotional marketing phrases, and AI clichés ("surgical", "catastrophic", "harvesting low-hanging fruits", "slashed") eliminated?
- [ ] Are all benchmark numbers verified with explicit units, deltas, and test hardware (using standard hardware names without promotional/commercial prefixes)?
- [ ] Are authors and contributors formatted with clickable GitHub profile links instead of corporate emails?
- [ ] Are compound engineering units spaced (e.g., `ms / step`, `ms / tok`, `tok / s`) to prevent enterprise document tool URL auto-linkification?
- [ ] Are code snippets runnable with production-accurate runtime targets and zero dead variables?
- [ ] Is the main body readable in 3–5 minutes with code snippets <= 6 lines, and all complete diffs/schemas pushed to Appendices?
- [ ] Are gratuitous diagrams eliminated, with execution timeline charts reserved for the Appendix?
- [ ] Are conversational FAQs and redundant/strawman tradeoff tables avoided?
- [ ] Is the roadmap a compact PR list referencing the commit history appendix?
