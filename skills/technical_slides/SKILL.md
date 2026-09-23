---
name: technical_slides
description: Disciplined 5-gate workflow for creating engineering-grade web presentations and RFC slide decks from research papers, GitHub PRs, and benchmark dashboards. Enforces source/data reconciliation, collaborative Markdown outline sign-off, audience/style calibration, technical stack justification, and SVG diagram-first slide generation.
---

# Technical Presentation & Engineering RFC Slide Engineering (`technical_slides`)

This skill defines a strict **5-Gate Engineering Workflow** for transforming technical papers, design proposals (RFCs), GitHub prototype PRs, and hardware benchmark dashboards into high-impact, visually clear web presentations for ML & Systems Engineers.

> **Core Golden Rule:**
> **NEVER jump directly from a user request to writing HTML/slide code.**
> You MUST execute Gates 1 through 4 collaboratively with the author and receive explicit approval before generating the final slide deck in Gate 5.

---

## 🚦 The 5-Gate Presentation Workflow

```text
[Gate 1: Data & Source Audit]
       │  Reconcile paper vs. dashboard numbers, verify author & prototype/prod status
       ▼
[Gate 2: Collaborative Markdown Outline]
       │  Co-design slide-by-slide narrative arc & stop for Author Review
       ▼
[Gate 3: Audience & Style Specification]
       │  Calibrate technical depth (ML Engineer vs. General), enforce Diagram-First rule
       ▼
[Gate 4: Tech Stack Selection & Rationale]
       │  Justify rendering architecture (16:9 Viewport-Locked HTML + Inline SVG)
       ▼
[Gate 5: Slide Generation & Verified Deployment]
          Build SVG-rich slides, verify zero text overflow, deploy & check live URL
```

---

## 🔍 Gate 1: Authoritative Source & Benchmark Data Audit

Before drafting any slides, audit all primary sources and resolve discrepancies:

1. **Inventory All Input Sources:**
   - **Primary Paper / Design Doc:** Read the full manuscript (`.md` / `.tex`), extracting formal theorems, system conflicts, architecture diagrams, and invariants.
   - **Codebase / Prototype PR:** Check the exact commit SHA, LOC touched, and whether the code is a **Design Proposal / Prototype PR** (under review) or **Merged in Production**.
   - **Pedagogical References:** Check background repositories (e.g., `llm-learning-lab`) for clean first-principles explanations of foundational topics.
   - **Live Benchmark Dashboards:** Inspect the commit-pinned benchmark report (e.g., `lj report` dashboard).

2. **Cross-Source Data Reconciliation (Critical):**
   - Research papers and active benchmark dashboards frequently contain numbers from different iteration epochs (e.g., an early `17.76x` run in an abstract vs. a controlled 4-arm `2.97x` ablation in the latest commit-pinned dashboard).
   - **Action:** Build a concise **Dataset Comparison Table** showing the candidate datasets side-by-side and propose a clear reconciliation strategy (e.g., *"Use Commit-Pinned Dashboard X for the primary 4-arm ablation table, and Paper Tables 2–4 for the $B=1024$ micro-breakdown and cross-drafter EAGLE-3/DFlash experiments"*).

3. **Mandatory Metadata Verification:**
   - **Author & Affiliation:** Always confirm exact author credit (e.g., `Author: John Zhang, Core ML of Google`).
   - **Lifecycle Framing Badge:** If the PR is a prototype, explicitly badge every slide (`PROPOSAL & PROTOTYPE RFC — PR #XXXX, Not Yet Merged in Production`) so reviewers never mistake a prototype for merged production code.

---

## 📝 Gate 2: Collaborative Markdown Outline (`slides_outline.md`)

Draft a slide-by-slide Markdown outline and **request the author's review before proceeding**.

### Standard 10-Slide Narrative Arc for ML Systems / Architecture Proposals

| Slide | Role | Required Content & Visual Anchor |
| :---: | :--- | :--- |
| **1** | **Title & Executive Summary** | Title, Author/Affiliation, Prototype/RFC Status Badge, 3-Column Summary (*Problem*, *Proposed Design*, *Headline Hardware Results*). |
| **2** | **Background I: Domain Primer** | Teach the first domain prerequisite (e.g., *Structured Decoding / XGrammar PDA + Token Bitmask*) to a General ML Engineer. Highlight the hardware bottleneck (e.g., **16 GB Weight Read** vs. **128 KB KV Cache Write**). |
| **3** | **Background II: Systems Primer** | Teach the second prerequisite (e.g., *Speculative Decoding `[B, 1+K]` & Roofline Arithmetic Intensity*). Show why verifying $\gamma=8$ tokens costs roughly the same HBM bandwidth as decoding 1 token. |
| **4** | **The Core Insight ("Aha!" Moment)** | Combine Background I + II (e.g., *Jump Decoding: Stop Walking 1 Token/Step, Jump Across Deterministic `out-degree == 1` Spans*). Include formal step-compression bounds. |
| **5** | **Prior Art & Why Pioneers Failed** | Analyze why naive implementations (e.g., *Dynamic Variable-Length Micro-Prefills* or *Scheduler Draft Eviction*) break modern compiled engines (*Async Pipeline Stalls*, *XLA/CUDA Graph Recompilation*, *Disaggregated Decode Nodes Lacking Prefill Kernels*). |
| **6** | **Proposed Design I: Core Contract** | Present the unified abstraction (e.g., *Virtual Draft Model*, `(tokens, flags)` $[B, \gamma]$ static contract, *Draft Row Invariant* with arbitrary interleaving `[2, 2, 1, 2, 2, 2, 0]`). |
| **7** | **Proposed Design II: Key Optimizations** | Detail the planner & hardware fast-paths (e.g., `CompositeDraftPlanner` leading-run upgrade for EAGLE-3 + **Zero-Target-Logits Bypass** slicing `[B*8, H] -> [B, 1, H]` before `lm_head`). |
| **8** | **Prototype Implementation** | Show the modular software architecture (~300 LOC across 4 files in the prototype PR) with clean code snippets and zero kernel invasiveness. |
| **9** | **Benchmark Evaluation I (Core Ablation)** | Controlled multi-arm latency & speedup comparison across batch sizes, $\gamma$ window sensitivity (`4 vs 8 vs 16`), and per-step kernel profiling (`36x` sampling speedup). |
| **10** | **Benchmark Evaluation II & Roadmap** | Cross-architecture generalization (e.g., EAGLE-3 & DFlash speedups), honest boundary limitations (compute-bound crossover at high $B$), and phased upstreaming roadmap. |

