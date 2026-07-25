#!/usr/bin/env python3
import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

REPO = "vllm-project/vllm-torchtpu"
DEFAULT_RECIPIENT = "johnqiangzhang@google.com"

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
    output = run_command(f"gh api repos/{REPO}/commits?per_page=30")
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

def check_premature_merges(hours):
    """Rule 2: Detect PRs merged while CI checks were failing or in progress."""
    violations = []
    all_merged_prs = []
    cmd = f"gh pr list --repo {REPO} --state merged --limit 20 --json number,title,mergedAt,author,statusCheckRollup,reviews"
    output = run_command(cmd)
    if not output:
        return violations

    try:
        prs = json.loads(output)
    except Exception as e:
        print(f"Failed to parse PRs JSON: {e}")
        return violations

    now = datetime.now(timezone.utc)
    for pr in prs:
        merged_at = pr.get("mergedAt")
        if merged_at:
            try:
                merged_datetime = datetime.fromisoformat(merged_at.replace("Z", "+00:00"))
                if now - merged_datetime > timedelta(hours=hours):
                    break
            except Exception:
                pass

        number = pr.get("number")
        title = pr.get("title", "")
        merged_at = pr.get("mergedAt")
        author = pr.get("author", {}).get("login", "Unknown")
        reviews = pr.get("reviews", [])
        
        # Extract unique reviewers
        reviewers = set()
        for r in reviews:
            reviewer = r.get("author", {}).get("login")
            if reviewer and reviewer != author: # Exclude author from reviewers list if they reviewed their own PR (rare but possible)
                reviewers.add(reviewer)
        
        reviewers_list = sorted(list(reviewers))

        all_merged_prs.append({
            "number": number,
            "title": title,
            "author": author,
            "merged_at": merged_at,
            "reviewers": reviewers_list
        })

        # Rule Exemption: If PR title explicitly requests skipping CI, ignore check failures.
        if "skip-ci" in title.lower():
            continue

        checks = pr.get("statusCheckRollup", [])

        failed_checks = []
        pending_checks = []
        for check in checks:
            check_type = check.get("__typename", "")
            name = check.get("name", check.get("context", "Unknown Check"))

            if check_type == "StatusContext":
                state = check.get("state", "")
                if state in ("FAILURE", "ERROR"):
                    failed_checks.append(f"{name} ({state})")
                elif state == "PENDING":
                    pending_checks.append(f"{name} ({state})")
            else:
                # CheckRun (GitHub Actions)
                status = check.get("status", "")
                conclusion = check.get("conclusion", "")
                # Ignore disabled/skipped legacy GHA TPU Presubmit Gate
                if name == "TPU Presubmit Gate" and conclusion in ("CANCELLED", "SKIPPED"):
                    continue
                if conclusion == "FAILURE":
                    failed_checks.append(f"{name} ({conclusion})")
                elif status in ("IN_PROGRESS", "QUEUED", "PENDING") and not conclusion:
                    pending_checks.append(f"{name} ({status})")

        if failed_checks or pending_checks:
            violations.append({
                "number": number,
                "title": title,
                "merged_at": merged_at,
                "author": author,
                "failed_checks": failed_checks,
                "pending_checks": pending_checks
            })

    return violations, all_merged_prs

