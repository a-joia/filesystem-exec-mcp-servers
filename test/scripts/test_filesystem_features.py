import os
import shutil
import pytest
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from tools.filesystem import set_workspace, get_workspace, edit_file, backup_file, restore_file, list_backups, commit_changes, compare_versions, format_code, generate_diff

def cleanup(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

def test_backup_and_restore():
    ws = 'test_features_backup'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'b.txt'
    content1 = 'foo\nbar\n'
    content2 = 'baz\nqux\n'
    edit_file(fname, content=content1)
    b1 = backup_file(fname)
    assert b1['status'] == 'success'
    edit_file(fname, content=content2)
    b2 = backup_file(fname)
    assert b2['status'] == 'success'
    # List backups
    blist = list_backups(fname)
    assert blist['status'] == 'success'
    assert blist['total_backups'] >= 2
    # Restore first backup
    ts = blist['backups'][-1]['timestamp']
    r = restore_file(fname, backup_timestamp=ts)
    assert r['status'] == 'success'
    with open(os.path.join(ws_path, fname)) as f:
        assert f.read() == content1
    # Edge: restore with invalid timestamp
    r2 = restore_file(fname, backup_timestamp='not_a_ts')
    assert r2['status'] == 'error'
    # Edge: backup non-existent file
    err = backup_file('nope.txt')
    assert err['status'] == 'error'
    cleanup(os.path.join('.workspace', ws))

def test_commit_and_list_backups():
    ws = 'test_features_commit'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'c.txt'
    edit_file(fname, content='abc\ndef\n')
    b = backup_file(fname)
    assert b['status'] == 'success'
    c = commit_changes(fname, commit_message='my commit')
    assert c['status'] == 'success'
    blist = list_backups(fname)
    assert blist['status'] == 'success'
    found = False
    for b in blist['backups']:
        if b.get('committed'):
            found = True
            assert b.get('commit_message') == 'my commit'
    assert found
    # Edge: commit with no backups
    fname2 = 'empty.txt'
    edit_file(fname2, content='')
    err = commit_changes(fname2)
    assert err['status'] == 'error'
    cleanup(os.path.join('.workspace', ws))

def test_compare_versions():
    ws = 'test_features_compare'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'cmp.txt'
    edit_file(fname, content='a\nb\nc\n')
    b1 = backup_file(fname)
    edit_file(fname, content='a\nB\nc\n')
    b2 = backup_file(fname)
    # Compare current to first backup
    blist = list_backups(fname)
    ts = blist['backups'][-1]['timestamp']
    cmp = compare_versions(fname, backup_timestamp=ts)
    assert cmp['status'] == 'success'
    assert 'diff' in cmp and '-b' in cmp['diff']
    # Edge: compare with invalid timestamp
    err = compare_versions(fname, backup_timestamp='not_a_ts')
    assert err['status'] == 'error'
    cleanup(os.path.join('.workspace', ws))

def test_format_code():
    ws = 'test_features_format'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'fmt.py'
    code = 'def foo():\n  return 1\n'
    edit_file(fname, content=code)
    fmt = format_code(fname)
    assert fmt['status'] in ('success', 'error')  # success if black is installed
    # Edge: format non-Python file
    fname2 = 'notpy.txt'
    edit_file(fname2, content='just text')
    fmt2 = format_code(fname2)
    assert fmt2['status'] == 'error' or 'error' in fmt2.get('message', '').lower()
    cleanup(os.path.join('.workspace', ws))

def test_generate_diff():
    t1 = 'a\nb\nc\n'
    t2 = 'a\nB\nc\n'
    diff = generate_diff(t1, t2, filename='foo.txt')
    assert diff['status'] == 'success'
    assert '-b' in diff['diff'] or '+B' in diff['diff']
    # Edge: invalid input (empty strings)
    diff2 = generate_diff('', '', filename='foo.txt')
    assert diff2['status'] == 'success'

def test_backup_restore_nested_dirs():
    ws = 'test_features_nested'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    nested = os.path.join('a', 'b', 'c', 'deep.txt')
    os.makedirs(os.path.join(ws_path, 'a', 'b', 'c'), exist_ok=True)
    content = 'deep\nfile\ncontent\n'
    edit_file(nested, content=content)
    b = backup_file(nested)
    assert b['status'] == 'success'
    edit_file(nested, content='changed\n')
    r = restore_file(nested)
    assert r['status'] == 'success'
    with open(os.path.join(ws_path, nested)) as f:
        assert f.read() == content
    cleanup(os.path.join('.workspace', ws))

def test_large_file_backup_restore_commit():
    ws = 'test_features_largefile'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'large.txt'
    big = 'x' * 10**6 + '\n'  # 1MB file
    edit_file(fname, content=big)
    b = backup_file(fname)
    assert b['status'] == 'success'
    edit_file(fname, content='y' * 10**6 + '\n')
    b2 = backup_file(fname)
    assert b2['status'] == 'success'
    c = commit_changes(fname, commit_message='big commit')
    assert c['status'] == 'success'
    # Restore using the first backup's timestamp
    blist = list_backups(fname)
    ts = blist['backups'][-1]['timestamp']
    r = restore_file(fname, backup_timestamp=ts)
    assert r['status'] == 'success'
    with open(os.path.join(ws_path, fname)) as f:
        assert f.read() == 'x' * 10**6 + '\n'
    cleanup(os.path.join('.workspace', ws))

def test_list_backups_no_backups():
    ws = 'test_features_nobackups'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    blist = list_backups('nope.txt')
    assert blist['status'] == 'success'
    assert blist['total_backups'] == 0
    cleanup(os.path.join('.workspace', ws))

def test_format_code_syntax_error():
    ws = 'test_features_formaterr'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    fname = 'bad.py'
    code = 'def foo(:\n  return 1\n'  # Syntax error
    edit_file(fname, content=code)
    fmt = format_code(fname)
    assert fmt['status'] == 'error' or 'error' in fmt.get('message', '').lower()
    cleanup(os.path.join('.workspace', ws))

def test_generate_diff_large():
    t1 = 'a' * 10000 + '\n' + 'b' * 10000 + '\n'
    t2 = 'a' * 10000 + '\n' + 'B' * 10000 + '\n'
    diff = generate_diff(t1, t2, filename='big.txt')
    assert diff['status'] == 'success'
    assert '-b' in diff['diff'] or '+B' in diff['diff']

def test_workspace_containment():
    ws = 'test_features_containment'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    # Try to backup a file outside workspace
    try:
        backup_file('../outside.txt')
        assert False, 'Should not allow backup outside workspace'
    except PermissionError:
        pass
    except Exception as e:
        print(f"backup_file raised {type(e).__name__}: {e}")
        assert False, f"Expected PermissionError, got {type(e).__name__}: {e}"
    # Try to restore a file outside workspace
    try:
        restore_file('../outside.txt')
        assert False, 'Should not allow restore outside workspace'
    except PermissionError:
        pass
    except Exception as e:
        print(f"restore_file raised {type(e).__name__}: {e}")
        assert False, f"Expected PermissionError, got {type(e).__name__}: {e}"
    # Try to edit a file outside workspace
    try:
        edit_file('../outside.txt', content='bad')
        assert False, 'Should not allow edit outside workspace'
    except PermissionError:
        pass
    except Exception as e:
        print(f"edit_file raised {type(e).__name__}: {e}")
        assert False, f"Expected PermissionError, got {type(e).__name__}: {e}"
    cleanup(os.path.join('.workspace', ws)) 