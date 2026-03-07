---
name: plan-implemented
description: "Post-implementation audit of Claude Code /plan output against actual code changes. Use when verifying a plan was implemented, checking if a plan was followed, auditing implementation completeness, finding dead code from a plan, or reviewing what was missed after Claude Code finished executing a plan. Supports reviewing committed changes, uncommitted work, or everything since the plan was created. Also trigger when the user says 'was the plan actually followed', 'did CC implement everything', 'check the plan against the diff', 'what did we miss', 'audit the plan', 'review uncommitted changes against the plan', or 'what changed since the plan'. Works with .claude/plans/ markdown files. Use this even when the user just wants a general post-implementation check — they don't need to say 'plan' explicitly if there's a plan in the project."
argument-hint: "[plan-file] [--base branch] [--scope branch|plan|uncommitted|all]"
allowed-tools: Bash(python:*), Bash(git:*), Read, Grep, Glob, Edit, AskUserQuestion
---

# Plan Implementation Audit

You are auditing whether a Claude Code `/plan` was fully implemented by comparing plan items against actual code changes. Your job is to run the audit script, interpret the results, and interactively walk the user through any gaps — explaining *why* things were missed, not just *that* they were missed. Then help fix them.

## Step 1: Determine the plan file

If `$ARGUMENTS` includes a path, use that as the plan file.

If no plan file is specified, discover it automatically:

1. Check `.claude/settings.local.json`, `.claude/settings.json`, and `~/.claude/settings.json` for a `plansDirectory` setting
2. If not configured, check `.claude/plans/` in the repo, then `~/.claude/plans/`
3. Pick the most recently modified `.md` file in whichever directory is found
4. Tell the user which plan you found and confirm before proceeding

To list available plans for the user:
```bash
python <skill-path>/scripts/review.py --list --repo .
```

## Step 2: Determine the diff scope

The `--scope` flag controls which changes to review. If `$ARGUMENTS` includes `--scope <value>`, use it. Otherwise, choose intelligently:

| Scope | What it diffs | When to use |
|-------|--------------|-------------|
| `plan` (default) | Changes since the plan file was last modified, including uncommitted | Best general-purpose option — captures everything done since the plan was written |
| `branch` | Committed changes only: `base..HEAD` | When you want a clean committed-only view |
| `uncommitted` | Staged + unstaged vs HEAD | When the user just finished implementing and hasn't committed yet |
| `all` | Committed + uncommitted vs base branch | When you want the complete picture against the base |

If the user says things like "check my uncommitted work" or "I haven't committed yet", use `--scope uncommitted`. If they say "what changed since the plan", use `--scope plan`. If they just say "audit the plan", the default `plan` scope is usually right.

## Step 3: Determine the base branch

If `$ARGUMENTS` includes `--base <branch>`, use that branch.

Otherwise, default to `main`. If the repo uses a different default branch, detect it:
```bash
git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@'
```

Note: `--base` is only used by the `branch` and `all` scopes. The `plan` scope anchors to the plan's modification time instead, and `uncommitted` diffs against HEAD.

## Step 4: Run the audit

Output to a temp file — the user doesn't need to open it, you present the results interactively.

```bash
python <skill-path>/scripts/review.py <plan-file> --base <branch> --scope <scope> --repo . --output /tmp/plan-review-$(date +%s).md
```

The script runs three phases:
1. **Parse** — extracts discrete checkable items from the plan (types, functions, fields, filters, tests, wiring)
2. **Evidence** — gathers changes according to the chosen scope
3. **Cross-reference** — matches each plan item against the diff, checks for dead code

The script exits 0 if all items pass, 1 if any issues are found.

If the user explicitly asks to save the report (e.g. `--output path`), write it there instead.

## Step 5: Present the summary

Read the temp file. Present a concise summary to the user covering:

