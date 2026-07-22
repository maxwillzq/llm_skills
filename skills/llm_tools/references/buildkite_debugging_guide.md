# Buildkite CLI & API Debugging Guide

This guide details best practices for debugging Buildkite pipelines and retrieving job logs in headless terminal environments (e.g., Cloudtop).

## 1. Why `curl` REST API > `bk` CLI for Log Inspection
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

## 3. Retrieving Job Logs via REST API

### A. URL Mapping (Web UI -> API Endpoint)
When given a Buildkite job URL containing `jid`:
`https://buildkite.com/{org}/{pipeline}/builds/{build_number}/list?jid={job_id}`

Map directly to the plain-text API log URL:
`https://api.buildkite.com/v2/organizations/{org}/pipelines/{pipeline}/builds/{build_number}/jobs/{job_id}/log.txt`

### B. List Failed Jobs in a Build
If you only have the build URL without `jid` (e.g., `builds/590`), list all failed job IDs:
```bash
curl -s -H "Authorization: Bearer $(jq -r .graphql_token ~/.buildkite/config.json)" \
  "https://api.buildkite.com/v2/organizations/<ORG_SLUG>/pipelines/<PIPELINE_SLUG>/builds/<BUILD_NUMBER>" \
  | jq '.jobs[] | select(.state == "failed") | {id: .id, name: .name}'
```

### C. Download & Clean Raw Job Logs
Use `/log.txt` to retrieve raw output directly without JSON overhead. Buildkite prepends internal timestamps (`bk;t=1784677318164 `) to log lines; strip them using `sed 's/bk;t=[0-9]* //'`:

```bash
# Fetch log, strip Buildkite timestamp prefixes, and save to local file
curl -s -H "Authorization: Bearer $(jq -r .graphql_token ~/.buildkite/config.json)" \
  "https://api.buildkite.com/v2/organizations/<ORG_SLUG>/pipelines/<PIPELINE_SLUG>/builds/<BUILD_NUMBER>/jobs/<JOB_ID>/log.txt" \
  | sed 's/bk;t=[0-9]* //' > /tmp/buildkite_job.log

# View pytest failure summary
grep -E "FAILED|FAILURES|ERROR" /tmp/buildkite_job.log -A 10 -B 2
```
