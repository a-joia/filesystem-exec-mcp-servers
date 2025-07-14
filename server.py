import os
from fastmcp import FastMCP
from tools.filesystem import (
    set_workspace, get_workspace, edit_file, preview_edit, validate_edit, backup_file, restore_file, list_backups, commit_changes, compare_versions, generate_diff, format_code, list_path, list_path_recursive, get_head, get_tail, get_lines
)
from tools.analysis import (
    check_syntax, check_syntax_multiple_files, lint_file, run_mutation_tests, search_code, search_symbols, find_unused_code, extract_docstrings, suggest_test_cases
)
from tools.exec_debug import (
    execute_python, execute_python_file, debug_python_file
)


def create_server():
    mcp = FastMCP(
        name="Development MCP Server",
        instructions="A comprehensive development server with filesystem, execution, analysis, and code tools."
    )

    # --- Filesystem & Code-Editing Tools ---

    @mcp.tool()
    async def set_workspace_mcp(workspace_name: str):
        """Set the active workspace directory.\nInput: workspace_name (str)\nOutput: dict with status, old_workspace, new_workspace, message"""
        return set_workspace(workspace_name)

    @mcp.tool()
    async def get_workspace_mcp():
        """Get the current workspace path and status.\nInput: none\nOutput: dict with status, workspace, exists, is_dir"""
        return get_workspace()

    @mcp.tool()
    async def edit_file_mcp(filepath: str, content: str = None, create_backup: bool = True, mode: str = None, diff_text: str = None, line_number: int = None, new_content: str = None, start_line: int = None, end_line: int = None):
        """Edit a file atomically. Supports overwrite, unified diff, line edit, span edit.\nInputs: filepath (str), content (str), create_backup (bool), mode (str), diff_text (str), line_number (int), new_content (str), start_line (int), end_line (int)\nOutput: dict with status, filepath, mode, changes_made, preview, etc."""
        return edit_file(filepath, content, create_backup, mode, diff_text, line_number, new_content, start_line, end_line)

    @mcp.tool()
    async def preview_edit_mcp(
        filepath: str,
        content: str = None,
        create_backup: bool = True,
        mode: str = None,
        diff_text: str = None,
        line_number: int = None,
        new_content: str = None,
        start_line: int = None,
        end_line: int = None
    ):
        """Preview an edit without applying it.\nInputs: same as edit_file\nOutput: dict with status, preview, changes_made"""
        return preview_edit(
            filepath,
            content=content,
            create_backup=create_backup,
            mode=mode,
            diff_text=diff_text,
            line_number=line_number,
            new_content=new_content,
            start_line=start_line,
            end_line=end_line
        )

    @mcp.tool()
    async def validate_edit_mcp(
        filepath: str,
        content: str = None,
        create_backup: bool = True,
        mode: str = None,
        diff_text: str = None,
        line_number: int = None,
        new_content: str = None,
        start_line: int = None,
        end_line: int = None
    ):
        """Validate an edit without applying it.\nInputs: same as edit_file\nOutput: dict with status, validation_errors"""
        return validate_edit(
            filepath,
            content=content,
            create_backup=create_backup,
            mode=mode,
            diff_text=diff_text,
            line_number=line_number,
            new_content=new_content,
            start_line=start_line,
            end_line=end_line
        )

    @mcp.tool()
    async def backup_file_mcp(filepath: str):
        """Create a timestamped backup of a file.\nInput: filepath (str)\nOutput: dict with status, backup_file, timestamp, etc."""
        return backup_file(filepath)

    @mcp.tool()
    async def restore_file_mcp(filepath: str, backup_timestamp: str = None):
        """Restore a file from a backup.\nInputs: filepath (str), backup_timestamp (str, optional)\nOutput: dict with status, restored_from, etc."""
        if backup_timestamp is not None:
            return restore_file(filepath, backup_timestamp)
        else:
            return restore_file(filepath)

    @mcp.tool()
    async def list_backups_mcp(filepath: str = None):
        """List all backups for a file or all files.\nInput: filepath (str, optional)\nOutput: dict with status, backups, total_backups"""
        if filepath is not None:
            return list_backups(filepath)
        else:
            return list_backups()

    @mcp.tool()
    async def commit_changes_mcp(filepath: str, commit_message: str = ""): 
        """Mark the latest backup as committed.\nInputs: filepath (str), commit_message (str)\nOutput: dict with status, commit_message, etc."""
        if commit_message is not None:
            return commit_changes(filepath, commit_message)
        else:
            return commit_changes(filepath)

    @mcp.tool()
    async def compare_versions_mcp(filepath: str, backup_timestamp: str = None):
        """Show a unified diff between the current file and a backup.\nInputs: filepath (str), backup_timestamp (str, optional)\nOutput: dict with status, diff, etc."""
        if backup_timestamp is not None:
            return compare_versions(filepath, backup_timestamp)
        else:
            return compare_versions(filepath)

    @mcp.tool()
    async def generate_diff_mcp(text1: str, text2: str, filename: str = "file.txt"):
        """Generate a unified diff between two text blobs.\nInputs: text1 (str), text2 (str), filename (str)\nOutput: dict with status, diff"""
        if filename is not None:
            return generate_diff(text1, text2, filename)
        else:
            return generate_diff(text1, text2)

    @mcp.tool()
    async def format_code_mcp(filepath: str):
        """Format a Python file using black.\nInput: filepath (str)\nOutput: dict with status, message"""
        return format_code(filepath)

    @mcp.tool()
    async def list_path_mcp(path: str = "."):
        """List files and directories at a given path (non-recursive).\nInput: path (str)\nOutput: dict with status, entries"""
        return list_path(path)

    @mcp.tool()
    async def list_path_recursive_mcp(path: str = "."):
        """List all files and directories under a path, recursively.\nInput: path (str)\nOutput: dict with status, entries"""
        return list_path_recursive(path)

    @mcp.tool()
    async def get_head_mcp(filepath: str, n: int = 10):
        """Get the first n lines of a file.\nInputs: filepath (str), n (int)\nOutput: dict with status, lines"""
        return get_head(filepath, n)

    @mcp.tool()
    async def get_tail_mcp(filepath: str, n: int = 10):
        """Get the last n lines of a file.\nInputs: filepath (str), n (int)\nOutput: dict with status, lines"""
        return get_tail(filepath, n)

    @mcp.tool()
    async def get_lines_mcp(filepath: str, start: int, end: int):
        """Get lines from start to end (inclusive, 1-based).\nInputs: filepath (str), start (int), end (int)\nOutput: dict with status, lines"""
        return get_lines(filepath, start, end)

    # --- Analysis Tools ---

    @mcp.tool()
    async def check_syntax_mcp(filepath: str):
        """Check Python syntax.\nInput: filepath (str)\nOutput: list of error messages (empty if valid)"""
        return check_syntax(filepath)

    @mcp.tool()
    async def check_syntax_multiple_files_mcp(filepaths: list):
        """Check syntax for multiple files.\nInput: filepaths (list of str)\nOutput: dict mapping file path to list of errors"""
        return check_syntax_multiple_files(filepaths)

    @mcp.tool()
    async def lint_file_mcp(filepath: str):
        """Run flake8 linter on a file.\nInput: filepath (str)\nOutput: linter output as string"""
        return lint_file(filepath)

    @mcp.tool()
    async def run_mutation_tests_mcp(filepath: str, test_file: str = None):
        """Run mutation tests using mutmut.\nInputs: filepath (str), test_file (str, optional)\nOutput: string with mutation test output"""
        if test_file is not None:
            return run_mutation_tests(filepath, test_file=test_file)
        else:
            return run_mutation_tests(filepath)

    @mcp.tool()
    async def search_code_mcp(pattern: str, directory: str = ".", file_pattern: str = "*.py"):
        """Search for a regex pattern in code files.\nInputs: pattern (str), directory (str), file_pattern (str)\nOutput: list of dicts with file, line, code"""
        if directory is not None and file_pattern is not None:
            return search_code(pattern, directory, file_pattern=file_pattern)
        elif directory is not None:
            return search_code(pattern, directory)
        else:
            return search_code(pattern)

    @mcp.tool()
    async def search_symbols_mcp(name: str, kind: str = "function", directory: str = "."):
        """Find function or class definitions by name.\nInputs: name (str), kind (str), directory (str)\nOutput: list of file:line strings"""
        if kind is not None and directory is not None:
            return search_symbols(name, kind=kind, directory=directory)
        elif kind is not None:
            return search_symbols(name, kind=kind)
        else:
            return search_symbols(name)

    @mcp.tool()
    async def find_unused_code_mcp(directory: str = "."):
        """Find unused code using vulture.\nInput: directory (str)\nOutput: list of unused code lines or error messages"""
        return find_unused_code(directory)

    @mcp.tool()
    async def extract_docstrings_mcp(filepath: str):
        """Extract docstrings from all functions and classes in a file.\nInput: filepath (str)\nOutput: dict mapping function/class names to docstrings"""
        return extract_docstrings(filepath)

    @mcp.tool()
    async def suggest_test_cases_mcp(filepath: str, function: str = None):
        """Generate a test skeleton for a function or file.\nInputs: filepath (str), function (str, optional)\nOutput: string with test function or file template"""
        if function is not None:
            return suggest_test_cases(filepath, function=function)
        else:
            return suggest_test_cases(filepath)

    # --- Execution & Debugging Tools ---

    @mcp.tool()
    async def execute_python_mcp(code: str, timeout: int = 30):
        """Execute Python code (as a string) in a subprocess.\nInputs: code (str), timeout (int)\nOutput: dict with status, stdout, stderr, return_code, execution_time"""
        if timeout is not None:
            return execute_python(code, timeout=timeout)
        else:
            return execute_python(code)

    @mcp.tool()
    async def execute_python_file_mcp(file: str, timeout: int = 30):
        """Execute a Python file in a subprocess.\nInputs: file (str), timeout (int)\nOutput: dict with status, stdout, stderr, return_code, execution_time"""
        if timeout is not None:
            return execute_python_file(file, timeout=timeout)
        else:
            return execute_python_file(file)

    @mcp.tool()
    async def debug_python_file_mcp(file: str, breakpoints: list, timeout: int = 60):
        """Run a Python file under pdb with breakpoints.\nInputs: file (str), breakpoints (list of int), timeout (int)\nOutput: string with pdb session transcript"""
        if timeout is not None:
            return debug_python_file(file, breakpoints, timeout=timeout)
        else:
            return debug_python_file(file, breakpoints, timeout=60)

    return mcp


MCP_MODE = os.getenv("MCP_MODE", "stdio")

if __name__ == "__main__":
    mcp = create_server()
    if MCP_MODE == "stdio":
        print("Starting MCP server in stdio mode")
        mcp.run(transport="stdio")
    else:
        print("Starting MCP server in HTTP mode on 0.0.0.0:8080")
        mcp.run(transport="http", host="0.0.0.0", port=8080) 