def send_email_report(direct_pushes, premature_merges, all_merged_prs, recipients=None, bcc=True):
    if not direct_pushes and not premature_merges and not all_merged_prs:
        print("\n✅ No activity or governance violations detected! Skipping email report.")
        return

    # Determine subject based on violations
    repo_short = REPO.split('/')[-1]
    if direct_pushes or premature_merges:
        subject = f"🚨 [Alert] {repo_short} Governance Violations!"
    else:
        subject = f"📊 [Summary] {repo_short} Daily Activity"

    # --- Generate Plain Text for Console ---
    text_body_lines = [
        f"Repository Governance Audit Report for {REPO}",
        f"Audit Time: {datetime.now(timezone.utc).isoformat()}\n",
        "=" * 60,
    ]

    if all_merged_prs:
        text_body_lines.append(f"\n📊 Summary of Merged PRs ({len(all_merged_prs)} instances):")
        for v in all_merged_prs:
            reviewers_str = ", ".join([f"@{u}" for u in v['reviewers']]) if v['reviewers'] else "None"
            text_body_lines.append(f"  - PR #{v['number']} (https://github.com/{REPO}/pull/{v['number']}) by @{v['author']}: '{v['title']}' (Reviewers: {reviewers_str})")
    else:
        text_body_lines.append("\nℹ️ No PRs merged in this period.")

    if direct_pushes:
        text_body_lines.append(f"\n🚨 Rule 1 Violation: Direct push to 'main' without PR ({len(direct_pushes)} instances):")
        for v in direct_pushes:
            text_body_lines.append(f"  - Commit {v['sha']} (https://github.com/{REPO}/commit/{v['sha']}) by {v['author']} on {v['date']}: {v['message']}")

    if premature_merges:
        text_body_lines.append(f"\n🚨 Rule 2 Violation: PR merged while CI failed or in-progress ({len(premature_merges)} instances):")
        for v in premature_merges:
            text_body_lines.append(f"\n  ▶ PR #{v['number']} (https://github.com/{REPO}/pull/{v['number']}) by @{v['author']}: '{v['title']}' (Merged at {v['merged_at']})")
            if v['failed_checks']:
                text_body_lines.append(f"    Failing Checks: {', '.join(v['failed_checks'])}")
            if v['pending_checks']:
                text_body_lines.append(f"    Pending Checks: {', '.join(v['pending_checks'])}")

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
            <p style="margin: 0; color: #666;"><strong>Audit Time:</strong> {audit_time_str}</p>
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
                        </tr>
                    </thead>
                    <tbody>
        """
        for pr in all_merged_prs:
            reviewers_str = ", ".join([f'<span style="background-color: #e6f3ff; padding: 2px 6px; border-radius: 4px; font-size: 0.9em;">@{u}</span>' for u in pr['reviewers']]) if pr['reviewers'] else '<span style="color: #999;">None</span>'
            html_body += f"""
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 12px; border: 1px solid #ddd;"><a href="https://github.com/{REPO}/pull/{pr['number']}" style="color: #0366d6; text-decoration: none; font-weight: bold;">#{pr['number']}</a></td>
                            <td style="padding: 12px; border: 1px solid #ddd;"><strong>@{pr['author']}</strong></td>
                            <td style="padding: 12px; border: 1px solid #ddd;">{pr['title']}</td>
                            <td style="padding: 12px; border: 1px solid #ddd;">{reviewers_str}</td>
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
                <h2 style="color: #a94442; margin-top: 0; border-bottom: 1px solid #ebccd1; padding-bottom: 8px;">🚨 Rule 2 Violation: Premature Merge (CI Failed/Pending)</h2>
        """
        for v in premature_merges:
            html_body += f"""
                <div style="background-color: white; border: 1px solid #ddd; padding: 12px; border-radius: 4px; margin-bottom: 15px;">
                    <p style="margin: 0 0 8px 0;">
                        <a href="https://github.com/{REPO}/pull/{v['number']}" style="color: #d9534f; font-size: 1.1em; font-weight: bold; text-decoration: none;">PR #{v['number']}</a> by <strong>@{v['author']}</strong><br>
                        <span style="color: #333; font-weight: bold;">{v['title']}</span>
                    </p>
            """
            if v['failed_checks']:
                html_body += """
                    <p style="margin: 0 0 5px 0; color: #a94442;"><strong>❌ Failing Checks:</strong></p>
                    <ul style="margin: 0 0 10px 0; padding-left: 20px; color: #a94442;">
                """
                for c in v['failed_checks']:
                    html_body += f"<li>{c}</li>"
                html_body += "</ul>"

            if v['pending_checks']:
                html_body += """
                    <p style="margin: 0 0 5px 0; color: #eea236;"><strong>⏳ Pending Checks:</strong></p>
                    <ul style="margin: 0; padding-left: 20px; color: #8a6d3b;">
                """
                for c in v['pending_checks']:
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

    sender = DEFAULT_RECIPIENT

    g3_dir = "/google/src/cloud/johnqiangzhang/vllm/google3"
    tool_path = f"{g3_dir}/blaze-bin/caribou/delivery/tools/send_rfc822"
    if not os.path.exists(tool_path):
        print("\nsend_rfc822 binary not found in blaze-bin. Automatically building it in google3...")
        run_command("blaze build //caribou/delivery/tools:send_rfc822", cwd=g3_dir)

    success_count = 0
    for target in recipients:
        to_header = target if bcc else ", ".join(recipients)
        eml_content = f"""From: {sender}
To: {to_header}
Subject: {subject}
MIME-Version: 1.0
Content-Type: text/html; charset=utf-8

{html_body}
"""
        with open("/tmp/audit_report.eml", "w") as f:
            f.write(eml_content)

        send_cmd = f"{tool_path} --to {target} --rfc822_path /tmp/audit_report.eml"
        res = run_command(send_cmd)
        if res is not None:
            success_count += 1

    if success_count > 0:
        print(f"\nAudit report email successfully sent to {success_count} recipient(s): {', '.join(recipients)}!")

def main():
    parser = argparse.ArgumentParser(description=f"Audit repository governance for {REPO}.")
    parser.add_argument(
        "--hours",
        type=float,
        default=24.0,
        help="Time window in hours to audit (default: 24.0)"
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
    print(f"Recipients: {', '.join(recipients)} (BCC: {args.bcc})")
    direct_pushes = check_direct_pushes(args.hours)
    premature_merges, all_merged_prs = check_premature_merges(args.hours)
    send_email_report(direct_pushes, premature_merges, all_merged_prs, recipients=recipients, bcc=args.bcc)

if __name__ == "__main__":
    main()
