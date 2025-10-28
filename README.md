# MCP Tools: Filesystem, Analysis, and Execution

## Overview

This project provides robust, workspace-contained tools for file editing, backup, code analysis, and execution, designed for AI-driven code assistants and automation. All tools return structured dictionaries for easy programmatic use.

---

## Environment & Container Setup

### Requirements
- Python 3.11+
- Docker (for containerized use)
- Recommended: `black`, `flake8`, `vulture`, `mutmut` for code formatting and analysis

### Running in Docker

1. **Build the image:**
   ```sh
   docker build -t mcp-tools .
   ```

2. **Run the container:**
   ```sh
   docker run --rm -it -v $(pwd):/app code_exec_mcp-mcp-server
   ```
   - To map a custom workspace, use `-v /your/workspace:/app/.workspace`.

3. **Run tests inside the container:**
   ```sh
   pytest -v test/scripts
   ```

---

## Filesystem Tools (`tools/filesystem.py`)

### Workspace Management
- **set_workspace(workspace_name: str) -> dict**
  - Sets the active workspace directory (created under `.workspace/`).
  - If the workspace does not exist, it is created. All file operations are contained within this workspace for safety.
  - **Returns:** `{ "status": "success", "old_workspace": ..., "new_workspace": ..., "message": ... }`

- **get_workspace() -> dict**
  - Gets the current workspace path and status.
  - **Returns:** `{ "status": "success", "workspace": ..., "exists": ..., "is_dir": ... }`

---

### File Editing & Diff
- **edit_file(filepath, content=None, create_backup=True, mode=None, diff_text=None, line_number=None, new_content=None, start_line=None, end_line=None) -> dict**
  - Atomically edits a file. Supports several modes:
    - **Overwrite**: Replace the file with `content` (default mode).
    - **Unified diff**: Apply a unified diff (`mode="unified_diff"`, `diff_text`).
    - **Line edit**: Replace a single line (`mode="line_edit"`, `line_number`, `new_content`).
    - **Span edit**: Replace a range of lines (`mode="span_edit"`, `start_line`, `end_line`, `new_content`).
  - If `create_backup` is True, a backup is made before editing.
  - All changes are atomic (write to temp file, then move).
  - **Returns:** `{ "status": "success"|"error", "filepath": ..., "mode": ..., "changes_made": ..., "preview": ..., ... }`
  - **Edge Cases:**
    - Returns error if file is outside workspace, or if required arguments are missing for the selected mode.
    - Handles encoding issues and large files robustly.

- **preview_edit(...) / validate_edit(...)**
  - Preview or validate an edit without applying it.
  - **Returns:** Dict with status, preview, and/or validation errors.
  - **Usage:** Use before `edit_file` to check what would change or to validate arguments.

---

### Backup & Restore
- **backup_file(filepath) -> dict**
  - Creates a timestamped backup of a file in `.mcp_backups/` within the workspace.
  - Stores both the file and a JSON metadata file.
  - **Returns:** `{ "status": "success"|"error", "backup_file": ..., "timestamp": ..., ... }`
  - **Edge Cases:**
    - Returns error if file does not exist or is outside workspace.

- **restore_file(filepath, backup_timestamp=None) -> dict**
  - Restores a file from a backup (by timestamp). If no timestamp is given, restores the latest backup.
  - **Returns:** `{ "status": "success"|"error", "restored_from": ..., ... }`
  - **Edge Cases:**
    - Returns error if no backups exist or timestamp is invalid.

- **list_backups(filepath=None) -> dict**
  - Lists all backups for a file or all files in the workspace.
  - **Returns:** `{ "status": "success", "backups": [...], "total_backups": ... }`
  - Each backup entry includes file path, timestamp, commit status, and metadata.

- **commit_changes(filepath, commit_message="") -> dict**
  - Marks the latest backup as committed with a message.
  - **Returns:** `{ "status": "success"|"error", ... }`
  - **Edge Cases:**
    - Returns error if no backups exist for the file.

---

### Diff & Formatting
- **compare_versions(filepath, backup_timestamp=None) -> dict**
  - Shows a unified diff between the current file and a backup (by timestamp).
  - **Returns:** `{ "status": "success"|"error", "diff": ..., ... }`
  - **Edge Cases:**
    - Returns error if file or backup does not exist.

- **generate_diff(text1, text2, filename="file.txt") -> dict**
  - Generates a unified diff between two text blobs.
  - **Returns:** `{ "status": "success"|"error", "diff": ... }`

