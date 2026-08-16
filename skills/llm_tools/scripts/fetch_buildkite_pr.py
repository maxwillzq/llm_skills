#!/usr/bin/env python3
"""Fetch Buildkite CI/CD logs and artifacts for a GitHub PR.

Saves cleaned logs and artifacts into /tmp/<repo_name>/PR_<PR_NUM>/ for easy debugging.

Usage:
    python3 fetch_buildkite_pr.py <PR_NUMBER_OR_URL> [--repo ORG/REPO] [--no-artifacts]

Example:
    python3 fetch_buildkite_pr.py 383 -r vllm-project/vllm-torchtpu
    python3 fetch_buildkite_pr.py https://github.com/vllm-project/vllm-torchtpu/pull/383
"""

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request


def get_default_repo() -> str:
    """Infer GitHub repo from current git remotes, fallback to vllm-project/vllm-torchtpu."""
    try:
        remote = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        match = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", remote)
        if match:
            return f"{match.group(1)}/{match.group(2)}"
    except Exception:
        pass
    return "vllm-project/vllm-torchtpu"


def parse_pr_input(pr_input: str, default_repo: str) -> tuple[str, int]:
    """Parse PR number and repo from URL or integer."""
    pr_input = pr_input.strip()
    match = re.match(
        r"https?://github\.com/([^/]+/[^/]+)/pull/(\d+)", pr_input
    )
    if match:
        return match.group(1), int(match.group(2))
    try:
        return default_repo, int(pr_input)
    except ValueError:
        sys.exit(f"Error: Invalid PR input '{pr_input}'. Expected number or PR URL.")


def get_buildkite_token() -> str:
    """Get Buildkite GraphQL token from ~/.buildkite/config.json."""
    config_path = os.path.expanduser("~/.buildkite/config.json")
    if not os.path.exists(config_path):
        sys.exit(
            f"Error: Buildkite config not found at {config_path}. Run 'bk configure' first."
        )
    with open(config_path) as f:
        data = json.load(f)
    token = data.get("graphql_token")
    if not token:
        sys.exit("Error: 'graphql_token' not found in ~/.buildkite/config.json.")
    return token


def fetch_pr_checks(repo: str, pr_num: int) -> list[dict]:
    """Fetch statusCheckRollup for the PR using gh CLI."""
    cmd = [
        "gh",
        "pr",
        "view",
        str(pr_num),
        "-R",
        repo,
        "--json",
        "statusCheckRollup",
    ]
    try:
        res = subprocess.check_output(cmd, text=True, stderr=subprocess.PIPE)
        data = json.loads(res)
        return data.get("statusCheckRollup", [])
    except subprocess.CalledProcessError as e:
        sys.exit(f"Error calling gh CLI: {e.stderr.strip()}")


def parse_buildkite_url(url: str) -> dict | None:
    """Extract org, pipeline, build, and optional job_id from Buildkite URL."""
    if not url or "buildkite.com" not in url:
        return None

    parsed = urllib.parse.urlparse(url)
    job_id = None
    if parsed.fragment:
        job_id = parsed.fragment
    elif "jid=" in parsed.query:
        params = urllib.parse.parse_qs(parsed.query)
        job_id = params.get("jid", [None])[0]

    # Pattern: /org/pipeline/builds/build_number
    match = re.search(r"^/([^/]+)/([^/]+)/builds/(\d+)", parsed.path)
    if not match:
        return None

    return {
        "org": match.group(1),
        "pipeline": match.group(2),
        "build_number": match.group(3),
        "job_id": job_id,
        "original_url": url,
    }


def strip_buildkite_noise(raw_text: str) -> str:
    """Strip Buildkite timestamp prefixes and ANSI color codes."""
    # Strip timestamp prefixes like 'bk;t=1786828662135 '
    text = re.sub(r"bk;t=\d+\s*", "", raw_text)
    # Strip ANSI escape sequences
    text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
    return text


def download_job_log(
    token: str,
    org: str,
    pipeline: str,
    build_number: str,
    job_id: str,
    dest_path: str,
) -> bool:
    """Download plain text log via REST API and strip formatting noise."""
    url = f"https://api.buildkite.com/v2/organizations/{org}/pipelines/{pipeline}/builds/{build_number}/jobs/{job_id}/log.txt"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        cleaned = strip_buildkite_noise(content)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(cleaned)
        return True
    except Exception as e:
        print(f"  [!] Failed to download log for job {job_id}: {e}")
        return False


