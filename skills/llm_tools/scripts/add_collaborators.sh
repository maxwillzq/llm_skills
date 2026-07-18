#!/usr/bin/env bash
#
# Script to batch invite/add GitHub users to a repository with specified permissions.
# Parses CSV files (auto-detecting 'GitHub Account' / 'GitHub Handle' columns), text files, or CLI arguments.
# Note: Dry-run is ENABLED BY DEFAULT for safety. Pass --execute or -x to apply changes.
#
# Usage:
#   add_collaborators.sh [options] [user1 user2 ...]
#   add_collaborators.sh -f merged_developers.csv
#   cat user_list.txt | add_collaborators.sh -x

set -euo pipefail

# Configuration defaults
REPO="vllm-project/vllm-torchtpu"
PERMISSION="push"  # 'push' corresponds to Write access in GitHub API
FILE_INPUT=""
DRY_RUN=true
RAW_INPUT=()

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS] [USERS / CSV FILE / LIST...]

Batch add or invite collaborators to a GitHub repository.
Safely extracts GitHub accounts from CSV files (auto-matching 'GitHub Account'), URLs, @mentions, or text files.

Default behavior: DRY-RUN mode is active by default to prevent accidental invites.
Use --execute (-x) to apply changes.

Options:
  -x, --execute              Execute actual API invitations (disables default dry-run mode)
  -d, --dry-run              Explicitly run in dry-run mode (default behavior)
  -r, --repo OWNER/REPO      Target repository (default: $REPO)
  -p, --permission PERM      Permission level: push (write), pull (read), maintain, admin, triage (default: $PERMISSION)
  -f, --file FILE            CSV file (e.g. merged_developers.csv) or text file containing GitHub handles
  -h, --help                 Display this help message

Examples:
  # Dry run test on CSV file (default)
  $(basename "$0") -f merged_developers.csv

  # Execute live invitations on repository
  $(basename "$0") --execute -f merged_developers.csv

  # Direct handles test
  $(basename "$0") octocat @alice https://github.com/bob
EOF
    exit 0
}

# Parse CLI options
while [[ $# -gt 0 ]]; do
    case "$1" in
        -x|--execute|--apply)
            DRY_RUN=false
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -r|--repo)
            REPO="$2"
            shift 2
            ;;
        -p|--permission)
            PERMISSION="$2"
            shift 2
            ;;
        -f|--file)
            FILE_INPUT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        -*)
            echo -e "${RED}Error: Unknown option $1${NC}" >&2
            usage
            ;;
        *)
            RAW_INPUT+=("$1")
            shift
            ;;
    esac
done

RAW_TEXT=""

# Read input from file if specified
if [[ -n "$FILE_INPUT" ]]; then
    if [[ ! -f "$FILE_INPUT" ]]; then
        echo -e "${RED}Error: File '$FILE_INPUT' not found.${NC}" >&2
        exit 1
    fi
    RAW_TEXT+=$(cat "$FILE_INPUT")
    RAW_TEXT+=$'\n'
fi

# Append CLI user arguments
if [[ ${#RAW_INPUT[@]} -gt 0 ]]; then
    RAW_TEXT+="${RAW_INPUT[*]}"
    RAW_TEXT+=$'\n'
fi

# Read stdin if no arguments/file were passed and stdin is piped
if [[ -z "$FILE_INPUT" ]] && [[ ${#RAW_INPUT[@]} -eq 0 ]] && [[ ! -t 0 ]]; then
    RAW_TEXT+=$(cat)
fi

if [[ -z "$(echo "$RAW_TEXT" | tr -d '[:space:]')" ]]; then
    echo -e "${RED}Error: No input text or GitHub usernames provided.${NC}" >&2
    echo "Provide usernames as arguments, via -f/--file, or pipe them into the script." >&2
    exit 1
fi

# Intelligent CSV and multi-format parsing:
# Automatically detects CSV headers ('GitHub Account', 'Permission')
# and extracts per-row GitHub account handles and target permissions.
CLEANED_USERS=()
declare -A SEEN=()
declare -A USER_TARGET_PERM=()

GH_COL_IDX=""
PERM_COL_IDX=""

# Helper function to assign numeric weights to permission roles
get_perm_weight() {
    case "$(echo "$1" | tr '[:upper:]' '[:lower:]')" in
        admin) echo 5 ;;
        maintain) echo 4 ;;
        push|write) echo 3 ;;
        triage) echo 2 ;;
        pull|read) echo 1 ;;
        *) echo 0 ;;
    esac
}