- **format_code(filepath) -> dict**
  - Formats a Python file using `black` (must be installed in the environment).
  - **Returns:** `{ "status": "success"|"error", "message": ... }`
  - **Edge Cases:**
    - Returns error if `black` is not installed or file is not valid Python.

---

### Filesystem Listing & File Slicing
- **list_path(path=".") -> dict**
  - Lists files and directories at a given path (non-recursive).
  - **Returns:** `{ "status": "success"|"error", "entries": [ {name, is_dir, size, mtime}, ... ] }`
  - **Edge Cases:**
    - Returns error if path does not exist or is not a directory.

- **list_path_recursive(path=".") -> dict**
  - Lists all files and directories under a path, recursively.
  - **Returns:** `{ "status": "success"|"error", "entries": [ {path, is_dir, size, mtime}, ... ] }`

- **get_head(filepath, n=10) -> dict**
  - Gets the first `n` lines of a file (default 10).
  - **Returns:** `{ "status": "success"|"error", "lines": [...] }`
  - **Edge Cases:**
    - Returns all lines if file has fewer than `n` lines.
    - Returns error if file does not exist.

- **get_tail(filepath, n=10) -> dict**
  - Gets the last `n` lines of a file (default 10).
  - **Returns:** `{ "status": "success"|"error", "lines": [...] }`
  - **Edge Cases:**
    - Returns all lines if file has fewer than `n` lines.
    - Returns error if file does not exist.

- **get_lines(filepath, start, end) -> dict**
  - Gets lines from `start` to `end` (inclusive, 1-based).
  - **Returns:** `{ "status": "success"|"error", "lines": [...] }`
  - **Edge Cases:**
    - Returns error if range is invalid or file does not exist.

---

## Analysis Tools (`tools/analysis.py`)

- **check_syntax(filepath) -> List[str]**
  - Checks Python syntax. Returns an empty list if valid, else a list of error messages (one per error).
  - **Edge Cases:**
    - Handles syntax errors, missing files, and encoding issues.

- **check_syntax_multiple_files(filepaths) -> Dict[str, List[str]]**
  - Checks syntax for multiple files. Returns a dict mapping file paths to lists of errors.

- **lint_file(filepath) -> str**
  - Runs `flake8` linter on a file. Returns the linter output as a string.
  - **Edge Cases:**
    - Returns error message if `flake8` is not installed or file is missing.

- **run_mutation_tests(filepath, test_file=None) -> str**
  - Runs mutation tests using `mutmut`. Optionally specify a test file.
  - **Returns:** Output of the mutation test run.

- **search_code(pattern, directory=".", file_pattern="*.py") -> List[Dict]**
  - Searches for a regex pattern in code files under a directory.
  - **Returns:** List of dicts with file, line number, and code line.

- **search_symbols(name, kind="function", directory=".") -> List[str]**
  - Finds function or class definitions by name.
  - **Returns:** List of file:line strings where the symbol is found.

- **find_unused_code(directory=".") -> List[str]**
  - Finds unused code using `vulture`.
  - **Returns:** List of unused code lines or error messages.

- **extract_docstrings(filepath) -> Dict[str, str]**
  - Extracts docstrings from all functions and classes in a file.
  - **Returns:** Dict mapping function/class names to docstrings.

- **suggest_test_cases(filepath, function=None) -> str**
  - Generates a test skeleton for a function or file.
  - **Returns:** String with a test function or file template.

---

## Execution & Debugging Tools (`tools/exec_debug.py`)

- **execute_python(code, timeout=30) -> Dict**
  - Executes Python code (as a string) in a subprocess, with a timeout.
  - **Returns:** Dict with status, stdout, stderr, return code, and execution time.
  - **Edge Cases:**
    - Returns error status and message if execution fails or times out.

- **execute_python_file(file, timeout=30) -> Dict**
  - Executes a Python file in a subprocess, with a timeout.
  - **Returns:** Dict with status, stdout, stderr, return code, and execution time.

- **debug_python_file(file, breakpoints, timeout=60) -> str**
  - Runs a Python file under `pdb` with breakpoints at specified line numbers.
  - **Returns:** The full session transcript as a string.
  - **Edge Cases:**
    - Raises FileNotFoundError if the file does not exist.
    - Captures exceptions and prints them in the transcript.

---

## Usage

- All functions are designed to be imported and called from Python, or used as part of an AI agent toolset.
- All file operations are workspace-contained for safety.
- All results are returned as dictionaries (or lists for some analysis functions), with `"status": "success"` or `"error"` and detailed fields.

---
