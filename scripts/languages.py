"""
Language pattern registry for plan-implemented.

Each language entry defines:
  extensions   — file extensions that identify this language
  fences       — code fence names (```rust, ```py, etc.)
  declarations — regexes to extract declared identifiers from code blocks
                 Each regex must have group(1) = the identifier name.
  call_pattern — how function calls look, with {name} placeholder
  access_pattern — how field/property access looks, with {name} placeholder
  noise_words  — keywords to exclude from pattern extraction

To add a new language, add an entry to LANGUAGES below. The key is a
human-readable name; the matching is done via extensions and fences.
"""

import re
from pathlib import Path
from typing import Optional


LANGUAGES: dict[str, dict] = {
    'typescript': {
        'extensions': ['.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs'],
        'fences': ['typescript', 'ts', 'javascript', 'js', 'jsx', 'tsx'],
        'declarations': {
            'type': r'(?:export\s+)?(?:type|interface|enum)\s+(\w+)',
            'function': r'(?:export\s+)?(?:static\s+)?(?:private\s+)?(?:protected\s+)?(?:async\s+)?(\w+)\s*\(',
            'field': r'(\w+)\??\s*:\s*(?:\w+)',
            'constant': r'(?:const|let|var)\s+(\w+)',
            'string_enum': r"'(\w+(?:_\w+)+)'",
        },
        'call_pattern': r'{name}\s*\(',
        'access_pattern': r'\.{name}\b',
        'noise_words': [
            'if', 'for', 'while', 'switch', 'return', 'new', 'throw',
            'catch', 'import', 'from', 'export', 'default', 'extends',
            'implements', 'constructor', 'super', 'this', 'true', 'false',
            'null', 'undefined', 'typeof', 'instanceof', 'void', 'delete',
            'e', 'i', 'j', 'key', 'value', 'type', 'content',
        ],
    },

    'python': {
        'extensions': ['.py', '.pyi'],
        'fences': ['python', 'py'],
        'declarations': {
            'type': r'class\s+(\w+)',
            'function': r'(?:async\s+)?def\s+(\w+)\s*\(',
            'field': r'self\.(\w+)\s*=',
            'constant': r'^([A-Z_][A-Z0-9_]+)\s*=',
            'decorator': r'@(\w+)',
        },
        'call_pattern': r'{name}\s*\(',
        'access_pattern': r'\.{name}\b',
        'noise_words': [
            'if', 'for', 'while', 'return', 'import', 'from', 'class',
            'def', 'self', 'cls', 'True', 'False', 'None', 'pass',
            'with', 'as', 'in', 'not', 'and', 'or', 'is', 'lambda',
            'e', 'i', 'j', 'key', 'value', 'args', 'kwargs',
        ],
    },

    'rust': {
        'extensions': ['.rs'],
        'fences': ['rust', 'rs'],
        'declarations': {
            'type': r'(?:pub\s+)?(?:struct|enum|trait|type)\s+(\w+)',
            'function': r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)',
            'field': r'(\w+)\s*:\s*(?:\w+)',
            'constant': r'(?:const|static)\s+(\w+)',
            'impl': r'impl(?:<[^>]*>)?\s+(\w+)',
            'macro': r'macro_rules!\s+(\w+)',
        },
        'call_pattern': r'{name}\s*[(\!]',
        'access_pattern': r'(?:\.{name}\b|{name}::)',
        'noise_words': [
            'if', 'for', 'while', 'match', 'return', 'let', 'mut',
            'pub', 'fn', 'use', 'mod', 'self', 'Self', 'super',
            'impl', 'where', 'true', 'false', 'Some', 'None', 'Ok', 'Err',
            'i', 'e', 'key', 'value',
        ],
    },

    'go': {
        'extensions': ['.go'],
        'fences': ['go', 'golang'],
        'declarations': {
            'type': r'type\s+(\w+)\s+(?:struct|interface)',
            'function': r'func\s+(?:\([^)]*\)\s+)?(\w+)\s*\(',
            'field': r'(\w+)\s+\w+(?:\s+`[^`]*`)?$',
            'constant': r'(?:const|var)\s+(\w+)',
        },
        'call_pattern': r'{name}\s*\(',
        'access_pattern': r'\.{name}\b',
        'noise_words': [
            'if', 'for', 'range', 'return', 'func', 'var', 'const',
            'import', 'package', 'type', 'struct', 'interface',
            'true', 'false', 'nil', 'err',
            'i', 'j', 'key', 'value',
        ],
    },

    'java': {
        'extensions': ['.java', '.kt', '.kts'],
        'fences': ['java', 'kotlin', 'kt'],
        'declarations': {
            'type': r'(?:public\s+|private\s+|protected\s+)?(?:abstract\s+)?(?:class|interface|enum|record)\s+(\w+)',
            'function': r'(?:public\s+|private\s+|protected\s+)?(?:static\s+)?(?:abstract\s+)?(?:synchronized\s+)?(?:\w+(?:<[^>]*>)?\s+)(\w+)\s*\(',
            'field': r'(?:private|protected|public)\s+(?:static\s+)?(?:final\s+)?(?:\w+)\s+(\w+)\s*[;=]',
            'constant': r'(?:static\s+final|final\s+static)\s+\w+\s+(\w+)',
            'annotation': r'@(\w+)',
        },
        'call_pattern': r'{name}\s*\(',
        'access_pattern': r'\.{name}\b',
        'noise_words': [
            'if', 'for', 'while', 'switch', 'return', 'new', 'throw',
            'catch', 'import', 'class', 'public', 'private', 'protected',
            'static', 'final', 'void', 'this', 'super', 'extends',
            'implements', 'true', 'false', 'null',
            'e', 'i', 'j', 'key', 'value', 'args',
        ],
    },

    'c': {
        'extensions': ['.c', '.h', '.cpp', '.cc', '.cxx', '.hpp', '.hxx', '.hh'],
        'fences': ['c', 'cpp', 'c++', 'cxx'],
        'declarations': {
            'type': r'(?:typedef\s+)?(?:struct|enum|union|class)\s+(\w+)',
            'function': r'(?:\w+[\s*]+)(\w+)\s*\([^;]*\)\s*\{',
            'field': r'(?:\w+[\s*]+)(\w+)\s*;',
            'constant': r'#define\s+(\w+)',
            'template': r'template\s*<[^>]*>\s*(?:class|struct)\s+(\w+)',
        },
        'call_pattern': r'{name}\s*\(',
        'access_pattern': r'(?:\.{name}\b|->{name}\b)',
        'noise_words': [
            'if', 'for', 'while', 'switch', 'return', 'sizeof', 'typedef',
            'struct', 'enum', 'union', 'void', 'int', 'char', 'float',
            'double', 'long', 'short', 'unsigned', 'signed', 'const',
            'static', 'extern', 'inline', 'NULL', 'nullptr', 'true', 'false',
            'public', 'private', 'protected', 'virtual', 'override',
            'class', 'namespace', 'template', 'typename',
            'i', 'j', 'n', 'p', 'buf', 'len', 'ret',
        ],
    },

    'csharp': {
        'extensions': ['.cs'],
        'fences': ['csharp', 'cs', 'c#'],
        'declarations': {
            'type': r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:abstract\s+|sealed\s+)?(?:partial\s+)?(?:class|interface|struct|enum|record)\s+(\w+)',
            'function': r'(?:public\s+|private\s+|protected\s+|internal\s+)?(?:static\s+)?(?:async\s+)?(?:virtual\s+|override\s+|abstract\s+)?(?:\w+(?:<[^>]*>)?\s+)(\w+)\s*\(',
            'field': r'(?:private|protected|public|internal)\s+(?:static\s+)?(?:readonly\s+)?(?:\w+)\s+(\w+)\s*[;=]',
            'constant': r'const\s+\w+\s+(\w+)',
        },
        'call_pattern': r'{name}\s*\(',
        'access_pattern': r'\.{name}\b',
        'noise_words': [
            'if', 'for', 'while', 'switch', 'return', 'new', 'throw',
            'catch', 'using', 'namespace', 'class', 'public', 'private',
            'protected', 'internal', 'static', 'void', 'this', 'base',
            'true', 'false', 'null', 'var', 'async', 'await',
            'i', 'j', 'key', 'value',
        ],
    },

    'ruby': {
        'extensions': ['.rb', '.rake'],
        'fences': ['ruby', 'rb'],
        'declarations': {
            'type': r'(?:class|module)\s+(\w+)',
            'function': r'def\s+(?:self\.)?(\w+[!?]?)',
            'constant': r'([A-Z_][A-Z0-9_]+)\s*=',
            'field': r'(?:attr_reader|attr_writer|attr_accessor)\s+:(\w+)',
        },
        'call_pattern': r'{name}\s*[(\s]',
        'access_pattern': r'\.{name}\b',
        'noise_words': [
            'if', 'unless', 'while', 'until', 'for', 'return', 'def',
            'end', 'class', 'module', 'do', 'begin', 'rescue', 'ensure',
            'self', 'true', 'false', 'nil', 'require', 'include',
            'i', 'e', 'key', 'value',
        ],
    },

    'swift': {
        'extensions': ['.swift'],
        'fences': ['swift'],
        'declarations': {
            'type': r'(?:public\s+|private\s+|internal\s+|open\s+)?(?:final\s+)?(?:class|struct|enum|protocol|actor)\s+(\w+)',
            'function': r'(?:public\s+|private\s+|internal\s+|open\s+)?(?:static\s+)?(?:override\s+)?func\s+(\w+)',
            'field': r'(?:var|let)\s+(\w+)\s*:',
            'constant': r'(?:static\s+)?let\s+(\w+)',
        },
        'call_pattern': r'{name}\s*\(',
        'access_pattern': r'\.{name}\b',
        'noise_words': [
            'if', 'for', 'while', 'switch', 'return', 'guard', 'let',
            'var', 'func', 'class', 'struct', 'enum', 'protocol',
            'self', 'Self', 'true', 'false', 'nil', 'import',
            'i', 'j', 'key', 'value',
        ],
    },

    'sql': {
        'extensions': ['.sql'],
        'fences': ['sql'],
        'declarations': {
            'type': r'CREATE\s+(?:TABLE|VIEW|TYPE)\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\w+\.)?(\w+)',
            'function': r'CREATE\s+(?:OR\s+REPLACE\s+)?(?:FUNCTION|PROCEDURE)\s+(?:\w+\.)?(\w+)',
            'field': r'(\w+)\s+(?:INTEGER|TEXT|VARCHAR|BOOLEAN|TIMESTAMP|UUID|SERIAL|INT|BIGINT|FLOAT|DOUBLE|DECIMAL|DATE|BLOB|CLOB|JSON|JSONB)',
            'constant': None,
        },
        'call_pattern': r'{name}\s*\(',
        'access_pattern': r'\b{name}\b',
        'noise_words': [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE',
            'CREATE', 'ALTER', 'DROP', 'TABLE', 'INDEX', 'VIEW',
            'INTO', 'VALUES', 'SET', 'AND', 'OR', 'NOT', 'NULL',
            'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'DEFAULT',
            'id', 'name', 'type', 'value', 'status',
        ],
    },
}


