"""
Filesystem & Code-Editing Tools (backup-based)
"""

import os
import shutil
import json
import difflib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import subprocess
import tempfile

_BASE_WORKSPACE = Path('.workspace').resolve()
_DEFAULT_WORKSPACE = _BASE_WORKSPACE / 'default'
_WORKSPACE_ROOT: Optional[Path] = None
_BACKUP_DIRNAME = '.mcp_backups'

class EditMode:
    UNIFIED_DIFF = "unified_diff"
    LINE_EDIT = "line_edit"
    SPAN_EDIT = "span_edit"

# --- Workspace Management ---
def _require_workspace() -> Path:
    global _WORKSPACE_ROOT
    if _WORKSPACE_ROOT is None:
        _WORKSPACE_ROOT = _DEFAULT_WORKSPACE
        _WORKSPACE_ROOT.mkdir(parents=True, exist_ok=True)
    return _WORKSPACE_ROOT

def set_workspace(workspace_name: str) -> dict:
    global _WORKSPACE_ROOT
    old_workspace = str(_WORKSPACE_ROOT) if _WORKSPACE_ROOT else None
    name = Path(workspace_name).name
    root = _BASE_WORKSPACE / name
    root.mkdir(parents=True, exist_ok=True)
    _WORKSPACE_ROOT = root
    return {
        "status": "success",
        "old_workspace": old_workspace,
        "new_workspace": str(_WORKSPACE_ROOT),
        "message": f"Workspace set to {root}"
    }

def get_workspace() -> dict:
    ws = _require_workspace()
    return {
        "status": "success",
        "workspace": str(ws),
        "exists": ws.exists(),
        "is_dir": ws.is_dir()
    }

def _resolve_path(filepath: str) -> Path:
    ws = _require_workspace().resolve()
    full_path = (ws / filepath.lstrip("/")).resolve()
    # Robust workspace containment check
    try:
        # Python 3.9+: use is_relative_to
        if not full_path.is_relative_to(ws):
            raise PermissionError("Attempt to access file outside workspace")
    except AttributeError:
        # Fallback for Python <3.9
        ws_parts = ws.parts
        full_parts = full_path.parts
        if ws_parts != full_parts[:len(ws_parts)]:
            raise PermissionError("Attempt to access file outside workspace")
    return full_path

# --- AI-Friendly Edit Helpers ---
def _read_file_lines(file_path: Path) -> List[str]:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.readlines()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as f:
            return f.readlines()

def _write_file_lines_atomic(file_path: Path, lines: List[str]) -> None:
    # Atomic write: write to temp file, then move
    dir_path = file_path.parent
    with tempfile.NamedTemporaryFile('w', delete=False, dir=dir_path, encoding='utf-8') as tmp:
        tmp.writelines(lines)
        temp_path = Path(tmp.name)
    shutil.move(str(temp_path), str(file_path))

def _apply_unified_diff(original_lines: List[str], diff_text: str) -> List[str]:
    # Use difflib to patch
    diff_lines = diff_text.splitlines()
    # Check for at least one ndiff prefix line
    if not any(line.startswith((' ', '+', '-')) for line in diff_lines):
        raise ValueError("Invalid ndiff format: no diff line prefixes found")
    try:
        patched = list(difflib.restore(diff_lines, 2))
    except Exception as e:
        raise ValueError(f"Failed to apply ndiff: {e}")
    return [line + '\n' if not line.endswith('\n') else line for line in patched]

def _apply_line_edit(original_lines: List[str], line_number: int, new_content: str) -> List[str]:
    lines = original_lines.copy()
    idx = line_number - 1
    if idx < 0 or idx >= len(lines):
        raise IndexError("Line number out of range")
    lines[idx] = new_content if new_content.endswith('\n') else new_content + '\n'
    return lines

def _apply_span_edit(original_lines: List[str], start_line: int, end_line: int, new_content: str) -> List[str]:
    lines = original_lines.copy()
    start_idx = start_line - 1
    end_idx = end_line
    if start_idx < 0 or end_idx > len(lines) or start_idx > end_idx:
        raise IndexError("Span out of range")
    new_lines = [l if l.endswith('\n') else l + '\n' for l in new_content.splitlines()]
    return lines[:start_idx] + new_lines + lines[end_idx:]

