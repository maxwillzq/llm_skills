import csv
import subprocess
import json
import os

csv_file = '/usr/local/google/home/johnqiangzhang/projects/llm_skills/skills/llm_tools/references/merged_developers.csv'

# 1. Read existing CSV to avoid duplicates
existing_handles = set()
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)
    gh_idx = header.index('GitHub Account')
    for row in reader:
        if len(row) > gh_idx:
            existing_handles.add(row[gh_idx].lower())

# 2. Fetch pending invitations from GitHub
print("Fetching pending invitations...")
res = subprocess.run(["gh", "api", "repos/vllm-project/vllm-torchtpu/invitations", "--paginate"], capture_output=True, text=True)
if res.returncode != 0:
    print("Error fetching invitations:", res.stderr)
    exit(1)

invitations = json.loads(res.stdout)

missing_invitees = []

for inv in invitations:
    invitee = inv.get('invitee')
    if invitee:
        handle = invitee.get('login')
        permission = inv.get('permissions')
        if handle and handle.lower() not in existing_handles:
            missing_invitees.append({
                'handle': handle,
                'permission': permission
            })

print(f"Found {len(missing_invitees)} missing invitees from invitations.")

# 3. Fetch user details for missing invitees and append to CSV
if missing_invitees:
    with open(csv_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        for missing in missing_invitees:
            handle = missing['handle']
            permission = missing['permission']
            
            print(f"Fetching details for {handle}...")
            user_res = subprocess.run(["gh", "api", f"users/{handle}"], capture_output=True, text=True)
            company = 'NULL'
            email = 'NULL'
            if user_res.returncode == 0:
                user_data = json.loads(user_res.stdout)
                company = user_data.get('company') or 'NULL'
                email = user_data.get('email') or 'NULL'
            
            # Map permission to CSV format (push -> write, pull -> read etc)
            csv_perm = permission
            if permission == 'push':
                csv_perm = 'write'
            elif permission == 'pull':
                csv_perm = 'read'
            
            # Determine Type roughly based on email or company
            dev_type = 'External Contributor'
            if 'google' in company.lower() or 'google' in email.lower():
                dev_type = 'Internal Developer'
            
            # Row order: Type, LDAP / Email, GitHub Account, Company, Permission, Interested Areas, Code Review, Notes
            row = [
                dev_type,
                email,
                handle,
                company,
                csv_perm,
                'NULL', # Interested Areas
                'NULL', # Code Review
                'Pending Invitation (Added via Script)'
            ]
            
            writer.writerow(row)
            print(f"Added {handle} to CSV.")
else:
    print("No missing invitees to add.")

print("Done.")
