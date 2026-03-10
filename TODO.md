# TODO for plan-implemented-skill

This file tracks remaining tasks to polish the repository for public release.

## ✅ Completed (Phase 1)

- [x] Add `pyproject.toml` with Python 3.10+ requirement
- [x] Create `examples/sample-plan.md` with realistic plan
- [x] Create `tests/` directory with pytest tests (18 tests, all passing)
- [x] Create `CONTRIBUTING.md` with detailed contribution guide
- [x] Improve error messages in scripts (Python version, git repo, plans directory)
- [x] Add Architecture section to README
- [x] Add `--help` output to README (CLI Reference section)
- [x] Remove `.vscode/coach/` directory

## ⏳ TODO (Phase 2 - Manual Tasks)

### 9. Record Quickstart GIF/Screenshot

**Goal:** ~30-second terminal recording showing `/plan-implemented` running against the sample plan.

**Tools:**

- `asciinema rec assets/quickstart.cast` (terminal recorder)
- `vhs` (charmbracelet) for reproducible animated GIFs
- Or manual screen capture

**What to show:**

1. Run: `/plan-implemented` (or `python3 scripts/review.py examples/sample-plan.md --repo .`)
2. Plan discovery message
3. Parsing output (e.g., "Found 8 verifiable items")
4. Evidence gathering (e.g., "3 files in diff")
5. Cross-reference summary (e.g., "Evidence: {'❌': 6, '🔍': 2}")
6. Report saved location

**Output:** Place recording in `assets/` (e.g., `assets/quickstart.gif` or `assets/quickstart.cast`)

**Dependency:** Requires examples/sample-plan.md (✅ done)

---

### 10. Example Walkthrough GIF/Screenshot

**Goal:** Screenshot or GIF of the interactive audit flow (Claude Code presenting findings and walking through gaps).

**What to capture:**

- Claude presenting the summary scorecard
- Walking through one Change with evidence details
- Offering to fix a gap
- (Optional) Re-verification after fix

**How:**

1. Run `/plan-implemented` against examples/sample-plan.md in Claude Code
2. Screenshot or record the interactive conversation
3. Crop/annotate to highlight the workflow

**Output:** Place in `examples/` (e.g., `examples/walkthrough.png` or `examples/interactive-flow.gif`)

**Dependency:** Can use same session as step 9

---

### 11. GitHub Repository Metadata

**Goal:** Set repository metadata via GitHub UI or `gh` CLI.

**Tasks:**

#### Topics/Tags

Add these topics via GitHub Settings → Topics:

- `claude-code`
- `skill`
- `plan-audit`
- `code-review`
- `developer-tools`
- `python`
- `git`

#### Description

Set repository description (appears under repo name):

```text
Post-implementation audit skill for Claude Code /plan — catches missing implementations, dead code, and gaps
```

#### Social Preview Image

- **Option A:** Upload `assets/datastone_logo.png` as social preview
- **Option B:** Create a dedicated card (1280×640px) with logo + tagline

**How to set:**

- GitHub UI: Settings → General → Social preview
- Or via `gh api` commands

**Dependency:** None (can be done anytime)

---

### 12. Update README with GIF References

**Goal:** Embed the GIFs/screenshots from steps 9 and 10 into README.

**Changes to make:**

1. **In the top section** (after the badges, before "Installation"):

   ```markdown
   ## Quick Demo
   
   ![Quickstart demo](assets/quickstart.gif)
   
   *Run `/plan-implemented` to audit a plan against your code changes.*
   ```

2. **In the "Interactive flow" section** (around line 135):

   ```markdown
   ## Interactive flow
   
   ![Interactive walkthrough](examples/walkthrough.png)
   
   1. **Summary**: scorecard and per-Change overview
   2. **Walkthrough**: one Change group at a time, explaining gaps, assessing severity, flagging false positives
   3. **Fix**: implement missing pieces in place when asked
   4. **Re-verify**: re-run the audit after fixes to confirm
   
   Claude pauses at each step for your input. You choose what to fix, skip, or stop.
   ```

**Dependency:** Requires steps 9 and 10 (GIFs must exist first)

---

## Verification Checklist

After completing Phase 2:

- [ ] Quickstart GIF exists and plays correctly
- [ ] Walkthrough image/GIF exists and is visible
- [ ] README displays both GIFs without errors
- [ ] GitHub topics are visible on repository page
- [ ] Repository description appears in search results
- [ ] Social preview image shows when repository is shared

---

## Optional Enhancements (Future)

- Add `examples/PLAN_REVIEW.md` showing real audit output
- Create a `docs/` directory with detailed examples
- Add asciinema/vhs recording scripts for reproducibility
- Create GitHub Actions workflow to run tests on PR
- Add more test cases for edge cases (deeply nested plans, unusual formats)
- Support additional languages (Elixir, PHP, Scala, etc.)
