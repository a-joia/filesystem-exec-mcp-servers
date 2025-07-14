"""
Code Execution & Debugging Tools
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

def execute_python(code: str, *, timeout: int = 30) -> Dict[str, Any]:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tmp:
        tmp.write(code)
        tmp_path = Path(tmp.name)
    return execute_python_file(str(tmp_path), timeout=timeout)

def execute_python_file(file: str, *, timeout: int = 30) -> Dict[str, Any]:
    try:
        completed = subprocess.run([
            "python", str(file)
        ], capture_output=True, text=True, timeout=timeout)
        status = "success" if completed.returncode == 0 else "error"
        return {
            "status": status,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "return_code": completed.returncode,
            "execution_time": "completed"
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "status": "error",
            "stdout": "",
            "stderr": f"Timeout (>{timeout}s) — {exc}",
            "return_code": None,
            "execution_time": "timeout"
        }

def debug_python_file(file: str, breakpoints: List[int], *, timeout: int = 60) -> str:
    """Run *file* under pdb, setting breakpoints at the given line numbers. Returns the captured pdb session transcript as a string."""
    import sys
    import io
    import pdb
    import runpy
    from contextlib import redirect_stdout, redirect_stderr
    from pathlib import Path

    # Explicitly check file existence
    if not Path(file).exists():
        raise FileNotFoundError(f"File not found: {file}")

    # Prepare a custom Pdb subclass to set breakpoints
    class CustomPdb(pdb.Pdb):
        def __init__(self, breakpoints, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.breakpoints = breakpoints
        def user_line(self, frame):
            lineno = frame.f_lineno
            if lineno in self.breakpoints:
                self.set_break(frame.f_code.co_filename, lineno)
            super().user_line(frame)

    f = io.StringIO()
    with redirect_stdout(f), redirect_stderr(f):
        debugger = CustomPdb(breakpoints)
        try:
            debugger.run(f'exec(open("{file}").read(), {{"__name__": "__main__"}})')
        except FileNotFoundError:
            raise
        except Exception as e:
            print(f"Exception: {e}")
    return f.getvalue() 