# GitHub CLI (gh) & Git Best Practices Guide

This reference provides quick commands, PR commit organization standards, and patterns for accessing PR data using the GitHub CLI.

## Prerequisites

Install GitHub CLI: https://cli.github.com/

Authenticate:
```bash
gh auth login
```

---

## PR Commit Organization & Commit Message Guidelines

### 1. Commit Organization Principles
When preparing PRs for review:
- **Atomic Separation of Concerns**: Separate core implementations (`src/`) from test suites (`tests/`). Keep commits focused, self-contained, and independently reviewable.
  - **Commit 1 (`feat`)**: Core feature / kernel / architecture implementation.
  - **Commit 2 (`test`)**: Dedicated unit tests, numerical verification, and benchmark suites.
- **Clean Squashing**: Squash intermediate fixups, formatting tweaks, and test debugging iterations before publishing or requesting review.
- **Stacked PR Workflow**: For complex, multi-stage projects, stack PRs logically:
  - **PR 1 (Baseline / Foundation)**: Unblocks the pipeline, fixes prerequisite bugs, and adds baseline E2E tests.
  - **PR 2 (Optimization Engine)**: Implements the optimized kernel/architecture and adds comparative performance benchmarks.

### 2. Commit Message Structure & Standards
Every commit must adhere to the Conventional Commits format with a detailed technical breakdown:

```text
<type>(<scope>): <concise imperative summary in lowercase>

- <Bullet 1: Clear explanation of WHAT was implemented/changed and WHY>
- <Bullet 2: Specific technical/mathematical mechanism (e.g., XLA Einsum, StableHLO select)>
- <Bullet 3: Concrete performance metric or benchmark result if applicable (e.g., 27.71x speedup)>
- <Bullet 4: Key bug fix / compatibility details (e.g., non-inplace Dynamo returns)>

Signed-off-by: Full Name <email@example.com>
```

#### Example Commit Message:
```text
feat(lora): implement static weight pool and XLA einsum linear layer on TPU

- Implement `TPUMultiLoRAPool` managing static 3D/4D tensorized LoRA weight pools on TPU HBM [0 .. max_loras - 1].
- Implement `TPUMultiLoRALinear` with zero-overhead XLA Static Einsum dispatch and StableHLO Select:
  - Base Linear Projection: `y_base = base_linear(x)`
  - Safe Index Clamp: `safe_slots = clamp(lora_indices - 1, min=0)`
  - 1st GEMM: `h = einsum('ti, tri -> tr', x, lora_a_pool[safe_slots])`
  - 2nd GEMM: `delta = einsum('tr, tor -> to', h, lora_b_pool[safe_slots]) * scale`
  - StableHLO Select: `torch.where(has_lora, y_base + delta, y_base)`
- Eliminate CPU host scheduling stalls, dynamic slice allocations, and HBM roundtrip thrashing.

Signed-off-by: John Zhang <johnqiangzhang@google.com>
```

### 3. Commit Re-structuring Recipe
To reorganize messy commits into clean atomic commits:
```bash
# 1. Soft reset to base branch (preserves all code changes as staged)
git reset --soft origin/main

# 2. Stage and commit implementation files first
git reset tests/
git commit -m "feat(...): ..."

# 3. Stage and commit test files
git add tests/
git commit -m "test(...): ..."
```

---

## Basic PR Information

### View PR Details
```bash
gh pr view <number> --repo <owner>/<repo>

# With JSON output
gh pr view <number> --repo <owner>/<repo> --json number,title,body,state,author,headRefName,baseRefName
```

### View PR Diff
```bash
gh pr diff <number> --repo <owner>/<repo>

# Save to file
gh pr diff <number> --repo <owner>/<repo> > pr_diff.patch
```

### List PR Files
```bash
gh pr view <number> --repo <owner>/<repo> --json files --jq '.files[].path'
```

## PR Comments and Reviews

### Get PR Comments (Review Comments on Code)
```bash
gh api /repos/<owner>/<repo>/pulls/<number>/comments

# Paginate through all comments
gh api /repos/<owner>/<repo>/pulls/<number>/comments --paginate

# With JQ filtering
gh api /repos/<owner>/<repo>/pulls/<number>/comments --jq '.[] | {path, line, body, user: .user.login}'
```

### Get PR Reviews
```bash
gh api /repos/<owner>/<repo>/pulls/<number>/reviews

# With formatted output
gh api /repos/<owner>/<repo>/pulls/<number>/reviews --jq '.[] | {state, user: .user.login, body}'
```