1. **Context** — which plan, scope used, branch, HEAD commit (from the Context section)
2. **Scorecard** — the counts: implemented, not implemented, dead code, partial, skipped
3. **Per-Change overview** — one line per Change group showing its overall status. For example:
   ```
   Change 1: Add TurnOrigin type — 3 items, all missing
   Change 2: Claude Code normalizer — 8 items, 2 implemented, 4 missing, 2 partial
   Change 5: Downstream consumers — 5a pattern analysis ok, 5b-5d have gaps
   ```
   Use the sub_id (5a, 5b, etc.) when available to make cross-referencing with the plan easy.

If everything passes, say so and you're done.

**STOP.** You MUST call `AskUserQuestion` NOW to ask the user how they want to proceed. Suggested options:
- Walk through the gaps (default — go Change by Change)
- Jump to a specific Change group
- Fix everything automatically
- Just show me the details (dump the full checklist without interactive flow)

Do NOT proceed to Step 6 until the user responds.

## Step 6: Interactive walkthrough

Walk through gaps one Change group at a time, starting with the most impactful. For each group with issues:

1. **Explain what's missing and why.** Don't just list pattern names — look at the actual code and the plan to understand the architectural reason. For example: "The plan expected `classifyTurnOrigin()` as a separate method, but the implementation inlined the logic into `buildTurns()` — the patterns don't match but the intent might be covered."

2. **Assess severity.** Is this a blocker (feature broken), a gap (feature works but incomplete), or a false positive (implemented differently than the plan described)?

3. Be smart about false positives. The script does mechanical pattern matching — if a plan says "add method `foo()`" and the code has `fooBar()` that covers the same intent, flag it as likely covered rather than missing. Read the actual source files to verify before calling something a real gap.

**STOP.** After presenting each Change group, you MUST call `AskUserQuestion` to ask the user what to do. Suggested options:
- **Fix** — implement the missing pieces for this Change group
- **Skip** — move on to the next Change group
- **Stop** — end the walkthrough

Do NOT move to the next Change group or start fixing until the user responds. Wait for their input on every group.

## Step 7: Fix and re-verify

When the user asks you to fix a gap:

1. Read the relevant plan section and source files
2. Implement the fix using Edit
3. After all requested fixes in a group are done:

**STOP.** You MUST call `AskUserQuestion` to ask: "Fixes applied. Want me to re-run the audit to verify, or move on to the next Change group?"

Do NOT continue until the user responds.

4. If they want re-verification, re-run with `--scope uncommitted` (to catch the just-made changes) and present an updated summary. Then continue the walkthrough with remaining Change groups.
5. If they want to move on, proceed to the next Change group (back to Step 6).

## What the scripts check

| Check | Meaning |
|-------|---------|
| File modified | Was the target file touched in the diff? |
| Pattern present | Do expected identifiers (type names, function names, field names) appear in added lines? |
| Dead code — assigned | Is a declared field actually assigned somewhere, not just declared? |
| Dead code — called | Is a declared function actually called, not just defined? |
| Dead code — read | Is a declared field read by any consumer? |
| Test present | For test items, does a matching test file or describe block exist? |

Dead-code detection is grep-based. It catches "never assigned" and "never called" but not "condition always false" or "unreachable branch." Note this limitation to the user if relevant.

## Example invocations

User types: `/plan-implemented`
→ Auto-discover most recent plan, review changes since the plan was written, walk through gaps

User types: `/plan-implemented .claude/plans/turn-origin-tagging.md`
→ Use that specific plan file, changes since it was written

User types: `/plan-implemented --scope uncommitted`
→ Auto-discover plan, check only uncommitted work against it

User types: `/plan-implemented --scope branch --base develop`
→ Auto-discover plan, committed changes only vs develop

User types: "check if the plan was actually implemented"
→ Auto-trigger, discover the plan, run the audit, walk through interactively

User types: "I haven't committed yet, did I cover everything in the plan?"
→ Auto-trigger with `--scope uncommitted`

User types: "fix the gaps from the plan"
→ After an audit has run, jump straight to fixing