# Check if first non-comment, non-empty line looks like a CSV header containing fields
FIRST_LINE=$(echo "$RAW_TEXT" | grep -v '^[[:space:]]*#' | grep -v '^[[:space:]]*$' | head -n 1 || true)

if [[ "$FIRST_LINE" == *","* ]]; then
    IFS=',' read -r -a HEADERS <<< "$FIRST_LINE"
    for idx in "${!HEADERS[@]}"; do
        clean_hdr=$(echo "${HEADERS[$idx]}" | tr -d '"'\''\r' | sed -E 's/^[[:space:]]*//; s/[[:space:]]*$//' | tr '[:upper:]' '[:lower:]')
        if [[ "$clean_hdr" == *"github"* ]]; then
            GH_COL_IDX=$idx
        elif [[ "$clean_hdr" == *"permission"* ]] || [[ "$clean_hdr" == *"role"* ]]; then
            PERM_COL_IDX=$idx
        fi
    done
fi

if [[ -n "$GH_COL_IDX" ]]; then
    # CSV format detected
    IS_HEADER=true
    while IFS= read -r line || [[ -n "$line" ]]; do
        line=$(echo "$line" | sed -e 's/#.*//')
        [[ -z "$(echo "$line" | tr -d '[:space:]')" ]] && continue

        if [[ "$IS_HEADER" == true ]]; then
            IS_HEADER=false
            continue
        fi

        IFS=',' read -r -a FIELDS <<< "$line"
        raw_val="${FIELDS[$GH_COL_IDX]:-}"
        raw_val=$(echo "$raw_val" | tr -d '"'\''\r')
        
        clean_user=$(echo "$raw_val" | sed -E 's|^[@[:punct:]]+||g; s|[[:punct:]]+$||g')

        # Determine per-row target permission
        row_perm="$PERMISSION"
        if [[ -n "$PERM_COL_IDX" ]]; then
            raw_p="${FIELDS[$PERM_COL_IDX]:-}"
            raw_p=$(echo "$raw_p" | tr -d '"'\''\r' | tr '[:upper:]' '[:lower:]' | sed -E 's/^[[:space:]]*//; s/[[:space:]]*$//')
            case "$raw_p" in
                admin) row_perm="admin" ;;
                maintain) row_perm="maintain" ;;
                write|push) row_perm="push" ;;
                read|pull) row_perm="pull" ;;
                triage) row_perm="triage" ;;
            esac
        fi

        if [[ "$clean_user" =~ ^[a-zA-Z0-9][-a-zA-Z0-9]{0,38}$ ]]; then
            lower_user=$(echo "$clean_user" | tr '[:upper:]' '[:lower:]')
            if [[ -z "${SEEN[$lower_user]:-}" ]]; then
                SEEN[$lower_user]=1
                CLEANED_USERS+=("$clean_user")
                USER_TARGET_PERM["$lower_user"]="$row_perm"
            fi
        fi
    done <<< "$RAW_TEXT"
else
    # Plain text / list parsing
    while IFS= read -r line || [[ -n "$line" ]]; do
        line=$(echo "$line" | sed -e 's/#.*//')
        [[ -z "$(echo "$line" | tr -d '[:space:]')" ]] && continue

        tokens=$(echo "$line" | tr ',;\t:' '    ')

        for token in $tokens; do
            clean_user=$(echo "$token" | sed -E 's|^[@[:punct:]]+||g; s|[[:punct:]]+$||g')
            if [[ "$clean_user" =~ ^[a-zA-Z0-9][-a-zA-Z0-9]{0,38}$ ]]; then
                lower_user=$(echo "$clean_user" | tr '[:upper:]' '[:lower:]')
                if [[ -z "${SEEN[$lower_user]:-}" ]]; then
                    SEEN[$lower_user]=1
                    CLEANED_USERS+=("$clean_user")
                    USER_TARGET_PERM["$lower_user"]="$PERMISSION"
                fi
            fi
        done
    done <<< "$RAW_TEXT"
