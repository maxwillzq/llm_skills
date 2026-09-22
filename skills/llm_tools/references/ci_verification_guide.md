# CI Verification Guide

How to confirm a CI run is *actually* green, how to reproduce it locally
without lying to yourself, and the specific linter traps that cost real time.

Everything here was learned by getting it wrong first.

---

## 1. The GitHub Actions verification loop

```bash
# Three-state answer: pass / fail / pending. Exits non-zero while pending.
gh pr checks <PR_NUMBER>

# Only the failing steps, not the whole 3000-line log.
gh run view <RUN_ID> --log-failed

# Watch until terminal, instead of polling by hand.
gh run watch <RUN_ID>

# Which lines can an inline review comment legally target?
# (GitHub 422s "Line could not be resolved" outside a diff hunk.)
gh pr diff <N> --patch | awk '/^diff --git/{f=$3} /^@@/{print f": "$0}'
```

> [!WARNING]
> A local `pytest` run is **not** evidence about CI. Report "pending" while
> checks are pending. See the `verify_before_claiming` rule.

### Duplicate runs

`push` and `pull_request` triggers on the same commit produce **different**
`github.ref` values, so a `concurrency.group` keyed on `github.ref` will *not*
deduplicate them — you get the whole matrix twice. Restrict `push` to the
default branch and let `pull_request` cover feature branches.

---

## 2. A local reproduction must copy `actions/checkout` semantics

Running the test command in your working tree does not reproduce CI. Three
things leak:

1. **The dev virtualenv.** It has accumulated extras CI never installs.
2. **Untracked files.** CI only sees what is committed.
3. **Code that injects a venv into `sys.path`.** Some repos do this
   deliberately (e.g. to find an optional protobuf). Then optional deps leak
   into *any* local run, including one launched from a deliberately minimal
   virtualenv — so even a "clean venv" repro silently passes.

The recipe that actually works:

```bash
WORK_DIR="$(mktemp -d)"
git archive --format=tar HEAD | tar -x -C "$WORK_DIR"   # tracked files only
git diff | (cd "$WORK_DIR" && patch -p1 -s)             # optional: uncommitted edits
[[ -e "$WORK_DIR/.venv" ]] && { echo "venv leaked"; exit 1; }
cd "$WORK_DIR" && uv venv .ci-venv --python 3.12
```

Then assert the environment is what you think it is. If the job's whole point
is to test the *degraded* path, prove the optional dependency is absent:

```bash
if python -c "import optional_dep" 2>/dev/null; then
  echo "ERROR: optional_dep present; this job no longer tests the degraded path" >&2
  exit 1
fi
```

Reproduce the **full** job, in order, including the lint steps. A repro that
stops after `pytest` cannot tell you about a failure in step 7.

---

## 3. Linter traps

### shellcheck

| Code | Trap | Fix |
| :--- | :--- | :--- |
| SC1091 | `source "${SCRIPT_DIR}/common.sh"` is not a literal path, so it is not followed | Add `# shellcheck source=path/to/common.sh` **and** invoke with `-x` |
| SC1072/SC1073 | A comment line starting with `# shellcheck ` is parsed as a **directive** — prose breaks the parse | Reword so no line begins with that token |
| SC2086 | Word-splitting that is *intentional* | Use an array — do not add quotes (changes semantics) and do not blanket-disable |
| SC2012 | `ls -t dir/*.x \| head -n 1` | `find dir -maxdepth 1 -name '*.x' -printf '%T@ %p\n' \| sort -rn \| head -n1 \| cut -d' ' -f2-` |
| SC2034 | "appears unused" for vars consumed by scripts that `source` this file | `export` them — that is the honest fix, not a disable |

Intentional word-splitting, done explicitly:

```bash
read -r -a _flags <<< "${BUILD_FLAGS:---default}"
some_command "${_flags[@]}"
```

> [!IMPORTANT]
> Do not dismiss shellcheck findings as style noise. Triage each one. An
> SC2027 ("the surrounding quotes actually unquote this") once turned out to
> be `KUBECTL=""${KUBECTL}" --context=..."` — under `set -u` the script died
> on that line with `unbound variable` before doing anything, *and* the
> variable was dead code. The linter found a total outage, not a nit.

### actionlint

Bare `actionlint` locates the project by walking up for a `.git` directory. In
a tarball-extracted scratch checkout there isn't one:

```
no project was found in any parent directories of "/tmp/..."
```

Pass the files explicitly: `actionlint .github/workflows/*.yml`.

### Pin your linters

`apt-get install shellcheck` gives whatever the runner image ships. The
version drifts, differs from your local one, and a new release can turn the
build red with no change of yours. Download a pinned static binary in both CI
and the local repro so the two agree:

```yaml
env:
  SHELLCHECK_VERSION: 0.10.0
run: |
  curl -sSLo shellcheck.tar.xz \
    "https://github.com/koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}/shellcheck-v${SHELLCHECK_VERSION}.linux.x86_64.tar.xz"
  tar xJf shellcheck.tar.xz "shellcheck-v${SHELLCHECK_VERSION}/shellcheck"
```

---

## 4. Ordering: put cheap linters first

CI fails fast, so whatever runs last has effectively never run. If `pytest`
sits before `shellcheck` and `pytest` has been broken for a while, the shell
scripts are unlinted and you will not find out until the day you fix the
tests. Put the seconds-long linters first, or accept that fixing one failure
will uncover the next.
