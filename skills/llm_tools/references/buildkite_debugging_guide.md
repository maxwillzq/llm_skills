# Buildkite CLI & API Debugging Guide

This guide details best practices for debugging Buildkite pipelines, downloading cleaned logs, and retrieving job artifacts in headless terminal environments (e.g., Cloudtop).

---

## 1. Why `curl` / GraphQL REST API > `bk` CLI for Log Inspection
- **No GraphQL Complexity Limits**: In large enterprise organizations (e.g., `tpu-commons`), running generic discovery commands via `bk` (like `bk browse` or `bk pipeline list`) without filtering issues global queries (`pipelines(first: 500)` across all orgs) that exceed Buildkite's GraphQL complexity limit (`Ratelimit-Complexity-Requested: 501503 > 50000`).
- **Direct Log Access**: The `bk` CLI (v2.x) lacks built-in subcommands to print job execution terminal logs directly. Using `curl` against Buildkite's REST API v2 provides immediate access to exact job output without extra tools.

---

## 2. Authentication Setup (`~/.buildkite/config.json`)

Buildkite configuration stores tokens in `~/.buildkite/config.json`.
To configure GitHub authentication in headless environments where a browser cannot be opened, reuse your local `gh` CLI credentials formatted as a Go `oauth2.Token` struct:

```bash
# Inject gh token cleanly into Buildkite config
jq --arg token "$(gh auth token)" '.github_oauth_token = {"access_token": $token, "token_type": "bearer"}' ~/.buildkite/config.json > ~/.buildkite/config.json.tmp && mv ~/.buildkite/config.json.tmp ~/.buildkite/config.json
```

---

## 3. Recommended Storage Structure: `/tmp/<repo_name>/PR_<PR_NUM>/`

When investigating CI errors on a pull request, organize downloaded artifacts and logs into a dedicated folder under `/tmp/`:

```text
/tmp/<repo_name>/PR_<PR_NUM>/
├── logs/
│   └── <failing_step_name>.log    # Cleaned plain-text log (timestamps & ANSI stripped)
└── artifacts/
    └── <job_or_artifact_path>/    # Dumps, XML reports, profiler traces, JSON results
```

---

## 4. Automated Log & Artifact Fetcher (`fetch_buildkite_pr.py`)

A helper script is provided in `skills/llm_tools/scripts/fetch_buildkite_pr.py`. It inspects failing Buildkite checks on any GitHub PR, downloads the logs, cleans ANSI color escape codes and Buildkite timestamps, and downloads job artifacts into `/tmp/<repo_name>/PR_<PR_NUM>/`.

```bash
# Auto-detects repo if inside git directory, or specify -r
python3 ~/.gemini/config/skills/llm_tools/scripts/fetch_buildkite_pr.py 383 -r vllm-project/vllm-torchtpu

# Or pass PR URL directly:
python3 ~/.gemini/config/skills/llm_tools/scripts/fetch_buildkite_pr.py https://github.com/vllm-project/vllm-torchtpu/pull/383
```

---

## 5. Manual Step-by-Step Workflow (REST & GraphQL API)

### A. Discover Failed Checks from GitHub PR
```bash
gh pr view <PR_NUM> -R <REPO> --json statusCheckRollup \
  | jq -r '.statusCheckRollup[] | select(.state=="FAILURE" or .conclusion=="FAILURE") | "\(.context) \(.targetUrl)"'
```

### B. Download & Clean Raw Job Logs
Buildkite URLs map to the REST API log endpoint:
`https://api.buildkite.com/v2/organizations/{org}/pipelines/{pipeline}/builds/{build_number}/jobs/{job_id}/log.txt`

```bash
TOKEN=$(jq -r .graphql_token ~/.buildkite/config.json)
TARGET_DIR="/tmp/<repo_name>/PR_<PR_NUM>"
mkdir -p "${TARGET_DIR}/logs" "${TARGET_DIR}/artifacts"

# Download log, strip Buildkite timestamp prefixes (bk;t=...) and ANSI color codes
curl -s -H "Authorization: Bearer $TOKEN" \
  "https://api.buildkite.com/v2/organizations/<ORG>/pipelines/<PIPELINE>/builds/<BUILD_NUM>/jobs/<JOB_ID>/log.txt" \
  | sed -E 's/bk;t=[0-9]* //; s/\x1b\[[0-9;]*[a-zA-Z]//g' > "${TARGET_DIR}/logs/<JOB_NAME>.log"
```

### C. Download Artifacts via Pre-signed GraphQL URLs
Buildkite GraphQL returns pre-signed S3/GCS download URLs for each artifact:

```bash
python3 -c "
import json, urllib.request, os

with open(os.path.expanduser('~/.buildkite/config.json')) as f:
    token = json.load(f)['graphql_token']

query = '''
query {
  job(uuid: \"<JOB_ID>\") {
    ... on JobTypeCommand {
      artifacts(first: 50) {
        edges {
          node {
            path
            downloadURL
          }
        }
      }
    }
  }
}
'''

req = urllib.request.Request(
    'https://graphql.buildkite.com/v1',
    data=json.dumps({'query': query}).encode('utf-8'),
    headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
)

with urllib.request.urlopen(req) as resp:
    data = json.load(resp)

base_dir = '${TARGET_DIR}/artifacts'
for edge in data['data']['job']['artifacts']['edges']:
    node = edge['node']
    dest = os.path.join(base_dir, node['path'])
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    urllib.request.urlretrieve(node['downloadURL'], dest)
    print(f'Downloaded {node[\"path\"]} -> {dest}')
"
```

---

## 6. Common Error Patterns & Diagnostic Signals

| Failure Type | Search Pattern / Signal | Typical Cause & Action |
|---|---|---|
| **Pytest Assertion / Failure** | `grep -E "(=== FAILURES ===\|FAILED .* - )" -A 20` | Test assertion failure. Check `Traceback` lines. |
| **OOM / Killed (Host or TPU)** | `exit status 137`, `Killed`, `ResourceExhaustedError` | RAM / TPU HBM exhausted. Reduce batch size or fix memory leak. |
| **Segmentation Fault** | `exit status 139`, `Segmentation fault` | Native C++/XLA/Pallas crash. Download core dump or inspect backtrace. |
| **Timeout** | `timed_out`, `Job timed out after XX minutes` | Process deadlock, hang in distributed communication (NCCL/Ray), or network stall. |
| **Docker / Registry Error** | `failed to pull image`, `denied: access forbidden` | Authentication issue, missing image tag, or pull rate limit. |