def _diff_preview(original: List[str], edited: List[str], file_name: str) -> str:
    return ''.join(difflib.unified_diff(original, edited, fromfile=f"a/{file_name}", tofile=f"b/{file_name}"))

# --- Main AI-Friendly Edit Function ---
def edit_file(filepath: str, content: str = None, create_backup: bool = True, mode: str = None, diff_text: str = None, line_number: int = None, new_content: str = None, start_line: int = None, end_line: int = None) -> dict:
    try:
        file_path = _resolve_path(filepath)
        original_lines = _read_file_lines(file_path) if file_path.exists() else []
        backup_info = None
        if create_backup and file_path.exists():
            backup_info = backup_file(filepath)
        # AI editing modes
        if mode == EditMode.UNIFIED_DIFF:
            if not diff_text:
                return {"status": "error", "message": "diff_text required for unified_diff mode"}
            edited_lines = _apply_unified_diff(original_lines, diff_text)
        elif mode == EditMode.LINE_EDIT:
            if line_number is None or new_content is None:
                return {"status": "error", "message": "line_number and new_content required for line_edit mode"}
            edited_lines = _apply_line_edit(original_lines, line_number, new_content)
        elif mode == EditMode.SPAN_EDIT:
            if start_line is None or end_line is None or new_content is None:
                return {"status": "error", "message": "start_line, end_line, and new_content required for span_edit mode"}
            edited_lines = _apply_span_edit(original_lines, start_line, end_line, new_content)
        else:
            # Default: overwrite with content
            if content is None:
                return {"status": "error", "message": "content required for default edit"}
            edited_lines = [l if l.endswith('\n') else l + '\n' for l in content.splitlines()]
        # Atomic write
        _write_file_lines_atomic(file_path, edited_lines)
        preview = _diff_preview(original_lines, edited_lines, file_path.name)
        result = {
            "status": "success",
            "filepath": str(file_path),
            "mode": mode or "overwrite",
            "changes_made": original_lines != edited_lines,
            "preview": preview,
            "message": "File edited successfully (atomic)",
        }
        if backup_info and backup_info.get("status") == "success":
            result["backup_created"] = True
            result["backup_file"] = backup_info["backup_file"]
            result["backup_timestamp"] = backup_info["timestamp"]
        return result
    except PermissionError:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Preview and Validation ---