fi

if [[ ${#CLEANED_USERS[@]} -eq 0 ]]; then
    echo -e "${RED}Error: Could not parse any valid GitHub usernames from the input.${NC}" >&2
    exit 1
fi

# Pre-flight check: gh CLI installed and authenticated
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed.${NC}" >&2
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: Not logged in to GitHub CLI. Please run 'gh auth login'.${NC}" >&2
    exit 1
fi

echo -e "${BLUE}=== GitHub Collaborator Inviter ===${NC}"
echo "Target Repository : $REPO"
echo "Default Permission: $PERMISSION"
echo "Parsed Handles (${#CLEANED_USERS[@]}) : ${CLEANED_USERS[*]}"
if [[ "$DRY_RUN" == true ]]; then
    echo -e "Execution Mode    : ${YELLOW}${BOLD}DRY-RUN (Safe mode - no API calls made)${NC}"
else
    echo -e "Execution Mode    : ${RED}${BOLD}LIVE (Applying invitations to GitHub)${NC}"
fi
echo "-----------------------------------"

SUCCESS_COUNT=0
SKIP_COUNT=0
FAIL_COUNT=0

for username in "${CLEANED_USERS[@]}"; do
    lower_name=$(echo "$username" | tr '[:upper:]' '[:lower:]')
    target_perm="${USER_TARGET_PERM[$lower_name]:-$PERMISSION}"

    echo -n "Checking '$username' (Target: '$target_perm')... "

    # Read-only permission check via gh api --jq
    curr_perm=$(gh api "repos/$REPO/collaborators/$username/permission" --jq '.permission' 2>/dev/null || echo "none")

    curr_weight=$(get_perm_weight "$curr_perm")
    target_weight=$(get_perm_weight "$target_perm")

    # Guard against downgrading existing access or repeating unnecessary updates
    if [[ $curr_weight -ge $target_weight ]] && [[ "$curr_perm" != "none" ]]; then
        echo -e "${YELLOW}SKIPPED (Current role '$curr_perm' >= target role '$target_perm')${NC}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        SKIP_COUNT=$((SKIP_COUNT + 1))
        continue
    fi

    if [[ "$DRY_RUN" == true ]]; then
        if [[ "$curr_perm" != "none" ]]; then
            echo -e "${YELLOW}[DRY-RUN] Would update role from '$curr_perm' to '$target_perm'${NC}"
        else
            echo -e "${YELLOW}[DRY-RUN] Would send invitation with permission '$target_perm'${NC}"
        fi
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
        continue
    fi

    # Execute PUT invitation / permission update
    response=$(gh api -X PUT "repos/$REPO/collaborators/$username" \
        -f permission="$target_perm" 2>&1) && status=$? || status=$?

    if [[ $status -eq 0 ]]; then
        echo -e "${GREEN}SUCCESS (Invitation sent or access updated)${NC}"
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        echo -e "${RED}FAILED${NC}"
        if echo "$response" | grep -q "rate_limit exceeded"; then
            echo -e "  ${RED}Reason: GitHub 24h repository invitation rate limit reached (50 invites/day max). Re-run the script tomorrow to finish remaining accounts.${NC}"
        elif echo "$response" | grep -q "404"; then
            echo -e "  ${RED}Reason: User account '$username' does not exist on GitHub (or repository not accessible).${NC}"
        elif echo "$response" | grep -q "403"; then
            echo -e "  ${RED}Reason: Permission denied. Ensure your authenticated account has Admin access to '$REPO'.${NC}"
        else
            echo -e "  ${RED}Details: $response${NC}"
        fi
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

echo "-----------------------------------"
if [[ "$DRY_RUN" == true ]]; then
    echo -e "${YELLOW}${BOLD}Dry run finished cleanly.${NC} Evaluated ${#CLEANED_USERS[@]} user(s)."
    echo -e "To send actual invitations, run the command again with ${BOLD}-x${NC} or ${BOLD}--execute${NC}."
else
    echo -e "${GREEN}Completed: $SUCCESS_COUNT processed ($SKIP_COUNT skipped high permissions), $FAIL_COUNT failed.${NC}"
fi
