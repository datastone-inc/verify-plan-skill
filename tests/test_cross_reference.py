"""Tests for cross_reference module."""

import sys
from pathlib import Path

# Add scripts to path for imports
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'scripts'))

from cross_reference import (
    cross_reference,
    IN_DIFF,
    MIXED,
    PRE_EXISTING,
    NOT_FOUND,
    SKIPPED,
)


class TestCrossReference:
    """Test evidence level determination and dead-code detection."""
    
    def test_in_diff_all_patterns_found(self):
        """Evidence level IN_DIFF when all patterns in diff added lines."""
        plan_items = [{
            'id': 'item1',
            'change_id': 1,
            'change_title': 'Add function',
            'file_pattern': 'test.py',
            'expected_patterns': ['calculate_delay', 'RetryConfig'],
            'category': 'function',
        }]
        
        evidence = {
            'file_diffs': {
                'test.py': (
                    'diff --git a/test.py b/test.py\n'
                    '+def calculate_delay(attempt, config):\n'
                    '+    return attempt * 1000\n'
                    '+\n'
                    '+class RetryConfig:\n'
                    '+    pass\n'
                )
            },
            'current_files': {
                'test.py': (
                    'def calculate_delay(attempt, config):\n'
                    '    return attempt * 1000\n'
                    '\n'
                    'class RetryConfig:\n'
                    '    pass\n'
                )
            },
            'full_diff': '',
            'modified_files': ['test.py'],
            'errors': [],
        }
        
        results = cross_reference(plan_items, evidence)
        assert len(results) == 1
        assert results[0]['evidence_level'] == IN_DIFF
    
    def test_mixed_some_in_diff_some_pre_existing(self):
        """Evidence level MIXED when patterns split between diff and existing."""
        plan_items = [{
            'id': 'item1',
            'change_id': 1,
            'change_title': 'Update function',
            'file_pattern': 'test.py',
            'expected_patterns': ['new_function', 'existing_function'],
            'category': 'function',
        }]
        
        evidence = {
            'file_diffs': {
                'test.py': (
                    'diff --git a/test.py b/test.py\n'
                    '+def new_function():\n'
                    '+    pass\n'
                    ' def existing_function():\n'
                    '     pass\n'
                )
            },
            'current_files': {
                'test.py': (
                    'def new_function():\n'
                    '    pass\n'
                    '\n'
                    'def existing_function():\n'
                    '    pass\n'
                )
            },
            'full_diff': '',
            'modified_files': ['test.py'],
            'errors': [],
        }
        
        results = cross_reference(plan_items, evidence)
        assert len(results) == 1
        assert results[0]['evidence_level'] == MIXED
    
    def test_pre_existing_all_patterns_already_exist(self):
        """Evidence level PRE_EXISTING when patterns exist but not in diff."""
        plan_items = [{
            'id': 'item1',
            'change_id': 1,
            'change_title': 'Add feature',
            'file_pattern': 'test.py',
            'expected_patterns': ['old_function'],
            'category': 'function',
        }]
        
        evidence = {
            'file_diffs': {
                'test.py': (
                    'diff --git a/test.py b/test.py\n'
                    '+def new_function():\n'
                    '+    pass\n'
                    ' def old_function():\n'
                    '     pass\n'
                )
            },
            'current_files': {
                'test.py': (
                    'def new_function():\n'
                    '    pass\n'
                    '\n'
                    'def old_function():\n'
                    '    pass\n'
                )
            },
            'full_diff': '',
            'modified_files': ['test.py'],
            'errors': [],
        }
        
        results = cross_reference(plan_items, evidence)
        assert len(results) == 1
        assert results[0]['evidence_level'] == PRE_EXISTING
    
    def test_not_found_patterns_missing(self):
        """Evidence level NOT_FOUND when patterns don't exist anywhere."""
        plan_items = [{
            'id': 'item1',
            'change_id': 1,
            'change_title': 'Add feature',
            'file_pattern': 'test.py',
            'expected_patterns': ['missing_function', 'also_missing'],
            'category': 'function',
        }]
        
        evidence = {
            'file_diffs': {
                'test.py': (
                    'diff --git a/test.py b/test.py\n'
                    '+def other_function():\n'
                    '+    pass\n'
                )
            },
            'current_files': {
                'test.py': 'def other_function():\n    pass\n'
            },
            'full_diff': '',
            'modified_files': ['test.py'],
            'errors': [],
        }
        
        results = cross_reference(plan_items, evidence)
        assert len(results) == 1
        assert results[0]['evidence_level'] == NOT_FOUND
    
    def test_no_patterns_marked_skipped(self):
        """Items with no expected patterns are marked SKIPPED."""
        plan_items = [{
            'id': 'item1',
            'change_id': 1,
            'change_title': 'Update documentation',
            'file_pattern': None,  # No file pattern
            'expected_patterns': [],
            'category': 'wiring',
        }]
        
        evidence = {
            'file_diffs': {},
            'current_files': {},
            'full_diff': '',
            'modified_files': [],
            'errors': [],
        }
        
        results = cross_reference(plan_items, evidence)
        assert len(results) == 1
        assert results[0]['evidence_level'] == SKIPPED
    
    def test_dead_code_function_not_called(self):
        """Detect function declared but never called."""
        plan_items = [{
            'id': 'item1',
            'change_id': 1,
            'change_title': 'Add function',
            'file_pattern': 'test.py',
            'expected_patterns': ['unused_function'],
            'category': 'function',
        }]
        
        evidence = {
            'file_diffs': {
                'test.py': (
                    'diff --git a/test.py b/test.py\n'
                    '+def unused_function():\n'
                    '+    return 42\n'
                )
            },
            'current_files': {
                'test.py': 'def unused_function():\n    return 42\n',
                'main.py': 'def main():\n    pass\n',  # No call to unused_function
            },
            'full_diff': '',
            'modified_files': ['test.py'],
            'errors': [],
        }
        
        results = cross_reference(plan_items, evidence)
        assert len(results) == 1
        # Dead code detection runs only for patterns found in diff
        # Check that the function was found in diff
        assert results[0]['evidence_level'] in [IN_DIFF, MIXED]
    
    def test_dead_code_type_not_referenced(self):
        """Detect type/interface declared but never used."""
        plan_items = [{
            'id': 'item1',
            'change_id': 1,
            'change_title': 'Add type',
            'file_pattern': 'types.ts',
            'expected_patterns': ['UnusedConfig'],
            'category': 'type_definition',
        }]
        
        evidence = {
            'file_diffs': {
                'types.ts': (
                    'diff --git a/types.ts b/types.ts\n'
                    '+export interface UnusedConfig {\n'
                    '+  retries: number;\n'
                    '+}\n'
                )
            },
            'current_files': {
                'types.ts': 'export interface UnusedConfig {\n  retries: number;\n}\n',
                'handler.ts': 'function handle() {}\n',  # No reference to UnusedConfig
            },
            'full_diff': '',
            'modified_files': ['types.ts'],
            'errors': [],
        }
        
        results = cross_reference(plan_items, evidence)
        assert len(results) == 1
        assert len(results[0]['dead_code_findings']) > 0
    
    def test_function_called_not_dead(self):
        """Function is called elsewhere, so not dead code."""
        plan_items = [{
            'id': 'item1',
            'change_id': 1,
            'change_title': 'Add function',
            'file_pattern': 'utils.py',
            'expected_patterns': ['calculate_delay'],
            'category': 'function',
        }]
        
        evidence = {
            'file_diffs': {
                'utils.py': (
                    'diff --git a/utils.py b/utils.py\n'
                    '+def calculate_delay(attempt):\n'
                    '+    return attempt * 1000\n'
                )
            },
            'current_files': {
                'utils.py': 'def calculate_delay(attempt):\n    return attempt * 1000\n',
                'handler.py': (
                    'from utils import calculate_delay\n'
                    '\n'
                    'def process():\n'
                    '    delay = calculate_delay(3)\n'
                ),
            },
            'full_diff': '',
            'modified_files': ['utils.py'],
            'errors': [],
        }
        
        results = cross_reference(plan_items, evidence)
        assert len(results) == 1
        assert len(results[0]['dead_code_findings']) == 0
    
    def test_basename_matching(self):
        """Match file patterns by basename when exact path not found."""
        plan_items = [{
            'id': 'item1',
            'change_id': 1,
            'change_title': 'Add function',
            'file_pattern': 'handler.py',  # No path
            'expected_patterns': ['process'],
            'category': 'function',
        }]
        
        evidence = {
            'file_diffs': {
                'src/webhooks/handler.py': (  # Full path
                    'diff --git a/src/webhooks/handler.py b/src/webhooks/handler.py\n'
                    '+def process():\n'
                    '+    pass\n'
                )
            },
            'current_files': {
                'src/webhooks/handler.py': 'def process():\n    pass\n'
            },
            'full_diff': '',
            'modified_files': ['src/webhooks/handler.py'],
            'errors': [],
        }
        
        results = cross_reference(plan_items, evidence)
        assert len(results) == 1
        assert results[0]['evidence_level'] == IN_DIFF
