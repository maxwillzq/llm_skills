# Proving a Refactor Changed Nothing (Equivalence Verification)

A guide for behaviour-preserving changes, dependency removals, and refactors claimed to produce "the same output".

---

## 1. The Baseline-Capture-and-Diff Loop

Whenever a refactor is claimed to produce zero semantic changes:

1. **Before touching code**: Write a capture script that invokes the affected code against a real production payload (not toy fixtures) and writes the result to JSON with stable ordering. Save as `baseline_before.json`.
2. **Apply the refactor**: Complete the implementation.
3. **Capture after**: Run the exact same capture script pointing to `baseline_after.json`.
4. **Structural recursive diff**: Walk both JSON trees recursively, asserting zero differences.

```python
def walk(path, a, b, tol=1e-6):
    if type(a) != type(b):
        yield f"TYPE {path}: {type(a)} != {type(b)}"
        return
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                yield f"KEY {path}: missing {k}"
            else:
                yield from walk(f"{path}.{k}", a[k], b[k], tol)
    elif isinstance(a, list):
        if len(a) != len(b):
            yield f"LEN {path}: {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            yield from walk(f"{path}[{i}]", x, y, tol)
    elif isinstance(a, float):
        if abs(a - b) > tol * max(1.0, abs(a)):
            yield f"FLOAT {path}: {a} != {b}"
    elif a != b:
        yield f"VAL {path}: {a!r} != {b!r}"
```

---

## 2. Four Concrete Traps in Equivalence Diffs

### Trap 1: Float last-bit noise breaks sort ordering
`ps / 1e6` and `ns / 1000.0` disagree in the last bit for **25% (1,009,302 of 3,999,999)** of integer picosecond values. If ops with equal durations are sorted by float sum, this last-bit difference flips ties and changes top-N ordering.
- **Fix**: Round the metric in the sort key: `sort_key = (-round(total_us, 6), op_name)`.
- **In diff**: Compare floating-point values with a small relative tolerance (`1e-6` or `1e-9`), never exact `==`.

### Trap 2: Positional matching vs. Name-based matching
When an internal ID is intentionally changed or renumbered (e.g. Perfetto `tid` or thread IDs), comparing lists positionally or matching by numeric IDs produces 100% false mismatches.
- **Fix**: Match lanes, series, or entities by their semantic **name/label** (`process_name`, `thread_name`, op name), not numeric sequence index.

### Trap 3: Over-normalising the diff hides real bugs
If anonymous lanes are collapsed into a single generic bucket (e.g. mapping all `Line_<id>` to `Line_*`), lane swapping or dropped lines become invisible.
- **Fix**: Normalise by *first-appearance ordinal* (`anon#0`, `anon#1`, etc.), not a shared wildcard bucket.

### Trap 4: Staged-file invisibility
A `git add`-ed file is invisible to `git archive HEAD`, to plain `git diff`, and to untracked-file checks. A clean-room reproduction checkout can run against a tree missing your new module while reporting green.
- **Fix**: Use `git diff --binary HEAD` or check working-tree files against index before archiving.

---

## 3. Audit Blocking Constraints Before Accepting Them

When a dependency or architectural cleanup appears blocked by an existing requirement (e.g. "we must keep dependency X because we need field Y"):

1. **Verify what consumes field Y**: Check every callsite that reads field Y.
2. **Measure on real traces**: Does field Y actually contain what the caller thinks it contains?
3. In this project, preserving `line.id` was believed to be mandatory because `_analyze_perfetto_json_bubbles` keyed off `tid == 4`. When measured against real trace metadata, `tid == 4` selected `Async XLA Ops` (94 ms) and dropped `XLA Ops` (66 ms) and `XLA Modules` (66 ms) — dropping **59% of device execution**.
4. **Conclusion**: A constraint blocking a cleanup is often itself a latent bug masquerading as a specification.
