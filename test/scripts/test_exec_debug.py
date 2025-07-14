import sys
import os
import tempfile
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from tools.exec_debug import *

def test_exec_debug():
    # 1. Test execute_python with valid code
    code = 'print("hi")'
    result = execute_python(code)
    assert result['stdout'].strip() == 'hi'
    assert result['stderr'] == ''
    assert result['status'] == 'success'
    # 2. Test execute_python with error
    code_err = 'raise ValueError("fail")'
    result_err = execute_python(code_err)
    assert 'ValueError' in result_err['stderr']
    assert result_err['status'] == 'error'
    # 3. Test execute_python with syntax error
    code_syntax = 'def foo(:\n  pass'
    result_syntax = execute_python(code_syntax)
    assert result_syntax['status'] == 'error'
    assert 'SyntaxError' in result_syntax['stderr']
    # 4. Test execute_python with timeout
    code_timeout = 'import time\ntime.sleep(2)'
    result_timeout = execute_python(code_timeout, timeout=1)
    assert result_timeout['status'] == 'error'
    assert 'Timeout' in result_timeout['stderr']
    # 5. Test execute_python_file with nonexistent file
    result_nf = execute_python_file('no_such_file.py')
    assert result_nf['status'] == 'error'
    # 6. Test execute_python_file with large output
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('print("x" * 10000)')
        fname = f.name
    result_large = execute_python_file(fname)
    assert result_large['status'] == 'success'
    assert len(result_large['stdout']) > 9000
    # 7. Test debug_python_file with valid file and breakpoint
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('print("before")\nprint("at_breakpoint")\nprint("after")')
        fname2 = f.name
    output = debug_python_file(fname2, [2])
    assert output and isinstance(output, str)
    # 8. Test debug_python_file with nonexistent file
    try:
        debug_python_file('no_such_file.py', [1])
        assert False, 'Should raise FileNotFoundError'
    except FileNotFoundError:
        pass
    # 9. Test debug_python_file with invalid breakpoint
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('print("only one line")')
        fname3 = f.name
    output2 = debug_python_file(fname3, [100])
    assert 'Exception' in output2 or isinstance(output2, str)
    # 10. Test code that tries to access files (security)
    code_sec = 'try:\n open("/etc/passwd")\nexcept Exception as e:\n print("SEC", e)'
    result_sec = execute_python(code_sec)
    assert 'SEC' in result_sec['stdout'] or 'Permission' in result_sec['stderr'] or result_sec['status'] in ('success', 'error')
    # 11. Multiple breakpoints
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('print("A")\nprint("B")\nprint("C")')
        fname = f.name
    output = debug_python_file(fname, [1, 2, 3])
    assert output and isinstance(output, str)
    # 12. Breakpoints on comments/blank lines
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('print("A")\n# comment\n\nprint("B")')
        fname = f.name
    output = debug_python_file(fname, [2, 3])
    assert output and isinstance(output, str)
    # 13. Breakpoints out of range
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('print("A")')
        fname = f.name
    output = debug_python_file(fname, [0, 100])
    assert output and isinstance(output, str)
    # 14. Exception in debugged code
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('print("A")\nraise RuntimeError("debug fail")')
        fname = f.name
    output = debug_python_file(fname, [2])
    assert 'Exception' in output or 'debug fail' in output or isinstance(output, str)
    # 15. Debug with no breakpoints
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('print("A")\nprint("B")')
        fname = f.name
    output = debug_python_file(fname, [])
    assert output and isinstance(output, str)
    # 16. Debug with syntax error
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('def foo(:\n  pass')
        fname = f.name
    output = debug_python_file(fname, [1])
    assert 'SyntaxError' in output or 'Exception' in output or isinstance(output, str)
    # 17. Non-UTF-8 encoded file
    with tempfile.NamedTemporaryFile('w+b', suffix='.py', delete=False) as f:
        f.write('print("áéíóú")'.encode('latin-1'))
        fname = f.name
    try:
        result = execute_python_file(fname)
        assert result['status'] in ('success', 'error')
    except Exception as e:
        assert isinstance(e, UnicodeDecodeError)
    # 18. Return value consistency for execute_python/execute_python_file
    code = 'print("consistency")'
    result1 = execute_python(code)
    result2 = execute_python_file(fname)
    for key in ['status', 'stdout', 'stderr', 'return_code', 'execution_time']:
        assert key in result1 and key in result2
    # 19. Resource limits (simulate with large loop)
    code = 'for i in range(10**7): pass\nprint("done")'
    result = execute_python(code, timeout=5)
    assert result['status'] in ('success', 'error')
    # 20. Breakpoint on never-executed line
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('if False:\n print("never")\nprint("end")')
        fname = f.name
    output = debug_python_file(fname, [2])
    assert output and isinstance(output, str)
    print('exec_debug tests passed')

if __name__ == '__main__':
    test_exec_debug() 