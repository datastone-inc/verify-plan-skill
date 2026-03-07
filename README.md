<!-- markdownlint-disable MD013 MD033 MD041 -->
<p align="center"><img src="assets/datastone_logo.png" width="300" alt="dataStone logo" /></p>
<!-- markdownlint-enable MD033 MD041 -->

# plan-implemented skill for Claude Code

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet.svg)](https://docs.anthropic.com/en/docs/claude-code)

Post-implementation audit skill for Claude Code `/plan`. Verifies that a `/plan` was fully implemented by comparing plan items against actual code changes. Catches missing implementations, dead code, and missing tests, then interactively walks you through gaps and offers to fix them.

> [!NOTE]
>
> - Works on committed and uncommitted work. Run before or after committing.
> - Complements code review but doesn't replace it; focuses on implementation gaps vs. the plan, not code quality or design. Run before or after code review, as needed.
> - Suggested to run this **before** `/simplify`, `/refactor`, or similar commands. If there's a gap between the plan and the current code, those commands may remove or restructure code that appears unused or dead, but is only that way because the wiring is missing. Close the plan implementation gaps first, then simplify.

## Installation

### Step 1: Clone into the global skills folder

```bash
mkdir -p ~/.claude/skills
git clone https://github.com/datastone-inc/plan-implemented-skill ~/.claude/skills/plan-implemented
```

This installs the skill globally, available in all your projects. That covers most people.

**Project-scoped install (niche):** If you need the skill scoped to a single repo, avoid cloning into it — that creates a nested git repo, which Git handles poorly. Copy from the global install instead:

```bash
mkdir -p .claude/skills
cp -r ~/.claude/skills/plan-implemented .claude/skills/plan-implemented
```

Note: the copy won't receive updates via `git pull` — you'll need to re-copy after updating the global install.

### Step 2: Install the slash command

```bash
python ~/.claude/skills/plan-implemented/scripts/install_command.py
```

Works on macOS, Linux, and Windows. Creates a symlink in `~/.claude/commands/` (falls back to copying on Windows if symlinks require elevated privileges).

Restart Claude Code or start a new session.

### Keeping it up-to-date

```bash
cd ~/.claude/skills/plan-implemented && git pull
```

## Requirements

- Python 3.10+
- Git

No pip dependencies. Uses only the Python standard library.

## Usage

In Claude Code:

``` text
# Auto-discover most recent plan, review all changes (committed + uncommitted) since it was written
/plan-implemented

# Specify a plan file
/plan-implemented .claude/plans/my-plan.md

# Review only uncommitted work
/plan-implemented --scope uncommitted

# Review committed changes only vs a branch
/plan-implemented --scope branch --base develop

# Review everything (committed + uncommitted) vs main
/plan-implemented --scope all

# List available plans
/plan-implemented --list

# Or just say it naturally
> was the plan actually followed?
> check if the plan was implemented
> I haven't committed yet, did I cover the plan?
```

### Scopes

| Scope | What it diffs | When to use |
| ------ | ------------ | ----------- |
| `plan` (default) | Changes since the plan was last modified, including uncommitted | Best general-purpose option |
| `branch` | Committed changes only: `base..HEAD` | Clean committed-only view |
| `uncommitted` | Staged + unstaged vs HEAD | Just finished implementing, haven't committed |
| `all` | Committed + uncommitted vs base branch | Complete picture |

## Interactive flow

1. **Summary**: scorecard and per-Change overview
2. **Walkthrough**: one Change group at a time, explaining gaps, assessing severity, flagging false positives
3. **Fix**: implement missing pieces in place when asked
4. **Re-verify**: re-run the audit after fixes to confirm

Claude pauses at each step for your input. You choose what to fix, skip, or stop.

## Language support

Pattern extraction works across multiple languages, detected automatically from file extensions and code fences:

TypeScript/JS, Python, Rust, Go, Java/Kotlin, C/C++, C#, Ruby, Swift, SQL

To add a new language, add an entry to `scripts/languages.py`. No other code changes needed. See the existing entries for the pattern format.

## How it works

1. **Parse**: reads the plan markdown and extracts verifiable items (types, functions, fields, filters, tests) using language-aware pattern extraction
2. **Evidence**: gathers changes according to the chosen scope (branch diff, plan-anchored, uncommitted, or all)
3. **Cross-reference**: checks each item against the diff; language-aware dead-code detection finds declared-but-unused symbols
4. **Interactive**: Claude presents findings, walks through gaps, and offers to fix them

## Contributing

Contributions welcome! The easiest way to help is adding language support by adding an entry to `scripts/languages.py`. Each language entry is a self-contained dict of regex patterns.

For bug reports and feature requests, please open an issue.

## Authors

**[dataStone Inc.](https://github.com/datastone-inc)**: concept, design, and development

**[Claude (Anthropic)](https://www.anthropic.com)**: co-developed the implementation, scripts, and multi-language support via Claude Code

## License

[MIT](LICENSE)
