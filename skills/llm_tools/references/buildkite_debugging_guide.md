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

### A. Step ID (`sid`) vs. Job ID (`id`)
In web dashboard URLs (e.g., `https://buildkite.com/tpu-commons/vllm-torchtpu-ci/builds/67/list?sid=019f1aa9-90fa-4a36-9d47-e498d338333f`), `sid` represents the frontend UI Step Group identifier. REST API endpoints require the specific **Job ID** (`id`).

### B. List Failed Jobs in a Build
To find the exact Job IDs and names of failed jobs in a build:
```bash
curl -s -H "Authorization: Bearer $(jq -r .graphql_token ~/.buildkite/config.json)" \
  "https://api.buildkite.com/v2/organizations/<ORG_SLUG>/pipelines/<PIPELINE_SLUG>/builds/<BUILD_NUMBER>" \
  | jq '.jobs[] | select(.state == "failed") | {id: .id, name: .name}'
```

### C. Fetch & Filter Job Output Log
Once you have the Job ID, retrieve the terminal output log and filter for errors:
```bash
curl -s -H "Authorization: Bearer $(jq -r .graphql_token ~/.buildkite/config.json)" \
  "https://api.buildkite.com/v2/organizations/<ORG_SLUG>/pipelines/<PIPELINE_SLUG>/builds/<BUILD_NUMBER>/jobs/<JOB_ID>/log" \
  | jq -r .content | grep -E "FAILED|RuntimeError|ValueError|Error:"
```