def preview_edit(filepath: str, **kwargs) -> dict:
    try:
        file_path = _resolve_path(filepath)
        original_lines = _read_file_lines(file_path) if file_path.exists() else []
        mode = kwargs.get('mode')
        diff_text = kwargs.get('diff_text')
        line_number = kwargs.get('line_number')
        new_content = kwargs.get('new_content')
        start_line = kwargs.get('start_line')
        end_line = kwargs.get('end_line')
        content = kwargs.get('content')
        if mode == EditMode.UNIFIED_DIFF:
            if not diff_text:
                return {"status": "error", "message": "diff_text required for unified_diff mode"}
            edited_lines = _apply_unified_diff(original_lines, diff_text)
        elif mode == EditMode.LINE_EDIT:
            if line_number is None or new_content is None:
                return {"status": "error", "message": "line_number and new_content required for line_edit mode"}
            edited_lines = _apply_line_edit(original_lines, line_number, new_content)
        elif mode == EditMode.SPAN_EDIT:
            if start_line is None or end_line is None or new_content is None:
                return {"status": "error", "message": "start_line, end_line, and new_content required for span_edit mode"}
            edited_lines = _apply_span_edit(original_lines, start_line, end_line, new_content)
        else:
            if content is None:
                return {"status": "error", "message": "content required for default preview"}
            edited_lines = [l if l.endswith('\n') else l + '\n' for l in content.splitlines()]
        preview = _diff_preview(original_lines, edited_lines, file_path.name)
        return {
            "status": "success",
            "filepath": str(file_path),
            "mode": mode or "overwrite",
            "preview": preview,
            "changes_made": original_lines != edited_lines
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def validate_edit(filepath: str, **kwargs) -> dict:
    try:
        file_path = _resolve_path(filepath)
        original_lines = _read_file_lines(file_path) if file_path.exists() else []
        mode = kwargs.get('mode')
        diff_text = kwargs.get('diff_text')
        line_number = kwargs.get('line_number')
        new_content = kwargs.get('new_content')
        start_line = kwargs.get('start_line')
        end_line = kwargs.get('end_line')
        content = kwargs.get('content')
        errors = []
        if mode == EditMode.UNIFIED_DIFF:
            if not diff_text:
                errors.append("diff_text required for unified_diff mode")
        elif mode == EditMode.LINE_EDIT:
            if line_number is None or new_content is None:
                errors.append("line_number and new_content required for line_edit mode")
            elif line_number < 1 or (file_path.exists() and line_number > len(original_lines)):
                errors.append("line_number out of range")
        elif mode == EditMode.SPAN_EDIT:
            if start_line is None or end_line is None or new_content is None:
                errors.append("start_line, end_line, and new_content required for span_edit mode")
            elif start_line < 1 or end_line < start_line or (file_path.exists() and end_line > len(original_lines)):
                errors.append("span out of range")
        else:
            if content is None:
                errors.append("content required for default edit")
        return {
            "status": "success" if not errors else "error",
            "validation_errors": errors
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Backup & Restore ---
def backup_file(filepath: str) -> dict:
    try:
        full_path = _resolve_path(filepath)  # This will raise PermissionError if out of workspace
        if not full_path.exists():
            return {"status": "error", "message": "File does not exist"}
        backups_dir = _require_workspace() / _BACKUP_DIRNAME
        backups_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        backup_filename = f"{full_path.stem}_{timestamp}{full_path.suffix}"
        backup_path = backups_dir / backup_filename
        shutil.copy2(full_path, backup_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        backup_metadata = {
            "original_file": str(full_path),
            "backup_file": str(backup_path),
            "timestamp": timestamp,
            "datetime": datetime.now().isoformat(),
            "original_content": original_content,
            "committed": False
        }
        metadata_file = backups_dir / f"{backup_filename}.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(backup_metadata, f, indent=2)
        return {
            "status": "success",
            "original_file": str(full_path),
            "backup_file": str(backup_path),
            "timestamp": timestamp,
            "message": "Backup created successfully"
        }
    except PermissionError:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}

def restore_file(filepath: str, backup_timestamp: str = None) -> dict:
    try:
        full_path = _resolve_path(filepath)
        backups_dir = _require_workspace() / _BACKUP_DIRNAME
        if not backups_dir.exists():
            return {"status": "error", "message": "No backups directory found"}
        backup_files = [b for b in backups_dir.glob(f"{full_path.stem}_*{full_path.suffix}") if b.suffix == full_path.suffix]
        if not backup_files:
            return {"status": "error", "message": "No backups found for this file"}
        backup_files.sort(key=lambda x: x.name, reverse=True)
        if backup_timestamp:
            target_backup = None
            for backup_file in backup_files:
                if backup_timestamp in backup_file.name:
                    target_backup = backup_file
                    break
            if not target_backup:
                return {"status": "error", "message": f"Backup with timestamp {backup_timestamp} not found"}
        else:
            target_backup = backup_files[0]
        shutil.copy2(target_backup, full_path)
        return {
            "status": "success",
            "filepath": str(full_path),
            "restored_from": str(target_backup),
            "message": "File restored successfully"
        }
    except PermissionError:
        raise
    except Exception as e:
        return {"status": "error", "message": str(e)}

def list_backups(filepath: str = None) -> dict:
    try:
        backups_dir = _require_workspace() / _BACKUP_DIRNAME
        if not backups_dir.exists():
            return {"status": "success", "backups": [], "total_backups": 0, "message": "No backups directory found"}
        backups = []
        if filepath:
            full_path = _resolve_path(filepath)
            for backup_file in backups_dir.glob(f"{full_path.stem}_*{full_path.suffix}"):
                if backup_file.suffix == full_path.suffix:
                    metadata_file = backups_dir / f"{backup_file.name}.json"
                    metadata = {}
                    if metadata_file.exists():
                        with open(metadata_file, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    backups.append({
                        "backup_file": str(backup_file),
                        "timestamp": metadata.get("timestamp", ""),
                        "datetime": metadata.get("datetime", ""),
                        "committed": metadata.get("committed", False),
                        "commit_message": metadata.get("commit_message", ""),
                        "original_file": metadata.get("original_file", str(full_path))
                    })
        else:
            for metadata_file in backups_dir.glob("*.json"):
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                backup_file = Path(metadata["backup_file"])
                if backup_file.exists():
                    backups.append({
                        "backup_file": str(backup_file),
                        "timestamp": metadata.get("timestamp", ""),
                        "datetime": metadata.get("datetime", ""),
                        "committed": metadata.get("committed", False),
                        "commit_message": metadata.get("commit_message", ""),
                        "original_file": metadata.get("original_file", "")
                    })
        backups.sort(key=lambda x: x.get("datetime", ""), reverse=True)
        return {
            "status": "success",
            "backups": backups,
            "total_backups": len(backups)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def commit_changes(filepath: str, commit_message: str = "") -> dict:
    try:
        full_path = _resolve_path(filepath)
        backups_dir = _require_workspace() / _BACKUP_DIRNAME
        if not backups_dir.exists():
            return {"status": "error", "message": "No backups directory found"}
        backup_files = [b for b in backups_dir.glob(f"{full_path.stem}_*{full_path.suffix}") if b.suffix == full_path.suffix]
        if not backup_files:
            return {"status": "error", "message": "No backups found for this file"}
        backup_files.sort(key=lambda x: x.name, reverse=True)
        latest_backup = backup_files[0]
        metadata_file = backups_dir / f"{latest_backup.name}.json"
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            metadata["committed"] = True
            metadata["commit_message"] = commit_message
            metadata["commit_timestamp"] = datetime.now().isoformat()
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            return {
                "status": "success",
                "filepath": str(full_path),
                "backup_file": str(latest_backup),
                "committed": True,
                "commit_message": commit_message,
                "message": "Changes committed successfully"
            }
        else:
            return {"status": "error", "message": "Backup metadata not found"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Diff & Compare ---
def compare_versions(filepath: str, backup_timestamp: str = None) -> dict:
    try:
        full_path = _resolve_path(filepath)
        backups_dir = _require_workspace() / _BACKUP_DIRNAME
        if not full_path.exists():
            return {"status": "error", "message": "Current file does not exist"}
        if not backups_dir.exists():
            return {"status": "error", "message": "No backups directory found"}
        backup_files = [b for b in backups_dir.glob(f"{full_path.stem}_*{full_path.suffix}") if b.suffix == full_path.suffix]
        if not backup_files:
            return {"status": "error", "message": "No backups found for this file"}
        backup_files.sort(key=lambda x: x.name, reverse=True)
        if backup_timestamp:
            target_backup = None
            for backup_file in backup_files:
                if backup_timestamp in backup_file.name:
                    target_backup = backup_file
                    break
            if not target_backup:
                return {"status": "error", "message": f"Backup with timestamp {backup_timestamp} not found"}
        else:
            target_backup = backup_files[0]
        with open(full_path, 'r', encoding='utf-8') as f:
            current_content = f.read()
        with open(target_backup, 'r', encoding='utf-8') as f:
            backup_content = f.read()
        lines1 = current_content.splitlines(keepends=True)
        lines2 = backup_content.splitlines(keepends=True)
        diff = list(difflib.unified_diff(
            lines2, lines1,
            fromfile=f"backup/{full_path.name}",
            tofile=f"current/{full_path.name}",
            lineterm=""
        ))
        diff_text = "\n".join(diff)
        return {
            "status": "success",
            "filepath": str(full_path),
            "backup_file": str(target_backup),
            "diff": diff_text,
            "lines_changed": len(diff),
            "current_size": len(current_content),
            "backup_size": len(backup_content),
            "has_changes": current_content != backup_content
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

def generate_diff(text1: str, text2: str, filename: str = "file.txt") -> dict:
    try:
        lines1 = text1.splitlines(keepends=True)
        lines2 = text2.splitlines(keepends=True)
        diff = list(difflib.unified_diff(
            lines1, lines2,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
            lineterm=""
        ))
        diff_text = "\n".join(diff)
        return {"status": "success", "diff": diff_text}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Formatting ---
def format_code(filepath: str) -> dict:
    try:
        full_path = _resolve_path(filepath)
        result = subprocess.run(["black", str(full_path)], capture_output=True, text=True)
        if result.returncode == 0:
            return {"status": "success", "message": result.stdout}
        else:
            return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def list_path(path: str = '.') -> dict:
    """
    List files and directories at a given path (non-recursive).
    Returns a dict with status, entries (list of dicts: name, is_dir, size, mtime), and error/message if any.
    """
    try:
        dir_path = _resolve_path(path)
        if not dir_path.exists() or not dir_path.is_dir():
            return {"status": "error", "message": f"Path '{path}' does not exist or is not a directory"}
        entries = []
        for entry in dir_path.iterdir():
            entries.append({
                "name": entry.name,
                "is_dir": entry.is_dir(),
                "size": entry.stat().st_size if entry.is_file() else None,
                "mtime": entry.stat().st_mtime
            })
        return {"status": "success", "entries": entries}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def list_path_recursive(path: str = '.') -> dict:
    """
    List all files and directories under a given path, recursively.
    Returns a dict with status, entries (list of dicts: path, is_dir, size, mtime), and error/message if any.
    """
    try:
        dir_path = _resolve_path(path)
        if not dir_path.exists() or not dir_path.is_dir():
            return {"status": "error", "message": f"Path '{path}' does not exist or is not a directory"}
        entries = []
        for root, dirs, files in os.walk(dir_path):
            for d in dirs:
                entry_path = Path(root) / d
                entries.append({
                    "path": str(entry_path.relative_to(dir_path)),
                    "is_dir": True,
                    "size": None,
                    "mtime": entry_path.stat().st_mtime
                })
            for f in files:
                entry_path = Path(root) / f
                entries.append({
                    "path": str(entry_path.relative_to(dir_path)),
                    "is_dir": False,
                    "size": entry_path.stat().st_size,
                    "mtime": entry_path.stat().st_mtime
                })
        return {"status": "success", "entries": entries}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_head(filepath: str, n: int = 10) -> dict:
    """
    Return the first n lines of a file.
    Returns a dict with status, lines (list of str), and error/message if any.
    """
    try:
        file_path = _resolve_path(filepath)
        if not file_path.exists() or not file_path.is_file():
            return {"status": "error", "message": f"File '{filepath}' does not exist"}
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [next(f) for _ in range(n)]
        return {"status": "success", "lines": lines}
    except StopIteration:
        return {"status": "success", "lines": lines}  # Fewer than n lines
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_tail(filepath: str, n: int = 10) -> dict:
    """
    Return the last n lines of a file.
    Returns a dict with status, lines (list of str), and error/message if any.
    """
    try:
        file_path = _resolve_path(filepath)
        if not file_path.exists() or not file_path.is_file():
            return {"status": "error", "message": f"File '{filepath}' does not exist"}
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return {"status": "success", "lines": lines[-n:]}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def get_lines(filepath: str, start: int, end: int) -> dict:
    """
    Return lines from start to end (inclusive, 1-based) of a file.
    Returns a dict with status, lines (list of str), and error/message if any.
    """
    try:
        file_path = _resolve_path(filepath)
        if not file_path.exists() or not file_path.is_file():
            return {"status": "error", "message": f"File '{filepath}' does not exist"}
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        # Adjust for 1-based indexing
        if start < 1 or end < start or end > len(lines):
            return {"status": "error", "message": f"Invalid start/end: file has {len(lines)} lines"}
        return {"status": "success", "lines": lines[start-1:end]}
    except Exception as e:
        return {"status": "error", "message": str(e)} 