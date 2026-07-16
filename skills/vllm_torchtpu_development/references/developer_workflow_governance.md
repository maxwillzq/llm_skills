# Developer Workflow & Code Governance Guide (Pre-Public Special Supplement)
**Repository:** `vllm-project/vllm-torchtpu`  
**Effective Period:** July 2026 – Public Launch (Estimated Oct 2026)  
**Target Audience:** All Onboarded Developers, Core Maintainers, and Reviewers  
**Primary Tooling Standard:** [GitHub CLI (`gh`)](https://cli.github.com/) + Git

---

## 📌 Important Reference Notice

> [!NOTE]
> **Relationship to Standard Documentation:**  
> For all general contribution guidelines, bug reporting procedures, project directory structures, and general testing policies, **please refer directly to [`CONTRIBUTING.md`](file:///usr/local/google/home/johnqiangzhang/projects/vllm-torchtpu/CONTRIBUTING.md)**.  
>  
> **This document is EXCLUSIVELY a temporary, specialized governance supplement for the pre-public phase** to handle missing GitHub Team organization rulesets and open Read/Write repository access.

---

## 💡 1. Why This Guide Exists (Background & Rationale)

Welcome to the `vllm-project/vllm-torchtpu` pre-public development phase! Please read the rationale below regarding why this temporary governance guide is required:

### 🔍 The Situation & Challenge
1. **Transition Phase:** We are currently operating in a private organizational repository phase preparing for our official **Public Launch (Estimated October 2026)**.
2. **Missing Automated Rulesets:** Because this repository is currently a private organizational repository without GitHub Team subscription rulesets, **GitHub DOES NOT automatically enforce Branch Protection Rules**. Specifically:
   * ❌ GitHub will **NOT** block developers from accidentally running `git push origin main`.
   * ❌ GitHub will **NOT** lock the "Merge" button while CI tests are still running or failing.
   * ❌ GitHub will **NOT** show the UI "Update branch" button on outdated PRs.
3. **Open Read/Write Access Policy:** To foster active collaboration, we have opened Read/Write permissions to all onboarded developers. However, this creates significant risks of build breakage, unstable `main` branch state, and PR stalls if self-discipline is not maintained.

### 🎯 Purpose of This Document
Until the repository **goes public** (at which point standard automated GitHub Branch Protections will be activated and standard `CONTRIBUTING.md` will take full effect), **this document serves as our binding Developer Code of Conduct and Standard Operating Procedure (SOP)**. 

Compliance relies on every developer following these procedures strictly.

> [!WARNING]
> **Access Policy Enforcement:**  
> Because automated branch rulesets are disabled, compliance is monitored manually. **Contributors who repeatedly violate these rules (e.g., pushing directly to `main` or merging before CI passes) will have their write permissions revoked and downgraded back to Read-Only access.**

---

## 🛠️ 2. One-Time Setup & Prerequisites

Before submitting code, ensure you have `gh` CLI authenticated:

```bash
# Login to GitHub CLI (select github.com and HTTPS or SSH)
gh auth login

# Verify authentication status
gh auth status
```

> 💡 *Note: For pre-commit formatting and linting setup, directory structures, and code style rules, refer directly to [`CONTRIBUTING.md`](file:///usr/local/google/home/johnqiangzhang/projects/vllm-torchtpu/CONTRIBUTING.md).*

---

## 🚀 3. Code Submission Flow

All contributions during this pre-public phase must strictly follow this 4-step submission lifecycle:

> 🚨 **Mandatory Command Rule:**  
> **Always explicitly specify the target `<PR_NUMBER>` in all `gh` CLI commands** (e.g., `gh pr checks 35`, `gh pr view 35`) to avoid ambiguity.

---

### Phase 1: Create PR

1. **Create Branch & Set Direct Push Guard:**
   Never commit or push directly to `main`.
   ```bash
   # Switch to main and pull latest changes
   git checkout main && git pull origin main

   # Create feature branch (e.g. username/feature-name)
   git checkout -b username/feature-name

   # Guard against accidental direct push to origin/main locally
   git config branch.main.pushRemote no_push
   ```

2. **Commit with DCO Sign-off (`-s`):**
   ```bash
   git commit -s -m "feat(kernel): add experimental TPU attention layer"
   ```
   
   #### 💡 Handling DCO Failures
   * **CLI Fix (Recommended):** Amend latest commit and force push:
     ```bash
     git commit --amend --signoff --no-edit
     git push origin HEAD --force-with-lease
     ```
   * **UI Override (Temporary Pre-Public Option):** During this pre-public stage, repository collaborators can also manually click the DCO check details in the GitHub PR UI and click **"Set DCO to PASS"** to manually override and pass the check when necessary.

3. **Push & Open PR with Assignees:**
   Because GitHub UI only records one reviewer approval in certain views, **always assign multiple reviewers via `--assignee`**:
   ```bash
   git push origin HEAD
   gh pr create --fill --assignee reviewer1,reviewer2
   ```

   #### 💡 Adding Additional Reviewers (Assignees) After PR Creation
   If a PR is already created and you need to add another reviewer (e.g., `reviewer3`):
   ```bash
   # Add an additional assignee to an existing PR
   gh pr edit <PR_NUMBER> --add-assignee reviewer3
   
   # Or alternatively, request review via --add-reviewer:
   gh pr edit <PR_NUMBER> --add-reviewer reviewer3
   ```

---

### Phase 2: Wait for Test Pass & Review Approval

> 🚨 **CRITICAL RULE:** Never merge a PR while CI tests are still running/failing OR before getting approval. Always pass `<PR_NUMBER>` explicitly.

During this pre-public phase, GitHub does not automatically block merges or show status updates in the usual web UI ways. Pay attention to key differences and rules to watch out for:

1. **Watch CI Execution (No Automated Merge Blocking):**
   GitHub will **not** disable the merge button while CI is running or failing. Developers must manually monitor CI progress until all checks complete green.  
   *(Refer to Section 4: Quick Reference Cheat Sheet for `gh pr checks <PR_NUMBER> --watch --fail-fast`)*

2. **Verify Reviewer Approval:**
   Ensure at least one reviewer has explicitly approved the PR before merging.  
   *(Refer to Section 4: Quick Reference Cheat Sheet for approval verification command)*

3. **Check Unresolved Discussion Comments:**
   Verify that all review comment threads have been addressed and marked as resolved.  
   *(Refer to Section 4: Quick Reference Cheat Sheet for GraphQL thread query)*

4. **Update Outdated PR (Missing Web UI Button):**
   Because the "Update branch" web button is disabled/missing on outdated PRs in this repository setup, update your branch directly via GitHub CLI if `main` has moved ahead.  
   *(Refer to Section 4: Quick Reference Cheat Sheet for `gh pr update-branch <PR_NUMBER>`)*

---

### Phase 3: Merge the PR

Once review approval is confirmed AND `gh pr checks` returns **PASS (All Green)** for `<PR_NUMBER>`, execute the safe guarded merge command:

```bash
# Verify approval AND CI status on target PR_NUMBER; only merge if both pass
[ "$(gh pr view <PR_NUMBER> --json latestReviews --jq '[.latestReviews[] | select(.state == "APPROVED")] | length')" -gt 0 ] && gh pr checks <PR_NUMBER> && gh pr merge <PR_NUMBER> --squash --delete-branch
```

> [!NOTE]
> Chaining `[ approved ] && gh pr checks && gh pr merge` guarantees that the merge will abort if the PR has no approvals OR if CI checks fail.

---

### Phase 4: Post Merge Validation & Nightly Build Inspection

After the PR is merged into `main`:

1. **Inspect Nightly & Scheduled Build Results (Buildkite):**  
   To verify that your change runs successfully in scheduled nightly TPU benchmarks:
   * 🔗 **Buildkite Dashboard URL:**  
     `https://buildkite.com/tpu-commons/vllm-torchtpu-ci/builds?branch=main&query=Scheduled+build`

2. **Verify Main Branch CI Runs (GitHub CLI):**
   Confirm that recent workflow runs on `main` remain green and stable:
   ```bash
   gh run list --branch main --limit 5
   ```

3. **Clean Up Local Environment:**
   Sync your local workspace and delete obsolete feature branches:
   ```bash
   git checkout main
   git pull origin main
   git branch -d username/feature-name
   git remote prune origin
   ```

---

## 🛠️ 4. Quick Reference Cheat Sheet (`gh` Commands & Links)

| Objective | Command / Direct Link |
| :--- | :--- |
| **Phase 1: Create PR & Assign** | `gh pr create --fill --assignee reviewer1,reviewer2` |
| **Phase 1: Add Missing Reviewer to PR** | `gh pr edit <PR_NUMBER> --add-assignee reviewer3` |
| **Phase 2: Watch CI (Fail Fast)** | `gh pr checks <PR_NUMBER> --watch --fail-fast` |
| **Phase 2: Check PR Approval** | `gh pr view <PR_NUMBER> --json latestReviews --jq 'if ([.latestReviews[] \| select(.state == "APPROVED")] \| length > 0) then "APPROVED ✅" else "NOT APPROVED ❌" end'` |
| **Phase 2: Check Resolved Discussions** | `gh api graphql -F owner='vllm-project' -F repo='vllm-torchtpu' -F pr=<PR_NUMBER> -f query='query($owner: String!, $repo: String!, $pr: Int!) { repository(owner: $owner, name: $repo) { pullRequest(number: $pr) { reviewThreads(first: 50) { nodes { isResolved } } } } }' --jq 'if ([.data.repository.pullRequest.reviewThreads.nodes[] \| select(.isResolved == false)] \| length == 0) then "RESOLVED ✅" else "UNRESOLVED ❌" end'` |
| **Phase 2: Update Outdated Branch** | `gh pr update-branch <PR_NUMBER>` |
| **Phase 3: Guarded Merge (Approved + Green)** | `[ "$(gh pr view <PR_NUMBER> --json latestReviews \| jq '[.latestReviews[] \| select(.state == "APPROVED")] \| length')" -gt 0 ] && gh pr checks <PR_NUMBER> && gh pr merge <PR_NUMBER> --squash --delete-branch` |
| **Phase 4: Main Branch CI Check (CLI)** | `gh run list --branch main --limit 5` |
| **Phase 4: Buildkite Nightly URL** | `https://buildkite.com/tpu-commons/vllm-torchtpu-ci/builds?branch=main&query=Scheduled+build` |
| **Fix Missing DCO (CLI)** | `git commit --amend --signoff --no-edit && git push origin HEAD --force-with-lease` |
| **Fix Missing DCO (UI Override)** | Click DCO check details in GitHub PR UI -> Click **"Set DCO to PASS"** |

---

## 📋 5. Pre-Merge Verification Checklist

Every developer merging code MUST verify:

- [ ] Review approval verified: `latestReviews` has at least 1 `APPROVED` for `<PR_NUMBER>` ✅
- [ ] Discussions checked: All comment threads marked as resolved for `<PR_NUMBER>` ✅
- [ ] `gh pr checks <PR_NUMBER>` returns ALL GREEN ✅ (Automated by the Guarded Merge command)
- [ ] DCO Sign-off verified (`-s` or UI override via "Set DCO to PASS")
- [ ] All PR discussion comments resolved
- [ ] Post-merge validation plan ready (Inspect Buildkite Nightly dashboard)