### Get Issue Comments (General PR Comments)
```bash
gh api /repos/<owner>/<repo>/issues/<number>/comments
```

## Commit Information

### List PR Commits
```bash
gh api /repos/<owner>/<repo>/pulls/<number>/commits

# Get commit messages
gh api /repos/<owner>/<repo>/pulls/<number>/commits --jq '.[] | {sha: .sha[0:7], message: .commit.message}'

# Get latest commit SHA
gh api /repos/<owner>/<repo>/pulls/<number>/commits --jq '.[-1].sha'
```

### Get Commit Details
```bash
gh api /repos/<owner>/<repo>/commits/<sha>

# Get commit diff
gh api /repos/<owner>/<repo>/commits/<sha> -H "Accept: application/vnd.github.diff"
```

## Branches

### Get Branch Information
```bash
# Source branch (head)
gh pr view <number> --repo <owner>/<repo> --json headRefName --jq '.headRefName'

# Target branch (base)
gh pr view <number> --repo <owner>/<repo> --json baseRefName --jq '.baseRefName'
```

### Compare Branches
```bash
gh api /repos/<owner>/<repo>/compare/<base>...<head>

# Get files changed
gh api /repos/<owner>/<repo>/compare/<base>...<head> --jq '.files[] | {filename, status, additions, deletions}'
```

## Related Issues and Tickets

### Get Linked Issues
```bash
# Get PR body which may contain issue references
gh pr view <number> --repo <owner>/<repo> --json body --jq '.body'

# Search for issue references (#123 format)
gh pr view <number> --repo <owner>/<repo> --json body --jq '.body' | grep -oE '#[0-9]+'
```

### Get Issue Details
```bash
gh issue view <number> --repo <owner>/<repo>

# JSON format
gh issue view <number> --repo <owner>/<repo> --json number,title,body,state,labels,assignees
```

### Get Issue Comments
```bash
gh api /repos/<owner>/<repo>/issues/<number>/comments
```

## PR Status Checks

### Get PR Status
```bash
gh pr checks <number> --repo <owner>/<repo>

# JSON format
gh api /repos/<owner>/<repo>/commits/<sha>/status
```

### Get Check Runs
```bash
gh api /repos/<owner>/<repo>/commits/<sha>/check-runs
```

## GitHub Actions Workflows

### List Running Workflow Runs
```bash
# List recent workflow runs in progress
gh run list --repo <owner>/<repo> --status in_progress

# Get run IDs via API
gh api /repos/<owner>/<repo>/actions/runs?status=in_progress --jq '.workflow_runs[] | {id, name, html_url}'
```

### Cancel or Force-Cancel Workflow Runs
```bash
# Standard cancel of a workflow run
gh run cancel <run_id> --repo <owner>/<repo>
# Or via API:
gh api -X POST /repos/<owner>/<repo>/actions/runs/<run_id>/cancel

# Force-cancel a running or stuck workflow run via API
gh api -X POST /repos/<owner>/<repo>/actions/runs/<run_id>/force-cancel
```

## Adding Comments

### Add Inline Code Comment
```bash
gh api -X POST /repos/<owner>/<repo>/pulls/<number>/comments \
  -f body="Your comment here" \
  -f commit_id="<sha>" \
  -f path="src/file.py" \
  -f side="RIGHT" \
  -f line=42
```

### Add Multi-line Inline Comment
```bash
gh api -X POST /repos/<owner>/<repo>/pulls/<number>/comments \
  -f body="Multi-line comment" \
  -f commit_id="<sha>" \
  -f path="src/file.py" \
  -f side="RIGHT" \
  -f start_line=40 \
  -f start_side="RIGHT" \
  -f line=45
```

### Add General PR Comment
```bash
gh pr comment <number> --repo <owner>/<repo> --body "Your comment"

# Or via API
gh api -X POST /repos/<owner>/<repo>/issues/<number>/comments \
  -f body="Your comment"
```

## Creating a Review

### Create Review with Comments
```bash
gh api -X POST /repos/<owner>/<repo>/pulls/<number>/reviews \
  -f body="Overall review comments" \
  -f event="COMMENT" \
  -f commit_id="<sha>" \
  -f comments='[{"path":"src/file.py","line":42,"body":"Comment on line 42"}]'
```

### Submit Review (Approve/Request Changes)
```bash
# Approve
gh api -X POST /repos/<owner>/<repo>/pulls/<number>/reviews \
  -f body="LGTM!" \
  -f event="APPROVE" \
  -f commit_id="<sha>"

# Request changes
gh api -X POST /repos/<owner>/<repo>/pulls/<number>/reviews \
  -f body="Please address these issues" \
  -f event="REQUEST_CHANGES" \
  -f commit_id="<sha>"
```