def download_job_artifacts(
    token: str, job_id: str, dest_dir: str, max_artifacts: int = 50
) -> int:
    """Download artifacts for a job using Buildkite GraphQL pre-signed URLs."""
    query = """
    query($job_id: ID!, $first: Int!) {
      job(uuid: $job_id) {
        ... on JobTypeCommand {
          artifacts(first: $first) {
            edges {
              node {
                path
                size
                downloadURL
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({
        "query": query,
        "variables": {"job_id": job_id, "first": max_artifacts},
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://graphql.buildkite.com/v1",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.load(resp)
        job_data = data.get("data", {}).get("job")
        if not job_data or "artifacts" not in job_data:
            return 0

        edges = job_data["artifacts"].get("edges", [])
        count = 0
        for edge in edges:
            node = edge["node"]
            rel_path = node["path"]
            dl_url = node["downloadURL"]
            if not dl_url:
                continue
            target_path = os.path.join(dest_dir, rel_path)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            urllib.request.urlretrieve(dl_url, target_path)
            count += 1
        return count
    except Exception as e:
        print(f"  [!] Failed to fetch artifacts for job {job_id}: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(
        description="Download failed Buildkite CI logs & artifacts for a PR."
    )
    parser.add_argument("pr", help="PR number or GitHub PR URL")
    parser.add_argument(
        "-r", "--repo", default=None, help="GitHub repository (owner/repo)"
    )
    parser.add_argument(
        "--no-artifacts", action="store_true", help="Skip downloading artifacts"
    )
    parser.add_argument(
        "--max-artifacts",
        type=int,
        default=50,
        help="Max artifacts per job (default: 50)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=None,
        help="Custom destination directory (default: /tmp/<repo_name>/PR_<pr_num>)",
    )
    args = parser.parse_args()

    default_repo = args.repo or get_default_repo()
    repo, pr_num = parse_pr_input(args.pr, default_repo)
    repo_name = repo.split("/")[-1]

    target_dir = args.output_dir or f"/tmp/{repo_name}/PR_{pr_num}"
    logs_dir = os.path.join(target_dir, "logs")
    artifacts_dir = os.path.join(target_dir, "artifacts")

    print(f"🔍 Inspecting checks for {repo} PR #{pr_num}...")
    token = get_buildkite_token()
    checks = fetch_pr_checks(repo, pr_num)

    failed_bk_checks = []
    for check in checks:
        state = check.get("state") or check.get("conclusion")
        if state in ("FAILURE", "TIMED_OUT", "ACTION_REQUIRED", "CANCELLED"):
            target_url = check.get("targetUrl") or check.get("detailsUrl") or ""
            info = parse_buildkite_url(target_url)
            if info:
                info["context"] = check.get("context") or check.get(
                    "name", "job"
                )
                failed_bk_checks.append(info)

    if not failed_bk_checks:
        print(
            f"✅ No failing Buildkite checks found for {repo} PR #{pr_num}!"
        )
        return

    # Filter out redundant top-level pipeline builds if individual job checks exist
    has_specific_jobs = any(item["job_id"] for item in failed_bk_checks)
    if has_specific_jobs:
        failed_bk_checks = [item for item in failed_bk_checks if item["job_id"]]

    print(
        f"🚨 Found {len(failed_bk_checks)} failing Buildkite check(s). Target folder: {target_dir}"
    )
    os.makedirs(logs_dir, exist_ok=True)

    for item in failed_bk_checks:
        org = item["org"]
        pipeline = item["pipeline"]
        build_number = item["build_number"]
        job_id = item["job_id"]
        context_name = item["context"].replace("/", "_").replace(" ", "_")

        print(f"\n📦 Processing Build #{build_number} ({item['context']})")

        # If job_id not in URL, query build to find failed jobs
        jobs_to_process = []
        if job_id:
            jobs_to_process.append((job_id, context_name))
        else:
            build_url = f"https://api.buildkite.com/v2/organizations/{org}/pipelines/{pipeline}/builds/{build_number}"
            req = urllib.request.Request(
                build_url, headers={"Authorization": f"Bearer {token}"}
            )
            try:
                with urllib.request.urlopen(req) as resp:
                    build_data = json.load(resp)
                for j in build_data.get("jobs", []):
                    if j.get("state") in ("failed", "timed_out", "broken"):
                        j_name = (
                            (j.get("name") or j.get("step_key") or j["id"])
                            .replace("/", "_")
                            .replace(" ", "_")
                        )
                        jobs_to_process.append((j["id"], j_name))
            except Exception as e:
                print(f"  [!] Failed to query build {build_number}: {e}")

        for j_id, j_name in jobs_to_process:
            log_path = os.path.join(logs_dir, f"{j_name}.log")
            print(f"  ⬇️  Downloading log -> {log_path}")
            if download_job_log(
                token, org, pipeline, build_number, j_id, log_path
            ):
                # Print failure preview
                try:
                    with open(log_path) as f:
                        lines = f.readlines()
                    error_lines = [
                        line.strip()
                        for line in lines
                        if re.search(
                            r"(FAIL|FAILED|ERROR|Traceback|exit status|timed_out)",
                            line,
                            re.I,
                        )
                    ]
                    if error_lines:
                        print(f"     🔎 Key failure line(s):")
                        for el in error_lines[-5:]:
                            print(f"        • {el[:120]}")
                except Exception:
                    pass

            if not args.no_artifacts:
                art_count = download_job_artifacts(
                    token, j_id, artifacts_dir, args.max_artifacts
                )
                if art_count > 0:
                    print(
                        f"  🎁 Downloaded {art_count} artifact(s) -> {artifacts_dir}"
                    )

    print(f"\n🎉 All logs and artifacts saved to: {target_dir}")


if __name__ == "__main__":
    main()
