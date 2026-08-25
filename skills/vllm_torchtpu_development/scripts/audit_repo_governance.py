#!/usr/bin/env python3
import argparse
import csv
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone, timedelta

REPO = "vllm-project/vllm-torchtpu"
DEFAULT_RECIPIENT = "johnqiangzhang@google.com"
DEFAULT_SENDER = '"vLLM-Torchtpu Governance Audit (No-Reply)" <johnqiangzhang@google.com>'

def load_recipients(cli_recipients=None, csv_path=None):
    recipients = []
    if csv_path:
        # Check relative to CWD first, then fallback to script directory
        resolved_path = csv_path
        if not os.path.exists(resolved_path):
            script_dir = os.path.dirname(os.path.abspath(__file__))
            fallback_path = os.path.join(script_dir, csv_path)
            if os.path.exists(fallback_path):
                resolved_path = fallback_path

        if not os.path.exists(resolved_path):
            print(f"⚠️ Error: Recipients CSV file '{csv_path}' not found.", file=sys.stderr)
        else:
            with open(resolved_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    for item in row:
                        item = item.strip()
                        if item and "@" in item and not item.startswith("#"):
                            recipients.append(item)
    if cli_recipients:
        for r in cli_recipients.split(","):
            r = r.strip()
            if r:
                recipients.append(r)
    # Deduplicate preserving order
    recipients = list(dict.fromkeys(recipients))
    if not recipients:
        recipients = [DEFAULT_RECIPIENT]
    return recipients


def run_command(cmd, text_output=True, cwd=None):
    if isinstance(cmd, str):
        result = subprocess.run(cmd, capture_output=True, text=text_output, shell=True, cwd=cwd)
    else:
        result = subprocess.run(cmd, capture_output=True, text=text_output, cwd=cwd)
    if result.returncode != 0:
        print(f"Error running command '{cmd}': {result.stderr}", file=sys.stderr)
        return None
    return result.stdout.strip() if text_output else result.stdout

def check_direct_pushes(hours):
    """Rule 1: Detect commits pushed directly to main without a PR."""
    violations = []
    limit = max(30, min(100, int(hours * 1.5)))
    output = run_command(f"gh api repos/{REPO}/commits?per_page={limit}")
    if not output:
        return violations

    try:
        commits = json.loads(output)
    except Exception as e:
        print(f"Failed to parse commits JSON: {e}")
        return violations

    now = datetime.now(timezone.utc)
    for c in commits:
        date = c.get("commit", {}).get("author", {}).get("date", "")
        if date:
            try:
                commit_datetime = datetime.fromisoformat(date.replace("Z", "+00:00"))
                if now - commit_datetime > timedelta(hours=hours):
                    break
            except Exception:
                pass

        sha = c.get("sha")
        message = c.get("commit", {}).get("message", "").split("\n")[0]
        # Ignore merge commits created by GitHub PR merges
        if message.startswith("Merge pull request #") or message.startswith("Merge branch"):
            continue

        # Query PRs associated with this commit
        pulls_output = run_command(f"gh api repos/{REPO}/commits/{sha}/pulls")
        if pulls_output is not None:
            try:
                pulls = json.loads(pulls_output)
                if not pulls:
                    author = c.get("commit", {}).get("author", {}).get("name", "Unknown")
                    violations.append({
                        "sha": sha[:8],
                        "author": author,
                        "date": date,
                        "message": message
                    })
            except Exception:
                pass
    return violations

def load_codeowners_rules():
    """Load and parse CODEOWNERS rules from local repo or GitHub API."""
    import fnmatch
    local_candidates = [
        os.path.expanduser("~/projects/vllm-torchtpu/.github/CODEOWNERS"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../vllm-torchtpu/.github/CODEOWNERS"),
        ".github/CODEOWNERS"
    ]
    for p in local_candidates:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    return parse_codeowners_content(f.read())
            except Exception:
                pass

    # Fallback to gh api
    output = run_command(f"gh api repos/{REPO}/contents/.github/CODEOWNERS --jq .content")
    if output:
        try:
            import base64
            decoded = base64.b64decode(output).decode("utf-8")
            return parse_codeowners_content(decoded)
        except Exception:
            pass
    return []

def parse_codeowners_content(content):
    rules = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        pattern = parts[0]
        owners = [o.lstrip("@") for o in parts[1:] if o.startswith("@")]
        if owners:
            rules.append((pattern, owners))
    return rules

def match_codeowners_rule(filepath, rules):
    import fnmatch
    p = "/" + filepath.lstrip("/")
    matched_rule = None
    for pattern, owners in rules:
        pat = pattern.rstrip("/")
        if pattern == "*":
            matched_rule = (pattern, owners)
        elif pattern.endswith("/"):
            if p.startswith(pat + "/") or p == pat:
                matched_rule = (pattern, owners)
        else:
            if p == pattern or fnmatch.fnmatch(p, pattern):
                matched_rule = (pattern, owners)
    return matched_rule

def check_premature_merges(hours):
    """Rule 2: Detect PRs merged while CI checks were failing, in progress, unexecuted, or merged prematurely."""
    violations = []
    all_merged_prs = []
    codeowners_rules = load_codeowners_rules()

    limit = max(30, min(60, int(hours * 0.5)))
    cmd = f"gh pr list --repo {REPO} --base main --state merged --limit {limit} --json number,title,mergedAt,author,statusCheckRollup,reviews,latestReviews,files"
    output = run_command(cmd)
    if not output:
        return violations, all_merged_prs

    try:
        prs = json.loads(output)
    except Exception as e:
        print(f"Failed to parse PRs JSON: {e}")
        return violations, all_merged_prs

    now = datetime.now(timezone.utc)
    for pr in prs:
        merged_at = pr.get("mergedAt")
        merged_datetime = None
        if merged_at:
            try:
                merged_datetime = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
                if now - merged_datetime > timedelta(hours=hours):
                    break
            except Exception:
                pass

        number = pr.get("number")
        title = pr.get("title", "")
        author = pr.get("author", {}).get("login", "Unknown")
        reviews = pr.get("reviews", [])
        
        # Extract unique reviewers
        reviewers = set()
        for r in reviews:
            reviewer = r.get("author", {}).get("login")
            if reviewer and reviewer != author: # Exclude author from reviewers list if they reviewed their own PR
                reviewers.add(reviewer)
        
        reviewers_list = sorted(list(reviewers))

        # Extract approvers from latestReviews (fallback to reviews)
        approvers = set()
        for r in (pr.get("latestReviews") or reviews):
            if r.get("state") == "APPROVED":
                login = r.get("author", {}).get("login")
                if login and login != author:
                    approvers.add(login)

        # Group modified files by matching CODEOWNERS rule
        groups = {}
        for f in pr.get("files", []):
            f_path = f.get("path", "")
            if f_path:
                rule = match_codeowners_rule(f_path, codeowners_rules)
                if rule:
                    pat, owners = rule
                    if pat not in groups:
                        groups[pat] = {"owners": owners, "files": []}
                    groups[pat]["files"].append(f_path)

        # Check approval for each module group
        group_statuses = []
        approved_groups_count = 0
        all_req_owners = set()
        for pat, data in groups.items():
            owners = data["owners"]
            all_req_owners.update(owners)
            matched_approvers = sorted(list(approvers & set(owners)))
            if matched_approvers:
                approved_groups_count += 1
                group_statuses.append({
                    "pattern": pat,
                    "approved": True,
                    "approvers": matched_approvers,
                    "required_owners": owners
                })
            else:
                group_statuses.append({
                    "pattern": pat,
                    "approved": False,
                    "approvers": [],
                    "required_owners": owners
                })

        if not groups:
            codeowner_verdict = "NO_RULES"
        elif approved_groups_count == len(groups):
            codeowner_verdict = "ALL_APPROVED"
        elif approved_groups_count > 0:
            codeowner_verdict = "PARTIALLY_APPROVED"
        else:
            codeowner_verdict = "NOT_APPROVED"

        all_merged_prs.append({
            "number": number,
            "title": title,
            "author": author,
            "merged_at": merged_at,
            "reviewers": reviewers_list,
            "approvers": sorted(list(approvers)),
            "req_owners": sorted(list(all_req_owners)),
            "group_statuses": group_statuses,
            "approved_groups_count": approved_groups_count,
            "total_groups_count": len(groups),
            "codeowner_verdict": codeowner_verdict
        })

        # Rule Exemption: If PR title explicitly requests skipping CI, ignore check failures.
        if "skip-ci" in title.lower():
            continue

        checks = pr.get("statusCheckRollup", [])

        # Optimization: Check for empty checks (0 tests executed)
        if not checks:
            violations.append({
                "number": number,
                "title": title,
                "merged_at": merged_at,
                "author": author,
                "failed_checks": ["No CI status checks found on PR (Merged with 0 tests)"],
                "pending_checks": [],
                "timing_violations": []
            })
            continue

        failed_checks = []
        pending_checks = []
        timing_violations = []

        for check in checks:
            check_type = check.get("__typename", "")
            name = check.get("name", check.get("context", "Unknown Check"))

            if check_type == "StatusContext":
                state = check.get("state", "")
                if state in ("FAILURE", "ERROR"):
                    failed_checks.append(f"{name} ({state})")
                elif state == "PENDING":
                    pending_checks.append(f"{name} ({state})")
                elif state == "SUCCESS" and merged_datetime and check.get("startedAt"):
                    # Check if merged before external status was posted
                    try:
                        started_dt = datetime.fromisoformat(check["startedAt"].replace("Z", "+00:00"))
                        if merged_datetime < started_dt - timedelta(seconds=30):
                            diff_sec = int((started_dt - merged_datetime).total_seconds())
                            timing_violations.append(f"{name} (posted at {started_dt.strftime('%H:%M:%S UTC')}, merged {diff_sec}s prior)")
                    except Exception:
                        pass
            else:
                # CheckRun (GitHub Actions / Apps)
                status = check.get("status", "")
                conclusion = check.get("conclusion", "")
                # Ignore disabled/skipped legacy GHA TPU Presubmit Gate
                if name == "TPU Presubmit Gate" and conclusion in ("CANCELLED", "SKIPPED"):
                    continue

                # Comprehensive non-success check status handling
                if conclusion in ("FAILURE", "TIMED_OUT", "CANCELLED", "ACTION_REQUIRED", "STARTUP_FAILURE", "STALE"):
                    failed_checks.append(f"{name} ({conclusion})")
                elif status in ("IN_PROGRESS", "QUEUED", "PENDING", "WAITING", "REQUESTED") and not conclusion:
                    pending_checks.append(f"{name} ({status})")
                elif conclusion in ("SUCCESS", "NEUTRAL", "SKIPPED") and merged_datetime and check.get("completedAt"):
                    # Check if merged before CheckRun completed
                    try:
                        completed_dt = datetime.fromisoformat(check["completedAt"].replace("Z", "+00:00"))
                        if merged_datetime < completed_dt - timedelta(seconds=30):
                            diff_sec = int((completed_dt - merged_datetime).total_seconds())
                            timing_violations.append(f"{name} (completed at {completed_dt.strftime('%H:%M:%S UTC')}, merged {diff_sec}s prior)")
                    except Exception:
                        pass

        if failed_checks or pending_checks or timing_violations:
            violations.append({
                "number": number,
                "title": title,
                "merged_at": merged_at,
                "author": author,
                "failed_checks": failed_checks,
                "pending_checks": pending_checks,
                "timing_violations": timing_violations
            })

    return violations, all_merged_prs

def send_email_report(direct_pushes, premature_merges, all_merged_prs, recipients=None, bcc=True, sender=None):
    # Determine TL;DR status message
    if not direct_pushes and not premature_merges and not all_merged_prs:
        tldr_msg = "✅ No activity or governance violations detected!"
    elif direct_pushes or premature_merges:
        violations_summary = []
        if direct_pushes:
            violations_summary.append(f"{len(direct_pushes)} direct push(es)")
        if premature_merges:
            violations_summary.append(f"{len(premature_merges)} premature merge(s)")
        tldr_msg = f"🚨 Governance violations detected! ({', '.join(violations_summary)})"
    else:
        tldr_msg = f"✅ {len(all_merged_prs)} PR(s) merged with no governance violations detected."

    # Determine subject based on violations
    repo_short = REPO.split('/')[-1]
    if direct_pushes or premature_merges:
        subject = f"🚨 [Alert] {repo_short} Governance Violations!"
    else:
        subject = f"📊 [Summary] {repo_short} Daily Activity"

    # --- Generate Plain Text for Console ---
    text_body_lines = [
        f"Repository Governance Audit Report for {REPO}",
        f"Audit Time: {datetime.now(timezone.utc).isoformat()}",
        f"TL;DR: {tldr_msg}\n",
        "=" * 60,
    ]

    if all_merged_prs:
        text_body_lines.append(f"\n📊 Summary of Merged PRs ({len(all_merged_prs)} instances):")
        for v in all_merged_prs:
            reviewers_str = ", ".join([f"@{u}" for u in v['reviewers']]) if v['reviewers'] else "None"
            verdict = v.get('codeowner_verdict', 'NOT_APPROVED')
            approved_cnt = v.get('approved_groups_count', 0)
            total_cnt = v.get('total_groups_count', 0)

            if verdict == "ALL_APPROVED":
                owner_status = f"✅ All Owners Approved ({approved_cnt}/{total_cnt} modules)"
            elif verdict == "PARTIALLY_APPROVED":
                owner_status = f"⚠️ Partially Approved ({approved_cnt}/{total_cnt} modules)"
            else:
                owner_status = f"ℹ️ No Codeowner Approval ({approved_cnt}/{total_cnt} modules)"

            group_details = []
            for g in v.get('group_statuses', []):
                pat = g['pattern']
                if g['approved']:
                    group_details.append(f"{pat}: ✅ {'/'.join(['@' + a for a in g['approvers']])}")
                else:
                    group_details.append(f"{pat}: ❌ (Req: {', '.join(['@' + o for o in g['required_owners']])})")
            
            group_summary_str = " | ".join(group_details) if group_details else "None"

            text_body_lines.append(f"  - PR #{v['number']} (https://github.com/{REPO}/pull/{v['number']}) by @{v['author']}: '{v['title']}'")
            text_body_lines.append(f"    Reviewers: {reviewers_str} | CODEOWNERS: {owner_status}")
            if group_details:
                text_body_lines.append(f"    Modules: {group_summary_str}")
    else:
        text_body_lines.append("\nℹ️ No PRs merged in this period.")

    if direct_pushes:
        text_body_lines.append(f"\n🚨 Rule 1 Violation: Direct push to 'main' without PR ({len(direct_pushes)} instances):")
        for v in direct_pushes:
            text_body_lines.append(f"  - Commit {v['sha']} (https://github.com/{REPO}/commit/{v['sha']}) by {v['author']} on {v['date']}: {v['message']}")

    if premature_merges:
        text_body_lines.append(f"\n🚨 Rule 2 Violation: PR merged while CI failed, in-progress, or premature ({len(premature_merges)} instances):")
        for v in premature_merges:
            text_body_lines.append(f"\n  ▶ PR #{v['number']} (https://github.com/{REPO}/pull/{v['number']}) by @{v['author']}: '{v['title']}' (Merged at {v['merged_at']})")
            if v.get('failed_checks'):
                text_body_lines.append(f"    Failing/Non-Passing Checks: {', '.join(v['failed_checks'])}")
            if v.get('pending_checks'):
                text_body_lines.append(f"    Pending/In-Flight Checks: {', '.join(v['pending_checks'])}")
            if v.get('timing_violations'):
                text_body_lines.append(f"    Merged Before Checks Finished: {', '.join(v['timing_violations'])}")

    text_body = "\n".join(text_body_lines)
    print("\n" + text_body)

    # --- Generate HTML for Email ---
    audit_time_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    
    html_body = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; max-width: 900px; margin: auto; border: 1px solid #e1e4e8; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <div style="background-color: {'#d9534f' if direct_pushes or premature_merges else '#5bc0de'}; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">{'🚨 Governance Audit Alert' if direct_pushes or premature_merges else '📊 Daily Repository Summary'}</h1>
            <p style="margin: 5px 0 0 0; opacity: 0.9;">{REPO}</p>
        </div>
        
        <div style="padding: 20px; background-color: #f9f9f9;">
            <p style="margin: 0 0 8px 0; color: #666;"><strong>Audit Time:</strong> {audit_time_str}</p>
            <p style="margin: 0; color: #333; font-size: 1.05em;"><strong>TL;DR:</strong> {tldr_msg}</p>
        </div>

        <div style="padding: 20px;">
    """

    # Summary Section
    html_body += """
            <div style="margin-bottom: 30px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #5bc0de; padding-bottom: 8px; margin-top: 0;">📊 Merged PRs Summary</h2>
    """
    if all_merged_prs:
        html_body += """
                <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                    <thead>
                        <tr style="background-color: #f2f2f2; text-align: left;">
                            <th style="padding: 12px; border: 1px solid #ddd;">PR</th>
                            <th style="padding: 12px; border: 1px solid #ddd;">Author</th>
                            <th style="padding: 12px; border: 1px solid #ddd;">Title</th>
                            <th style="padding: 12px; border: 1px solid #ddd;">Reviewers</th>
                            <th style="padding: 12px; border: 1px solid #ddd; text-align: center; min-width: 220px;">CODEOWNER Approved (Per Module)</th>
                        </tr>
                    </thead>
                    <tbody>
        """
        for pr in all_merged_prs:
            reviewers_str = ", ".join([f'<span style="background-color: #e6f3ff; padding: 2px 6px; border-radius: 4px; font-size: 0.9em;">@{u}</span>' for u in pr['reviewers']]) if pr['reviewers'] else '<span style="color: #999;">None</span>'
            verdict = pr.get('codeowner_verdict', 'NOT_APPROVED')
            approved_cnt = pr.get('approved_groups_count', 0)
            total_cnt = pr.get('total_groups_count', 0)

            if verdict == "ALL_APPROVED":
                header_badge = f'<span style="background-color: #d4edda; color: #155724; border: 1px solid #c3e6cb; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; font-weight: bold;">✅ All Approved ({approved_cnt}/{total_cnt})</span>'
            elif verdict == "PARTIALLY_APPROVED":
                header_badge = f'<span style="background-color: #fff3cd; color: #856404; border: 1px solid #ffeeba; padding: 2px 6px; border-radius: 4px; font-size: 0.85em; font-weight: bold;">⚠️ Partial ({approved_cnt}/{total_cnt})</span>'
            else:
                header_badge = f'<span style="background-color: #f8f9fa; color: #6c757d; border: 1px solid #ddd; padding: 2px 6px; border-radius: 4px; font-size: 0.85em;">ℹ️ None ({approved_cnt}/{total_cnt})</span>'

            # Build list of module items
            group_html_items = []
            for g in pr.get('group_statuses', []):
                pat_name = f"<code style='font-size:0.9em; background:#eee; padding:1px 3px; border-radius:2px;'>{g['pattern']}</code>"
                if g['approved']:
                    app_str = ", ".join([f"@{a}" for a in g['approvers']])
                    group_html_items.append(f"<li style='margin-bottom:2px;'>{pat_name}: <span style='color:#28a745; font-weight:bold;'>✅ {app_str}</span></li>")
                else:
                    req_str = ", ".join([f"@{o}" for o in g['required_owners']])
                    group_html_items.append(f"<li style='margin-bottom:2px;'>{pat_name}: <span style='color:#dc3545;'>❌</span> <span style='color:#777;'>({req_str})</span></li>")

            module_list_html = f"<ul style='margin: 4px 0 0 0; padding-left: 16px; font-size: 0.8em; text-align: left; list-style-type: disc;'>" + "".join(group_html_items) + "</ul>" if group_html_items else ""

            owner_cell_content = f"""
                <div style="margin-bottom: 3px; text-align: center;">{header_badge}</div>
                {module_list_html}
            """

            html_body += f"""
                        <tr style="border-bottom: 1px solid #ddd; vertical-align: top;">
                            <td style="padding: 12px; border: 1px solid #ddd;"><a href="https://github.com/{REPO}/pull/{pr['number']}" style="color: #0366d6; text-decoration: none; font-weight: bold;">#{pr['number']}</a></td>
                            <td style="padding: 12px; border: 1px solid #ddd;"><strong>@{pr['author']}</strong></td>
                            <td style="padding: 12px; border: 1px solid #ddd;">{pr['title']}</td>
                            <td style="padding: 12px; border: 1px solid #ddd;">{reviewers_str}</td>
                            <td style="padding: 12px; border: 1px solid #ddd;">{owner_cell_content}</td>
                        </tr>
            """
        html_body += """
                    </tbody>
                </table>
        """
    else:
        html_body += """
                <p style="color: #777; font-style: italic;">No PRs merged in this period.</p>
        """
    html_body += "</div>"

    # Violations Section (Rule 1)
    if direct_pushes:
        html_body += """
            <div style="margin-bottom: 30px; border: 1px solid #ebccd1; border-radius: 4px; background-color: #f2dede; padding: 15px;">
                <h2 style="color: #a94442; margin-top: 0; border-bottom: 1px solid #ebccd1; padding-bottom: 8px;">🚨 Rule 1 Violation: Direct Push to 'main'</h2>
                <ul style="padding-left: 20px; color: #a94442;">
        """
        for v in direct_pushes:
            html_body += f"""
                    <li style="margin-bottom: 10px;">
                        <strong>Commit:</strong> <a href="https://github.com/{REPO}/commit/{v['sha']}" style="color: #843534; font-family: monospace;">{v['sha']}</a> by <strong>@{v['author']}</strong> on <em>{v['date']}</em><br>
                        <span style="font-style: italic;">"{v['message']}"</span>
                    </li>
            """
        html_body += """
                </ul>
            </div>
        """

    # Violations Section (Rule 2)
    if premature_merges:
        html_body += """
            <div style="margin-bottom: 30px; border: 1px solid #ebccd1; border-radius: 4px; background-color: #f2dede; padding: 15px;">
                <h2 style="color: #a94442; margin-top: 0; border-bottom: 1px solid #ebccd1; padding-bottom: 8px;">🚨 Rule 2 Violation: Premature Merge (CI Failed / In-Flight / Premature)</h2>
        """
        for v in premature_merges:
            html_body += f"""
                <div style="background-color: white; border: 1px solid #ddd; padding: 12px; border-radius: 4px; margin-bottom: 15px;">
                    <p style="margin: 0 0 8px 0;">
                        <a href="https://github.com/{REPO}/pull/{v['number']}" style="color: #d9534f; font-size: 1.1em; font-weight: bold; text-decoration: none;">PR #{v['number']}</a> by <strong>@{v['author']}</strong><br>
                        <span style="color: #333; font-weight: bold;">{v['title']}</span>
                        <span style="color: #777; font-size: 0.9em; margin-left: 8px;">(Merged: {v.get('merged_at', 'N/A')})</span>
                    </p>
            """
            if v.get('failed_checks'):
                html_body += """
                    <p style="margin: 0 0 5px 0; color: #a94442;"><strong>❌ Failing/Non-Passing Checks:</strong></p>
                    <ul style="margin: 0 0 10px 0; padding-left: 20px; color: #a94442;">
                """
                for c in v['failed_checks']:
                    html_body += f"<li>{c}</li>"
                html_body += "</ul>"

            if v.get('pending_checks'):
                html_body += """
                    <p style="margin: 0 0 5px 0; color: #eea236;"><strong>⏳ Pending/In-Flight Checks:</strong></p>
                    <ul style="margin: 0 0 10px 0; padding-left: 20px; color: #8a6d3b;">
                """
                for c in v['pending_checks']:
                    html_body += f"<li>{c}</li>"
                html_body += "</ul>"

            if v.get('timing_violations'):
                html_body += """
                    <p style="margin: 0 0 5px 0; color: #d9534f;"><strong>⏱️ Merged Before Checks Finished (Timing Violation):</strong></p>
                    <ul style="margin: 0; padding-left: 20px; color: #a94442;">
                """
                for c in v['timing_violations']:
                    html_body += f"<li>{c}</li>"
                html_body += "</ul>"
            
            html_body += "</div>"
        html_body += "</div>"

    html_body += """
        </div>
        <div style="background-color: #f5f5f5; color: #777; padding: 15px; text-align: center; font-size: 0.9em; border-top: 1px solid #e5e5e5;">
            This is an automated report. Please do not reply directly.
        </div>
    </div>
    """

    if not recipients:
        recipients = [DEFAULT_RECIPIENT]
    elif isinstance(recipients, str):
        recipients = [r.strip() for r in recipients.split(",") if r.strip()]

    if not sender:
        sender = DEFAULT_SENDER

    tool_path = shutil.which("sendgmr") or "/usr/local/google/home/johnqiangzhang/bin/sendgmr"
    if not (tool_path and os.path.exists(tool_path)):
        g3_dir = "/google/src/cloud/johnqiangzhang/vllm/google3"
        candidate = f"{g3_dir}/blaze-bin/caribou/delivery/go/sendgmr"
        if os.path.exists(candidate):
            tool_path = candidate
        elif os.path.exists(g3_dir):
            print("\nsendgmr binary not found. Automatically building it in google3...")
            run_command("blaze build //caribou/delivery/go:sendgmr", cwd=g3_dir)
            if os.path.exists(candidate):
                tool_path = candidate

    if not (tool_path and os.path.exists(tool_path)):
        print("\nError: Neither sendgmr nor build path could be located.", file=sys.stderr)
        return

    html_path = "/tmp/audit_report.html"
    text_path = "/tmp/audit_report.txt"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_body)
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(text_body)

    recipients_str = ",".join(recipients)
    if bcc:
        # Extract plain email address from sender for --to in BCC mode (fallback to DEFAULT_RECIPIENT)
        m = re.search(r'<([^>]+)>', sender)
        primary_to = m.group(1) if m else DEFAULT_RECIPIENT

        # Exclude primary_to from BCC list to avoid duplicate delivery
        bcc_list = [r for r in recipients if r != primary_to]

        cmd = [
            tool_path,
            f"--from={sender}",
            f"--to={primary_to}",
            f"--subject={subject}",
            f"--html_file={html_path}",
            f"--body_file={text_path}",
        ]
        if bcc_list:
            cmd.append(f"--bcc={','.join(bcc_list)}")
    else:
        cmd = [
            tool_path,
            f"--from={sender}",
            f"--to={recipients_str}",
            f"--subject={subject}",
            f"--html_file={html_path}",
            f"--body_file={text_path}",
        ]

    res = run_command(cmd)
    if res is not None:
        mode_str = "BCC" if bcc else "To"
        print(f"\nAudit report email successfully sent to {len(recipients)} recipient(s) ({mode_str}): {', '.join(recipients)}!")
    else:
        print("\nFailed to send audit report email.", file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description=f"Audit repository governance for {REPO}.")
    parser.add_argument(
        "--hours",
        type=float,
        default=24.0,
        help="Time window in hours to audit (default: 24.0)"
    )
    parser.add_argument(
        "--sender",
        type=str,
        default=DEFAULT_SENDER,
        help=f"Sender email address (default: {DEFAULT_SENDER})"
    )
    parser.add_argument(
        "--recipients",
        type=str,
        default=None,
        help=f"Comma-separated list of recipient email addresses (default: {DEFAULT_RECIPIENT})"
    )
    parser.add_argument(
        "--recipients-csv",
        type=str,
        default=None,
        help="Path to a CSV file containing recipient email addresses"
    )
    parser.add_argument(
        "--bcc",
        action="store_true",
        default=True,
        help="Send email as BCC to all recipients (default: True)"
    )
    parser.add_argument(
        "--no-bcc",
        dest="bcc",
        action="store_false",
        help="Disable BCC mode and put all recipients in 'To:' header"
    )
    args = parser.parse_args()

    recipients = load_recipients(cli_recipients=args.recipients, csv_path=args.recipients_csv)

    print(f"Auditing repository {REPO} for the last {args.hours} hours...")
    print(f"Sender: {args.sender}")
    print(f"Recipients: {', '.join(recipients)} (BCC: {args.bcc})")
    direct_pushes = check_direct_pushes(args.hours)
    premature_merges, all_merged_prs = check_premature_merges(args.hours)
    send_email_report(direct_pushes, premature_merges, all_merged_prs, recipients=recipients, bcc=args.bcc, sender=args.sender)

if __name__ == "__main__":
    main()
