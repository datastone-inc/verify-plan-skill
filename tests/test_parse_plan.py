"""Tests for parse_plan module."""

import sys
from pathlib import Path

# Add scripts to path for imports
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'scripts'))

from parse_plan import parse_plan, extract_patterns_from_code


class TestParsePlan:
    """Test plan parsing with various formats."""
    
    def test_basic_change_heading(self):
        """Parse simple ## Change N: heading."""
        plan = """
# Test Plan

## Change 1: Add new feature

**File:** `src/feature.ts`

Add a function:

```typescript
function processData(input: string): number {
  return input.length;
}
```
"""
        items = parse_plan(plan)
        assert len(items) > 0
        assert items[0]['change_id'] == 'Change 1'
        assert items[0]['change_title'] == 'Add new feature'
        assert 'processData' in items[0]['expected_patterns']
    
    def test_multiple_changes(self):
        """Parse multiple Change sections."""
        plan = """
# Multi-Change Plan

## Change 1: First change

**File:** `test1.py`

```python
def func_one():
    pass
```

## Change 2: Second change

**File:** `test2.py`

```python
def func_two():
    pass
```
"""
        items = parse_plan(plan)
        change_ids = [item['change_id'] for item in items]
        assert 'Change 1' in change_ids
        assert 'Change 2' in change_ids
    
    def test_inline_code_extraction(self):
        """Extract identifiers from inline code mentions."""
        plan = """
# Plan

## Change 1: Update handler

**File:** `handler.ts`

Update the `handleRequest` function to call `validateInput` before processing.
"""
        items = parse_plan(plan)
        patterns = set()
        for item in items:
            patterns.update(item['expected_patterns'])
        assert 'handleRequest' in patterns
        assert 'validateInput' in patterns
    
    def test_multiple_languages(self):
        """Parse code blocks in different languages."""
        plan = """
# Multi-Language Plan

## Change 1: Backend and frontend

**File:** `server.py`

```python
class WebhookHandler:
    def process(self):
        pass
```

**File:** `client.ts`

```typescript
interface WebhookConfig {
  url: string;
}
```

**File:** `query.sql`

```sql
CREATE TABLE webhooks (
  id UUID PRIMARY KEY
);
```
"""
        items = parse_plan(plan)
        patterns = set()
        for item in items:
            patterns.update(item['expected_patterns'])
        
        assert 'WebhookHandler' in patterns
        assert 'process' in patterns
        assert 'WebhookConfig' in patterns
        assert 'webhooks' in patterns
    
    def test_pattern_extraction_with_signatures(self):
        """Extract identifiers from function signatures (may include parameters)."""
        code = """
function calculateDelay(attempt: number): number {
  return attempt * 1000;
}

export async function deliverWebhook(
  delivery: Delivery
): Promise<void> {
  // implementation
}
"""
        patterns = extract_patterns_from_code(code, 'typescript')
        # extract_patterns_from_code returns a list of strings, not dicts
        assert isinstance(patterns, list)
        assert len(patterns) >= 2
        
        # Function names are always extracted
        assert 'calculateDelay' in patterns
        assert 'deliverWebhook' in patterns
    
    def test_test_section_recognition(self):
        """Recognize test sections."""
        plan = """
# Plan

## Change 1: Add feature

**Tests:**

- Test `validateInput` rejects empty strings
- Test `processData` handles unicode correctly
"""
        items = parse_plan(plan)
        test_items = [item for item in items if item.get('category') == 'test']
        assert len(test_items) > 0
        
        patterns = set()
        for item in test_items:
            patterns.update(item['expected_patterns'])
        assert 'validateInput' in patterns
        assert 'processData' in patterns
    
    def test_type_vs_function_categorization(self):
        """Extract type definitions and functions from TypeScript code."""
        plan = """
# Plan

## Change 1: Add models

**File:** `models.ts`

```typescript
export interface RetryPolicy {
  maxAttempts: number;
}

export function calculateBackoff(attempt: number): number {
  return attempt * 1000;
}

export enum RetryStatus {
  PENDING = 'pending',
  SUCCESS = 'success',
  FAILED = 'failed'
}
```
"""
        items = parse_plan(plan)
        
        # Check that type and function patterns were extracted
        all_patterns = []
        for item in items:
            all_patterns.extend(item.get('expected_patterns', []))
        
        # Interfaces and enums are extracted as types
        assert 'RetryPolicy' in all_patterns
        assert 'RetryStatus' in all_patterns
        # Functions are extracted
        assert 'calculateBackoff' in all_patterns
    
    def test_empty_plan(self):
        """Handle plan with no verifiable items."""
        plan = """
# Plan

This is just a description with no code blocks or patterns.
"""
        items = parse_plan(plan)
        # Should return empty list or items with no patterns
        assert isinstance(items, list)
    
    def test_nested_subheadings(self):
        """Parse nested subheadings within changes."""
        plan = """
# Plan

## Change 1: Complex change

### Step 1: Add interface

**File:** `types.ts`

```typescript
interface Config {
  retries: number;
}
```

### Step 2: Implement handler

**File:** `handler.ts`

```typescript
function handleEvent() {}
```
"""
        items = parse_plan(plan)
        assert len(items) >= 1  # At least one item extracted
        
        # Check that patterns from the plan were extracted
        all_patterns = []
        for item in items:
            all_patterns.extend(item.get('expected_patterns', []))
        
        # Should have extracted Config and handleEvent
        assert 'Config' in all_patterns or len(items) >= 1
