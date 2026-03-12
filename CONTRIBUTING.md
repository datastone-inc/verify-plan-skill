# Contributing to verify-plan

Thank you for your interest in contributing! This guide will help you get started.

## Quick Links

- [Adding a New Language](#adding-a-new-language)
- [Running Tests](#running-tests)
- [Understanding the Architecture](#architecture)
- [Submitting Changes](#submitting-changes)

---

## Adding a New Language

The easiest way to contribute is adding support for a new programming language. All language definitions live in a single file: [`scripts/languages.py`](scripts/languages.py).

### Anatomy of a Language Entry

Each language is a dictionary with these keys:

```python
'LanguageName': {
    'extensions': ['.ext', '.ext2'],       # File extensions
    'fences': ['language', 'lang'],        # Code fence names (```language)
    'declarations': {                      # Patterns to extract identifiers
        'type': [r'regex_with_group1'],
        'function': [r'regex_with_group1'],
        'field': [r'regex_with_group1'],
        # ... language-specific patterns
    },
    'call_pattern': r'{name}\s*\(',       # How function calls look
    'access_pattern': r'\.{name}\b',      # How property access looks
    'noise_words': ['keyword1', 'keyword2'],  # Keywords to exclude
}
```

### Key Guidelines

1. **Regex group(1) must capture the identifier name**

   ```python
   r'function\s+(\w+)\s*\('  # group(1) = function name
   ```

2. **Test against real code samples**
   - Add test cases in `tests/test_parse_plan.py` for your language
   - Include common patterns: functions, classes, types, interfaces

3. **Use existing languages as templates**
   - See TypeScript/JavaScript, Python, Rust entries for examples
   - Most languages need: type, function, field patterns at minimum

4. **Call and access patterns support dead-code detection**
   - `{name}` is a placeholder that gets replaced with the identifier
   - Used to search for where declared symbols are used

### Example: Adding PHP Support

```python
'PHP': {
    'extensions': ['.php'],
    'fences': ['php'],
    'declarations': {
        'type': [
            r'class\s+(\w+)',
            r'interface\s+(\w+)',
            r'trait\s+(\w+)',
        ],
        'function': [
            r'function\s+(\w+)\s*\(',
        ],
        'field': [
            r'private\s+\$(\w+)',
            r'protected\s+\$(\w+)',
            r'public\s+\$(\w+)',
        ],
        'constant': [
            r'const\s+(\w+)\s*=',
            r'define\s*\(\s*[\'"](\w+)[\'"]',
        ],
    },
    'call_pattern': r'{name}\s*\(',
    'access_pattern': r'->{name}\b',
    'noise_words': ['function', 'class', 'interface', 'trait', 'const'],
}
```

Then add the entry to the `LANGUAGES` dict at the bottom of `languages.py`.

---

## Running Tests

### Prerequisites

```bash
# Install dev dependencies (pytest)
pip install -e ".[dev]"
```

### Run All Tests

```bash
python -m pytest tests/
```

### Run Specific Test File

```bash
python -m pytest tests/test_parse_plan.py
```

### Run with Verbose Output

```bash
python -m pytest tests/ -v
```

### Run a Single Test

```bash
python -m pytest tests/test_parse_plan.py::TestParsePlan::test_basic_change_heading
```

### Writing Tests

Tests live in `tests/`:

- `test_parse_plan.py`: Test plan parsing, pattern extraction, categorization
- `test_cross_reference.py`: Test evidence level matching, dead-code detection

When adding a new language, add test cases in `test_parse_plan.py` that:

1. Parse code blocks in your language
2. Extract expected identifiers correctly
3. Categorize items (type vs. function vs. field)

---

## Architecture

The skill operates in a 4-stage pipeline:

```text
┌─────────┐    ┌──────────┐    ┌────────────────┐    ┌─────────────┐
│ Parse   │ -> │ Evidence │ -> │ Cross-         │ -> │ Interactive │
│ Plan    │    │ Gather   │    │ Reference      │    │ Review      │
└─────────┘    └──────────┘    └────────────────┘    └─────────────┘
```

### Stage 1: Parse Plan

**File:** [`scripts/parse_plan.py`](scripts/parse_plan.py)

Reads a Claude Code `/plan` markdown file and extracts verifiable items:

- Detects `## Change N:` headings to group related work
- Extracts code blocks and applies language-specific patterns
- Finds inline code mentions (e.g., "Update the `handleRequest` function")
- Categorizes items: `type_definition`, `function`, `field`, `test`, etc.
- Outputs structured JSON: `{id, change_id, file_pattern, expected_patterns, category}`

**Key function:** `parse_plan(plan_text: str) -> list[dict]`

### Stage 2: Evidence Gather

**File:** [`scripts/gather_evidence.py`](scripts/gather_evidence.py)

Collects git diff and file contents according to scope:

- **Scopes**:
  - `plan`: Changes since plan file was modified (default)
  - `branch`: Committed changes vs base branch
  - `uncommitted`: Staged + unstaged vs HEAD
  - `all`: Committed + uncommitted vs base
- Parses unified diffs by file
- Reads current file contents for cross-referencing
- Handles exact path and basename matching

**Key function:** `gather_evidence(base, repo, plan_files, scope, plan_mtime) -> dict`

### Stage 3: Cross-Reference

**File:** [`scripts/cross_reference.py`](scripts/cross_reference.py)

Matches plan patterns against diff evidence:

- **Evidence levels**:
  - ✅ `IN_DIFF`: All patterns in added diff lines
  - 🔍 `MIXED`: Some in diff, others pre-existing
  - ⚠️ `PRE_EXISTING`: Pattern exists but not in diff
  - ❌ `NOT_FOUND`: Not found anywhere
  - ⏭️ `SKIPPED`: No verifiable patterns (e.g., prose descriptions)
- **Dead-code detection**:
  - Type definitions: checks if referenced elsewhere
  - Functions: searches for calls using language `call_pattern`
  - Fields: searches for assignments and reads using `access_pattern`
- Generates markdown report with evidence table and dead-code signals

**Key functions:** `cross_reference(plan_items, evidence) -> list[dict]`, `generate_report(...) -> str`

### Stage 4: Interactive Review

**Orchestrator:** [`scripts/review.py`](scripts/review.py)

Coordinates the pipeline and outputs results:

- Discovers plan files from CC settings hierarchy
- Runs stages 1-3 sequentially
- Outputs markdown report (`PLAN_REVIEW.md`) or JSON
- Provides exit codes for automation (0 = clean, 1 = gaps found)
- Claude Code uses this report in conversation to walk through findings interactively

**Key function:** `main()`

---

## Submitting Changes

### Before Submitting a PR

1. **Run the test suite**

   ```bash
   python -m pytest tests/
   ```

2. **Test against a real plan** (if modifying parsing or cross-reference logic)

   ```bash
   python scripts/review.py examples/sample-plan.md --repo .
   ```

3. **Check for errors** in scripts outside a git repo (if modifying error handling)

   ```bash
   cd /tmp
   python /path/to/review.py
   ```

### PR Guidelines

- **One logical change per PR**: Separate language additions from bug fixes
- **Add tests**: New features or bug fixes should include test coverage
- **Update docs**: If changing behavior, update README.md or this guide
- **Use descriptive commits**: "Add Elixir language support" not "Update languages.py"

### PR Checklist

- [ ] Tests pass (`python -m pytest tests/`)
- [ ] New code has test coverage
- [ ] Documentation updated if behavior changed
- [ ] No unrelated changes (formatting, refactoring) mixed with feature work
- [ ] Commit messages are descriptive

### Getting Help

If you're stuck:

1. Check existing language entries in `scripts/languages.py` for patterns
2. Look at test examples in `tests/` for how to structure tests
3. Open an issue describing what you're trying to add/fix

---

## Development Setup

### Clone the Repository

```bash
git clone https://github.com/datastone-inc/verify-plan-skill.git
cd verify-plan-skill
```

### Install Dev Dependencies

```bash
pip install -e ".[dev]"
```

### Run the Skill Locally

```bash
# Against the sample plan
python scripts/review.py examples/sample-plan.md --repo .

# Against your own plan
python scripts/review.py /path/to/your-plan.md --repo /path/to/your-repo
```

---

## Code Style

- **Python 3.10+ features**: Type hints encouraged, pattern matching welcome
- **Standard library only**: No pip dependencies in runtime code
- **Descriptive names**: `parse_plan` not `pp`, `evidence_level` not `lvl`
- **Comments for complex regex**: Explain what patterns match and why

---

## Questions or Feedback?

Open an issue on GitHub or reach out to [dataStone Inc.](https://github.com/datastone-inc)

We appreciate your contributions! 🎉
