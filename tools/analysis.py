"""
Static & Dynamic Analysis Tools
"""

import ast
import subprocess
from pathlib import Path
from typing import Any, Dict, List

def check_syntax(filepath: str) -> List[str]:
    src = Path(filepath).read_text(encoding="utf-8")
    try:
        compile(src, filepath, "exec")
        return []
    except SyntaxError as err:
        return [f"{err.filename}:{err.lineno}:{err.msg}"]

def check_syntax_multiple_files(filepaths: List[str]) -> Dict[str, List[str]]:
    return {fp: check_syntax(fp) for fp in filepaths}

def lint_file(filepath: str) -> str:
    try:
        result = subprocess.run(["flake8", filepath], capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return f"lint_file error: {e}"

def run_mutation_tests(filepath: str, *, test_file: str = None) -> str:
    try:
        cmd = ["mutmut", "run", filepath]
        if test_file:
            cmd += ["--tests", test_file]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.stdout + result.stderr
    except Exception as e:
        return f"mutation tests error: {e}"

def search_code(pattern: str, directory: str = ".", *, file_pattern: str = "*.py") -> List[Dict[str, Any]]:
    import re
    dir_path = Path(directory)
    results: List[Dict[str, Any]] = []
    regex = re.compile(pattern)
    for path in dir_path.rglob(file_pattern):
        for lineno, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
            if regex.search(line):
                results.append({"file": str(path), "line": lineno, "code": line.strip()})
    return results

def search_symbols(name: str, *, kind: str = "function", directory: str = ".") -> List[str]:
    import re
    matches: List[str] = []
    if kind == "function":
        pattern = rf"def {re.escape(name)}\s*\("
    elif kind == "class":
        pattern = rf"class {re.escape(name)}\s*\("
    else:
        pattern = rf"{re.escape(name)}"
    for item in search_code(pattern, directory):
        matches.append(f"{item['file']}:{item['line']}")
    return matches

def find_unused_code(directory: str = ".") -> List[str]:
    try:
        result = subprocess.run(["vulture", directory], capture_output=True, text=True)
        return result.stdout.splitlines()
    except Exception as e:
        return [f"find_unused_code error: {e}"]

def extract_docstrings(filepath: str) -> Dict[str, str]:
    tree = ast.parse(Path(filepath).read_text(encoding="utf-8"))
    docs: Dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(node):
            docs[node.name] = ast.get_docstring(node) or ""
    return docs

def suggest_test_cases(filepath: str, function: str = None) -> str:
    # Basic test skeleton generator
    if function:
        return f"def test_{function}():\n    # TODO: implement test for {function}\n    assert False\n"
    else:
        return f"# TODO: implement tests for {filepath}\n" 