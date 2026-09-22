# Collaborative Problem Solving & Disciplined Engineering

This guide defines a disciplined, high-velocity engineering workflow. It balances thorough analysis and safe collaboration with decisive execution, preventing rash code thrashing and unintended regressions.

---

## 🧭 Core Principles

1. **Do Not Act Rashly (谋定而后动)**: Never start editing core files or triggering expensive cloud jobs immediately upon seeing an error. Understand the system architecture and data flow first.
2. **Analyze the Context & Blast Radius**: Inspect surrounding code (周边环境), type signatures, lifecycle contracts, and downstream consumers before proposing changes.
3. **Solve the Right Root Cause**: Prefer idiomatic, standard framework mechanisms (e.g. registration APIs, decorator hooks, proper schemas) over ad-hoc monkey patches or string-hacking wrappers.
4. **Divide and Conquer (任务分治)**: Break complex multi-step refactorings into 2–3 self-contained, verifiable milestones. Align on the breakdown before implementation.
5. **Small Steps, Fast Checkpoints (小步快跑 · 提交锚点)**: For validated, passing changes, proactively create atomic Git commits. This establishes safe rollback checkpoints before entering high-risk experimental phases.
6. **Verifiable Definition of Done (闭环验证)**: Never claim a task is completed without concrete evidence (test outputs, curl status codes, diffs, live links).

---

## 🚦 Action Tier Matrix (行动分级与权限)

| Tier | Scope / Actions | Execution Protocol |
| :--- | :--- | :--- |
| 🟢 **Tier 1: Autonomous (自治操作)** | • Read-only code search (`grep`, `find`, `view_file`)<br>• Local/unit test runs (`pytest`, `lj test`)<br>• Local syntax/typo fixes with 100% certainty | **Execute immediately**. Report concise results directly. |
| 🟡 **Tier 2: Proposed (提案操作)** | • Adding local helper functions/utilities<br>• Surgical bug fixes with clear test coverage<br>• Low-cost dry-run commands | **Briefly state intent/diff**, then proceed to execute and verify. |
| 🔴 **Tier 3: Collaborative (严格协作)** | • Destructive data operations (GCS/DB deletion, prune)<br>• Public API breaking changes & schema rewrites<br>• Large architecture overhauls / expensive cloud jobs | **Stop & Align first**. Present options clearly (or via `ask_question`) before execution. |

---

## 🔄 Standard Workflow

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐
│ 1. Observation  │ ──► │ 2. Deep Analysis │ ──► │ 3. Alignment    │ ──► │ 4. Execution &   │
│    & Context    │     │    & Root Cause  │     │    & Plan       │     │    Verification  │
└─────────────────┘     └──────────────────┘     └─────────────────┘     └──────────────────┘
```

### 1. Observation & Context Gathering
- Read error logs and source definitions thoroughly.
- For broad multi-repo research, delegate to a read-only subagent to preserve the main context window.

### 2. Deep Analysis
- Trace inputs, outputs, data structures, and edge cases.
- Identify the root cause rather than treating symptoms.

### 3. Interactive Alignment (When Tier 3 / Trade-offs exist)
- **Design Trade-offs**: Use structured multiple-choice questions (`ask_question`) with recommended defaults to minimize user friction.
- **Complex Multi-Step Tasks**: Generate a structured plan artifact (`implementation_plan.md`) with actionable task checkboxes.

### 4. Execution, Verification & Checkpoint
- Make surgical, minimal edits.
- Run automated tests to verify zero regressions.
- Proactively propose atomic Git commits upon reaching verified milestones.

---

## 🧪 Mandatory Bug Fix Discipline: Test-First (Red-Green) Workflow

When resolving bug reports or fixing regressions, always follow strict Test-Driven Development (TDD) with atomic git checkpoints:

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ 1. Add Failing Test │ ──► │ 2. Confirm RED      │ ──► │ 3. Commit Test      │
│    (Regression Test)│     │    (Verify Failure) │     │    (Atomic Checkpt) │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
                                                               │
                                                               ▼
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ 6. Commit Fix       │ ◄── │ 5. Confirm GREEN    │ ◄── │ 4. Surgical Fix     │
│    (Atomic Checkpt) │     │    (Verify Pass)    │     │    (Root Cause)     │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

1. **Step 1: Reproduce with a Minimal Test**: Add a targeted unit or regression test covering the edge case described in the issue.
2. **Step 2: Make Test Fail First (RED Phase)**: Execute the test runner and verify that the test fails with the expected error. *Never implement or commit a fix without first confirming the test fails.*
3. **Step 3: Checkpoint Failing Test**: Create an atomic commit for the failing test:
   ```bash
   git commit -s -m "test(<scope>): add regression test for <issue-description> (#<issue_number>)"
   ```
4. **Step 4: Implement Surgical Fix**: Apply the minimal, non-invasive code change addressing the root cause.
5. **Step 5: Verify GREEN**: Re-run the regression test and the full test suite to guarantee zero regressions.
6. **Step 6: Checkpoint Fix**: Create an atomic commit for the fix:
   ```bash
   git commit -s -m "fix(<scope>): <fix-summary> (#<issue_number>)"
   ```

---

## 💡 Examples & Anti-Patterns

### ❌ Anti-Patterns
- **The Spray & Pray**: Seeing a serialization failure on integer keys and immediately writing a global recursive stringifier in a central middleware without knowing the underlying schema.
- **The Blind Job Runner**: Submitting a 30-minute TPU job immediately after a 1-line edit without local dry-run or unit test verification.
- **The Phantom Completion**: Telling the user "All fixed and verified" without actually running the test suite or checking command exit codes.

### ✅ Best Practices
- **Idiomatic Resolution**: Pausing to identify which PyTree structure failed serialization, recommending `jax.export.register_pytree_node_serialization`, and adding structured debugging logs.
- **Dry-Run Confirmation**: When cleaning cloud artifacts, providing `lj trace clean --dry-run` and showing the exact list of candidate deletions before executing.
- **Atomic Milestones**: "Core log parsing logic is implemented and 28/28 tests passed. Creating git commit `v1.0-checkpoint` before refactoring the UI layer."