## Searching and Filtering

### Search Code in PR
```bash
# Get PR diff and search
gh pr diff <number> --repo <owner>/<repo> | grep "search_term"

# Search in specific files
gh pr view <number> --repo <owner>/<repo> --json files --jq '.files[] | select(.path | contains("search_term"))'
```

### Filter by File Type
```bash
gh pr view <number> --repo <owner>/<repo> --json files --jq '.files[] | select(.path | endswith(".py"))'
```

## Labels, Assignees, and Metadata

### Get Labels
```bash
gh pr view <number> --repo <owner>/<repo> --json labels --jq '.labels[].name'
```

### Get Assignees
```bash
gh pr view <number> --repo <owner>/<repo> --json assignees --jq '.assignees[].login'
```

### Get Reviewers
```bash
gh pr view <number> --repo <owner>/<repo> --json reviewRequests --jq '.reviewRequests[].login'
```

## Advanced Queries

### Get PR Timeline
```bash
gh api /repos/<owner>/<repo>/issues/<number>/timeline
```

### Get PR Events
```bash
gh api /repos/<owner>/<repo>/issues/<number>/events
```

### Get All PR Data
```bash
gh pr view <number> --repo <owner>/<repo> --json \
  number,title,body,state,author,headRefName,baseRefName,\
  commits,reviews,comments,files,labels,assignees,milestone,\
  createdAt,updatedAt,mergedAt,closedAt,url,isDraft
```

## Common JQ Patterns

### Extract specific fields
```bash
--jq '.field'
--jq '.array[].field'
--jq '.[] | {field1, field2}'
```

### Filter arrays
```bash
--jq '.[] | select(.field == "value")'
--jq '.[] | select(.field | contains("substring"))'
```

### Count items
```bash
--jq '. | length'
--jq '.array | length'
```

### Map and transform
```bash
--jq '.array | map(.field)'
--jq '.[] | {newField: .oldField}'
```

## Line Number Considerations for Inline Comments

**IMPORTANT**: The `line` parameter for inline comments refers to the **line number in the diff**, not the absolute line number in the file.

### Understanding Diff Line Numbers

In a diff:
- Lines are numbered relative to the diff context, not the file
- The `side` parameter determines which version:
  - `"RIGHT"`: New version (after changes)
  - `"LEFT"`: Old version (before changes)

### Finding Diff Line Numbers

```bash
# Get diff with line numbers
gh pr diff <number> --repo <owner>/<repo> | cat -n

# Get specific file diff
gh api /repos/<owner>/<repo>/pulls/<number>/files --jq '.[] | select(.filename == "path/to/file")'
```

### Example Diff
```diff
@@ -10,7 +10,8 @@ def process_data(data):
     if not data:
         return None

-    result = old_function(data)
+    # New implementation
+    result = new_function(data)
     return result
```

In this diff:
- Line 13 (old) would be `side: "LEFT"`
- Line 14-15 (new) would be `side: "RIGHT"`
- Line numbers are relative to the diff hunk starting at line 10

## Error Handling

### Common Errors

**Resource not found**:
```bash
# Check repo access
gh repo view <owner>/<repo>

# Check PR exists
gh pr list --repo <owner>/<repo> | grep <number>
```

**API rate limit**:
```bash
# Check rate limit
gh api /rate_limit

# Use authentication to get higher limits
gh auth login
```

**Permission denied**:
```bash
# Check authentication
gh auth status

# May need additional scopes
gh auth refresh -s repo
```

## Tips and Best Practices

1. **Use `--paginate`** for large result sets (comments, commits)
2. **Combine with `jq`** for powerful filtering and formatting
3. **Cache results** by saving to files to avoid repeated API calls
4. **Check rate limits** when making many API calls
5. **Use `--json` output** for programmatic parsing
6. **Specify `--repo`** when outside repository directory
7. **Get latest commit** before adding inline comments
8. **Test comments** on draft PRs or test repositories first

## Reference Links

- GitHub CLI Manual: https://cli.github.com/manual/
- GitHub REST API: https://docs.github.com/en/rest
- JQ Manual: https://jqlang.github.io/jq/manual/
- PR Review Comments API: https://docs.github.com/en/rest/pulls/comments
- PR Reviews API: https://docs.github.com/en/rest/pulls/reviews