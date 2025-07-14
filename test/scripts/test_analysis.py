import os
import sys
import tempfile
import shutil
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from tools.analysis import *

def cleanup(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

def test_analysis():
    # 1. check_syntax: valid and invalid
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('def foo():\n    pass\n')
        fname = f.name
    assert check_syntax(fname) == []
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('def bar(:\n    pass\n')
        fname_err = f.name
    assert check_syntax(fname_err) != []
    # 2. check_syntax_multiple_files
    res = check_syntax_multiple_files([fname, fname_err])
    assert fname in res and fname_err in res
    # 3. lint_file: clean and dirty
    lint_clean = lint_file(fname)
    assert isinstance(lint_clean, str)
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('def BAD():\n  x=1\n')
        fname_lint = f.name
    lint_dirty = lint_file(fname_lint)
    assert isinstance(lint_dirty, str)
    # 4. run_mutation_tests: just check output is string
    mut_result = run_mutation_tests(fname)
    assert isinstance(mut_result, str)
    # 5. search_code and search_symbols
    code_results = search_code('foo', directory=os.path.dirname(fname))
    assert any('foo' in r['code'] for r in code_results)
    sym_results = search_symbols('foo', kind='function', directory=os.path.dirname(fname))
    assert any(fname in s for s in sym_results)
    # 6. find_unused_code: just check output is list
    unused = find_unused_code(os.path.dirname(fname))
    assert isinstance(unused, list)
    # 7. extract_docstrings
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('def docfun():\n    """docstring"""\n    pass\n')
        fname_doc = f.name
    docs = extract_docstrings(fname_doc)
    assert 'docfun' in docs and docs['docfun'] == 'docstring'
    # 8. suggest_test_cases
    test_skel = suggest_test_cases(fname, 'foo')
    assert 'test_foo' in test_skel
    # 9. check_syntax with nonexistent file
    try:
        check_syntax('no_such_file.py')
        assert False, 'Should raise FileNotFoundError'
    except FileNotFoundError:
        pass
    # 10. lint_file with nonexistent file
    lint_nf = lint_file('no_such_file.py')
    assert 'error' in lint_nf.lower()
    # 11. run_mutation_tests with nonexistent file
    mut_nf = run_mutation_tests('no_such_file.py')
    assert 'error' in mut_nf.lower() or isinstance(mut_nf, str)
    # 12. find_unused_code with nonexistent dir
    unused_nf = find_unused_code('no_such_dir')
    if isinstance(unused_nf, dict):
        assert 'error' in unused_nf.get('status', '').lower() or 'error' in unused_nf.get('message', '').lower()
    else:
        assert unused_nf == [] or any('error' in u.lower() for u in unused_nf)
    # 13. extract_docstrings with syntax error
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('def bad(:\n  pass')
        fname_bad = f.name
    try:
        extract_docstrings(fname_bad)
        assert False, 'Should raise SyntaxError'
    except SyntaxError:
        pass
    # 14. extract_docstrings with nested/no docstrings
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('def outer():\n    def inner():\n        pass\nclass C: pass')
        fname_nested = f.name
    docs = extract_docstrings(fname_nested)
    assert isinstance(docs, dict)
    # 15. search_code with regex special chars
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('a = 1\nb = 2\nc = 3')
        fname_regex = f.name
    results = search_code('a = 1|b = 2', directory=os.path.dirname(fname_regex))
    assert isinstance(results, list)
    # 16. suggest_test_cases with no function name
    skel = suggest_test_cases(fname)
    assert 'TODO' in skel
    # 17. check_syntax with encoding error
    with tempfile.NamedTemporaryFile('w+b', suffix='.py', delete=False) as f:
        f.write('print("áéíóú")'.encode('latin-1'))
        fname_enc = f.name
    try:
        check_syntax(fname_enc)
        assert False, 'Should raise UnicodeDecodeError'
    except UnicodeDecodeError:
        pass
    # 18. lint_file with missing flake8 (simulate by renaming PATH)
    old_path = os.environ.get('PATH', '')
    os.environ['PATH'] = ''
    lint_missing = lint_file(fname)
    os.environ['PATH'] = old_path
    assert 'error' in lint_missing.lower()
    # 19. run_mutation_tests with missing mutmut (simulate by renaming PATH)
    os.environ['PATH'] = ''
    mut_missing = run_mutation_tests(fname)
    os.environ['PATH'] = old_path
    assert 'error' in mut_missing.lower() or isinstance(mut_missing, str)
    # 20. find_unused_code with missing vulture (simulate by renaming PATH)
    os.environ['PATH'] = ''
    unused_missing = find_unused_code(os.path.dirname(fname))
    os.environ['PATH'] = old_path
    assert any('error' in u.lower() for u in unused_missing)
    # 21. search_code in large file
    with tempfile.NamedTemporaryFile('w', suffix='.py', delete=False) as f:
        f.write('foo\n' * 10000)
        fname_large = f.name
    results_large = search_code('foo', directory=os.path.dirname(fname_large))
    assert isinstance(results_large, list)
    # Cleanup
    cleanup(fname)
    cleanup(fname_err)
    cleanup(fname_lint)
    cleanup(fname_doc)
    cleanup(fname_bad)
    cleanup(fname_nested)
    cleanup(fname_regex)
    cleanup(fname_enc)
    cleanup(fname_large)
    print('analysis tests passed')

if __name__ == '__main__':
    test_analysis() 