---

## 🎨 Gate 3: Audience Calibration & Style Specification (`slides_style_spec.md`)

Document the visual and pedagogical rules agreed with the author:

### 1. Audience Calibration: "General ML & Systems Engineer"
- **What they ALREADY know:** Transformer forward pass, `bf16` model weights (`16 GB` for 8B model), Self-Attention KV Cache (`~128 KB/token`), HBM memory-bandwidth roof-line vs. MXU/TensorCore compute roof-line, `torch.compile` / XLA static shapes, and Prefill/Decode (P/D) disaggregation.
- **What they DO NOT know (and need explained clearly):** Domain-specific mechanics (how XGrammar compiles JSON schemas into PDAs and `int32[V/32]` bitmasks, how speculative rejection sampling cascades, why `eagle3.py` requires per-token hidden states).
- **Strict Anti-Patterns to Avoid:**
  - ❌ **No Fairy-Tale Metaphors:** Never replace precise engineering concepts (`16 GB Model Weights` vs. `KV Cache`) with childish analogies ("Giant Encyclopedia", "Duct-Tape Keyboard", "Professor and Intern").
  - ❌ **No Wall-of-Text Copy-Paste:** Never paste dense academic paragraphs from the paper into slide cards.

### 2. The "Diagram-First, Low-Text-Density" Rule
- **1 Custom Visual Diagram Per Slide:** Every slide must feature a clean inline `<svg>` diagram (pipeline flowchart, colored `[B, 8]` slot tray, roofline comparison, or horizontal bar chart).
- **Hard Text Limits:**
  - Maximum **3 cards** per slide (`row-2` or `row-3`).
  - Maximum **3 bullet points** per card, with **15–22 words per bullet**.
  - Use high-contrast semantic badges (`GRAMMAR=2` in Green `#067647`, `MODEL=1` in Blue `#175CD3`, `EMPTY=0` in Gray, Bottlenecks in Red `#B42318`).

---

## 🛠️ Gate 4: Technical Stack Selection & Rationale

Always explain to the user *what* technology will be used to build the deck and *why*:

### Recommended Architecture: Zipline-Style `16:9` Viewport-Locked HTML5 + Inline SVG
1. **Viewport-Locked Coordinate System (`--u: min(1vw, 1.7778vh)`):**
   - Sets `.stage { width: calc(var(--u) * 100); height: calc(var(--u) * 56.25); }`.
   - All typography, padding, and SVG dimensions scale proportionally with `--u`.
   - **Why:** Guarantees **zero text clipping, zero vertical scrollbars, and pixel-identical 16:9 presentation layout** across laptops, ultrawide monitors, and conference room projectors.
2. **Markdown-First Maintainability via `scripts/build_slides.py`:**
   - Instead of maintaining raw, thousand-line HTML files, slide authors write clean Markdown (`slides.md`).
   - The reusable compiler script in this skill (`scripts/build_slides.py`) compiles `slides.md` into Zipline-styled `index.html`:
     ```bash
     python3 skills/technical_slides/scripts/build_slides.py <slides.md> [output.html]
     ```
   - Authors can modify slide titles, lead paragraphs, code blocks, or fine captions directly in Markdown without wrestling with HTML/CSS.
3. **Handcrafted Inline `<svg>` Diagrams & Charts:**
   - **Why:** Unlike external chart libraries (Chart.js / Mermaid CDN) that fail offline or render blurry fonts, inline `<svg viewBox="...">` renders crisp vector boxes, arrows, tensor grids, and bar charts instantly with zero external dependencies.
4. **Cloud Run Versioned Hosting (`lj report upload -p <deck-name>`):**
   - Publishes immutable snapshots plus a `/latest/` pointer to Google Cloud Run for instant team review.

---

## 🚀 Gate 5: Execution & Verification Checklist

Only after the author approves Gates 1–4:
1. Maintain source content in `slides.md`.
2. Compile to HTML using the skill script:
   ```bash
   python3 skills/technical_slides/scripts/build_slides.py slides.md index.html
   ```
3. Verify every number against the dataset selected in Gate 1.
4. Confirm the **Author attribution** and **Prototype RFC status badge** appear on the cover and footer chrome.
5. Deploy via `lj report upload` and verify the live endpoint responds with HTTP 200.

