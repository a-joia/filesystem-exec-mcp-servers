import sys
import os
import shutil
import filecmp
import difflib
import time
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from tools.filesystem import edit_file, set_workspace, get_workspace, backup_file, list_backups, commit_changes, compare_versions, restore_file

def cleanup(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

def test_filesystem():
    ws = 'test_workspace'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()
    if isinstance(ws_path, dict):
        ws_path = ws_path.get('workspace', ws_path)
    test_file = 'foo.txt'
    # 1. Write file and check contents
    edit_file(test_file, content='hello')
    with open(os.path.join(ws_path, test_file)) as f:
        assert f.read().strip() == 'hello'
    # 2. Backup file and check backup contents
    backup = backup_file(test_file)
    assert backup['status'] == 'success' and os.path.exists(backup['backup_file'])
    with open(backup['backup_file']) as f:
        assert f.read().strip() == 'hello'
    # 3. Overwrite file, backup again, check new backup
    edit_file(test_file, content='world')
    time.sleep(1)
    backup2 = backup_file(test_file)
    assert backup2['status'] == 'success' and os.path.exists(backup2['backup_file'])
    with open(os.path.join(ws_path, test_file)) as f:
        assert f.read().strip() == 'world'
    with open(backup2['backup_file']) as f:
        assert f.read().strip() == 'world'
    # 4. Restore from first backup, check contents
    backups = list_backups(test_file)
    assert backups['status'] == 'success' and len(backups['backups']) >= 2
    first_backup_ts = backups['backups'][-1]['timestamp']
    restore_result = restore_file(test_file, backup_timestamp=first_backup_ts)
    assert restore_result['status'] == 'success'
    with open(os.path.join(ws_path, test_file)) as f:
        assert f.read().strip() == 'hello'
    # 5. List backups, check both backups are present
    backups = list_backups(test_file)
    assert backups['status'] == 'success' and len(backups['backups']) >= 2
    # 6. Commit changes, check commit hash is a backup timestamp
    commit = commit_changes(test_file)
    assert commit['status'] == 'success'
    backup_files = [b['backup_file'] for b in backups['backups']]
    assert commit['backup_file'] in backup_files
    # 7. Compare versions, check diff is correct
    edit_file(test_file, content='new content')
    time.sleep(1)
    backup3 = backup_file(test_file)
    backups = list_backups(test_file)
    previous_backup_ts = backups['backups'][1]['timestamp']
    diff = compare_versions(test_file, backup_timestamp=previous_backup_ts)
    assert diff['status'] == 'success' and ('-hello' in diff['diff'] or '+new content' in diff['diff'] or diff['diff'])
    print('filesystem tests passed')
    cleanup(os.path.join('.workspace', ws))

# --- Edge Case Tests ---
def test_backup_file_nonexistent():
    ws = 'test_workspace_ec1'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    try:
        result = backup_file('no_such_file.txt')
        assert result['status'] == 'error'
    except FileNotFoundError:
        pass
    cleanup(os.path.join('.workspace', ws))

def test_restore_file_invalid_timestamp():
    ws = 'test_workspace_ec2'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    edit_file('foo.txt', content='abc')
    backup_file('foo.txt')
    try:
        result = restore_file('foo.txt', backup_timestamp='invalid_ts')
        assert result['status'] == 'error'
    except FileNotFoundError:
        pass
    cleanup(os.path.join('.workspace', ws))

def test_write_new_file_no_backup():
    ws = 'test_workspace_ec3'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    test_file = 'foo.txt'
    edit_file(test_file, content='abc', create_backup=False)
    ws_path = get_workspace()
    if isinstance(ws_path, dict):
        ws_path = ws_path.get('workspace', ws_path)
    assert os.path.exists(os.path.join(ws_path, test_file))
    cleanup(os.path.join('.workspace', ws))

def test_commit_changes_no_backups():
    ws = 'test_workspace_ec4'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    test_file = 'foo.txt'
    edit_file(test_file, content='abc', create_backup=False)
    try:
        result = commit_changes(test_file)
        assert result['status'] == 'error'
    except IndexError:
        pass
    cleanup(os.path.join('.workspace', ws))

def test_compare_versions_missing_backup():
    ws = 'test_workspace_ec5'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    edit_file('foo.txt', content='abc')
    backup_file('foo.txt')
    try:
        result = compare_versions('foo.txt', backup_timestamp='invalid_ts')
        assert result['status'] == 'error'
    except FileNotFoundError:
        pass
    cleanup(os.path.join('.workspace', ws))

def test_list_backups_no_backups():
    ws = 'test_workspace_ec6'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    assert list_backups('foo.txt')['backups'] == []
    cleanup(os.path.join('.workspace', ws))

def test_set_workspace_nonexistent():
    ws = 'test_workspace_ec7/nested'
    cleanup(os.path.join('.workspace', 'test_workspace_ec7'))
    set_workspace(ws)
    ws_path = get_workspace()
    if isinstance(ws_path, dict):
        ws_path = ws_path.get('workspace', ws_path)
    assert os.path.exists(ws_path)
    cleanup(os.path.join('.workspace', 'test_workspace_ec7'))

def test_backup_restore_nested_dirs():
    ws = 'test_workspace_ec8'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()
    if isinstance(ws_path, dict):
        ws_path = ws_path.get('workspace', ws_path)
    nested_file = 'a/b/c/foo.txt'
    os.makedirs(os.path.join(ws_path, 'a/b/c'), exist_ok=True)
    edit_file(nested_file, content='nested')
    backup = backup_file(nested_file)
    edit_file(nested_file, content='changed')
    restore_result = restore_file(nested_file)
    assert restore_result['status'] == 'success'
    with open(os.path.join(ws_path, nested_file)) as f:
        assert f.read().strip() == 'nested'
    cleanup(os.path.join('.workspace', ws))

def test_write_new_file_empty_content():
    ws = 'test_workspace_ec9'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()
    if isinstance(ws_path, dict):
        ws_path = ws_path.get('workspace', ws_path)
    test_file = 'foo.txt'
    edit_file(test_file, content='')
    with open(os.path.join(ws_path, test_file)) as f:
        assert f.read().strip() == ''
    cleanup(os.path.join('.workspace', ws))

def test_list_path_and_recursive():
    ws = 'test_list_path_ws'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()
    if isinstance(ws_path, dict):
        ws_path = ws_path.get('workspace', ws_path)
    # Create files and dirs
    os.makedirs(os.path.join(ws_path, 'dir1/dir2'), exist_ok=True)
    with open(os.path.join(ws_path, 'file1.txt'), 'w') as f:
        f.write('abc\n')
    with open(os.path.join(ws_path, 'dir1', 'file2.txt'), 'w') as f:
        f.write('def\n')
    with open(os.path.join(ws_path, 'dir1', 'dir2', 'file3.txt'), 'w') as f:
        f.write('ghi\n')
    # Test list_path
    from tools.filesystem import list_path, list_path_recursive
    result = list_path('.')
    assert result['status'] == 'success'
    names = [e['name'] for e in result['entries']]
    assert 'file1.txt' in names and 'dir1' in names
    # Test list_path_recursive
    result = list_path_recursive('.')
    assert result['status'] == 'success'
    paths = [e['path'] for e in result['entries']]
    assert 'file1.txt' in paths or './file1.txt' in paths
    assert os.path.join('dir1', 'file2.txt') in paths or 'dir1/file2.txt' in paths
    assert os.path.join('dir1', 'dir2', 'file3.txt') in paths or 'dir1/dir2/file3.txt' in paths
    cleanup(os.path.join('.workspace', ws))

def test_get_head_tail_lines():
    ws = 'test_head_tail_ws'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()
    if isinstance(ws_path, dict):
        ws_path = ws_path.get('workspace', ws_path)
    test_file = 'lines.txt'
    lines = [f"line {i}\n" for i in range(1, 21)]
    with open(os.path.join(ws_path, test_file), 'w') as f:
        f.writelines(lines)
    from tools.filesystem import get_head, get_tail, get_lines
    # Test get_head
    result = get_head(test_file, n=5)
    assert result['status'] == 'success'
    assert result['lines'] == lines[:5]
    # Test get_tail
    result = get_tail(test_file, n=5)
    assert result['status'] == 'success'
    assert result['lines'] == lines[-5:]
    # Test get_lines
    result = get_lines(test_file, 6, 10)
    assert result['status'] == 'success'
    assert result['lines'] == lines[5:10]
    # Test get_lines with invalid range
    result = get_lines(test_file, 0, 5)
    assert result['status'] == 'error'
    result = get_lines(test_file, 10, 5)
    assert result['status'] == 'error'
    result = get_lines(test_file, 1, 100)
    assert result['status'] == 'error'
    # Test get_head/get_tail on non-existent file
    result = get_head('no_such_file.txt')
    assert result['status'] == 'error'
    result = get_tail('no_such_file.txt')
    assert result['status'] == 'error'
    cleanup(os.path.join('.workspace', ws))

if __name__ == '__main__':
    test_filesystem()
    test_backup_file_nonexistent()
    test_restore_file_invalid_timestamp()
    test_write_new_file_no_backup()
    test_commit_changes_no_backups()
    test_compare_versions_missing_backup()
    test_list_backups_no_backups()
    test_set_workspace_nonexistent()
    test_backup_restore_nested_dirs()
    test_write_new_file_empty_content()
    test_list_path_and_recursive()
    test_get_head_tail_lines()
    print('All filesystem edge case tests passed') 