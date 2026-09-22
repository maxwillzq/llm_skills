#!/usr/bin/env python3
"""fix_vllm_torchtpu_ci.py - Fix failing CI for vllm-torchtpu via Jetski Agent."""

import argparse
import os
import re
import subprocess

REPO = "vllm-project/vllm-torchtpu"
CLI = "/google/bin/releases/jetski-devs/tools/cli"


def main() -> None:
    parser = argparse.ArgumentParser(description="Fix vllm-torchtpu PR CI failure.")
    parser.add_argument("pr", help="PR number or URL")
    parser.add_argument("--auto", action="store_true", help="Fully unattended mode (no interactive prompt confirmations)")
    parser.add_argument("--dry-run", action="store_true", help="Print prompt and exit")
    args = parser.parse_args()

    m = re.search(r"/pull/(\d+)", args.pr)
    pr_num = int(m.group(1)) if m else int(args.pr)

    work_dir = os.path.expanduser(f"~/projects/{REPO.split('/')[-1]}")
    prompt = f"Use the `llm-tools` skill to investigate and fix the failing CI for {REPO} PR #{pr_num}."

    # --dangerously-skip-permissions: auto-approves tool requests
    # --mode=accept-edits: auto-accepts code modifications
    flag = "-p" if args.auto else "-i"
    cmd = [CLI, "--dangerously-skip-permissions", "--mode=accept-edits", flag, prompt]

    if args.dry_run:
        print(f"Directory: {work_dir}")
        print(f"Prompt:    {prompt}")
        print(f"Command:   {' '.join(cmd)}")
        return

    subprocess.run(cmd, cwd=work_dir)


if __name__ == "__main__":
    main()