# Generic fallback for unrecognized languages
GENERIC = {
    'extensions': [],
    'fences': [],
    'declarations': {
        'function': r'(?:fn|def|func|function|sub|proc)\s+(\w+)\s*\(',
        'type': r'(?:class|struct|interface|enum|type|trait|module)\s+(\w+)',
        'constant': r'(?:const|static|final|let)\s+(\w+)',
    },
    'call_pattern': r'{name}\s*\(',
    'access_pattern': r'\.{name}\b',
    'noise_words': [
        'if', 'for', 'while', 'return', 'true', 'false', 'null', 'nil',
        'i', 'j', 'e', 'key', 'value',
    ],
}


def detect_language(file_path: Optional[str] = None,
                    fence: Optional[str] = None) -> dict:
    """Detect language from file extension or code fence.

    Returns the language spec dict. Falls back to GENERIC if unknown.
    """
    if file_path:
        ext = Path(file_path).suffix.lower()
        for spec in LANGUAGES.values():
            if ext in spec['extensions']:
                return spec

    if fence:
        fence_lower = fence.lower().strip()
        for spec in LANGUAGES.values():
            if fence_lower in spec['fences']:
                return spec

    return GENERIC


def extract_patterns(code: str, lang_spec: dict) -> list[str]:
    """Extract verifiable patterns from a code block using language-specific regexes.

    Returns deduplicated list of identifier names.
    """
    patterns = []
    noise = set(lang_spec.get('noise_words', []))

    for category, regex in lang_spec.get('declarations', {}).items():
        if regex is None:
            continue
        for m in re.finditer(regex, code, re.MULTILINE):
            name = m.group(1)
            if name not in noise and len(name) > 2:
                patterns.append(name)

    # Also extract string enum values (common across languages)
    for m in re.finditer(r"['\"](\w+(?:_\w+)+)['\"]", code):
        name = m.group(1)
        if name not in noise and len(name) > 2:
            patterns.append(name)

    # Filter/condition patterns (common across languages)
    for m in re.finditer(r'(\w+)\s*(?:===?|==)\s*[\'"](\w+)[\'"]', code):
        for g in [m.group(1), m.group(2)]:
            if g not in noise and len(g) > 2:
                patterns.append(g)

    # Deduplicate preserving order
    seen = set()
    unique = []
    for p in patterns:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    return unique
