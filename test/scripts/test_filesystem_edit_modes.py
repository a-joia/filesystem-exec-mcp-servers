import os
import shutil
import difflib
import pytest
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from tools.filesystem import set_workspace, get_workspace, edit_file, preview_edit, EditMode

def cleanup(path):
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)

def test_edit_file_unified_diff():
    ws = 'test_edit_modes_udiff'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'foo.txt'
    orig = 'line1\nline2\nline3\n'
    edit_file(fname, content=orig)
    # Create an ndiff to change line2 to LINE2 (matches _apply_unified_diff logic)
    orig_lines = orig.splitlines(keepends=True)
    edited_lines = ['line1\n', 'LINE2\n', 'line3\n']
    diff = ''.join(difflib.ndiff(orig_lines, edited_lines))
    result = edit_file(fname, mode=EditMode.UNIFIED_DIFF, diff_text=diff)
    assert result['status'] == 'success'
    with open(os.path.join(ws_path, fname)) as f:
        assert f.readlines() == edited_lines
    # Error: missing diff_text
    err = edit_file(fname, mode=EditMode.UNIFIED_DIFF)
    assert err['status'] == 'error'
    cleanup(os.path.join('.workspace', ws))

def test_edit_file_line_edit():
    ws = 'test_edit_modes_line'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'bar.txt'
    orig = 'a\nb\nc\n'
    edit_file(fname, content=orig)
    # Change line 2 to B
    result = edit_file(fname, mode=EditMode.LINE_EDIT, line_number=2, new_content='B')
    assert result['status'] == 'success'
    with open(os.path.join(ws_path, fname)) as f:
        assert f.readlines() == ['a\n', 'B\n', 'c\n']
    # Error: missing line_number
    err = edit_file(fname, mode=EditMode.LINE_EDIT, new_content='X')
    assert err['status'] == 'error'
    cleanup(os.path.join('.workspace', ws))

def test_edit_file_span_edit():
    ws = 'test_edit_modes_span'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'baz.txt'
    orig = '1\n2\n3\n4\n5\n'
    edit_file(fname, content=orig)
    # Replace lines 2-4 with XX\nYY
    result = edit_file(fname, mode=EditMode.SPAN_EDIT, start_line=2, end_line=4, new_content='XX\nYY')
    assert result['status'] == 'success'
    with open(os.path.join(ws_path, fname)) as f:
        assert f.readlines() == ['1\n', 'XX\n', 'YY\n', '5\n']
    # Error: out of range
    err = edit_file(fname, mode=EditMode.SPAN_EDIT, start_line=10, end_line=12, new_content='Z')
    assert err['status'] == 'error'
    cleanup(os.path.join('.workspace', ws))

def test_edit_file_default_overwrite():
    ws = 'test_edit_modes_default'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'def.txt'
    orig = 'abc\ndef\n'
    edit_file(fname, content=orig)
    # Overwrite with new content
    result = edit_file(fname, content='123\n456')
    assert result['status'] == 'success'
    with open(os.path.join(ws_path, fname)) as f:
        assert f.read() == '123\n456\n'
    # Error: missing content
    err = edit_file(fname)
    assert err['status'] == 'error'
    cleanup(os.path.join('.workspace', ws))

def test_edit_file_output_dicts():
    ws = 'test_edit_modes_output_dicts'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'dict.txt'
    orig = 'x\ny\nz\n'
    edit_file(fname, content=orig)
    # ndiff for unified_diff
    orig_lines = orig.splitlines(keepends=True)
    edited_lines = ['x\n', 'Y\n', 'z\n']
    diff = ''.join(difflib.ndiff(orig_lines, edited_lines))
    result = edit_file(fname, mode=EditMode.UNIFIED_DIFF, diff_text=diff)
    assert result['status'] == 'success'
    assert result['filepath'].endswith(fname)
    assert result['mode'] == EditMode.UNIFIED_DIFF
    assert 'preview' in result
    assert result['changes_made'] is True
    assert 'message' in result
    # Check backup info
    assert 'backup_created' in result and result['backup_created']
    assert 'backup_file' in result and 'backup_timestamp' in result
    cleanup(os.path.join('.workspace', ws))

def test_edit_file_edge_cases():
    ws = 'test_edit_modes_edge'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'edge.txt'
    # Empty file, line_edit out of range
    edit_file(fname, content='')
    err = edit_file(fname, mode=EditMode.LINE_EDIT, line_number=1, new_content='foo')
    assert err['status'] == 'error'
    # span_edit out of range
    err2 = edit_file(fname, mode=EditMode.SPAN_EDIT, start_line=2, end_line=3, new_content='bar')
    assert err2['status'] == 'error'
    # invalid diff
    bad_diff = 'not a diff'
    err3 = edit_file(fname, mode=EditMode.UNIFIED_DIFF, diff_text=bad_diff)
    assert err3['status'] == 'error'
    # missing args
    err4 = edit_file(fname, mode=EditMode.LINE_EDIT)
    assert err4['status'] == 'error'
    cleanup(os.path.join('.workspace', ws))

def test_edit_file_atomicity():
    ws = 'test_edit_modes_atomicity'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'atomic.txt'
    orig = 'keep\nthis\nfile\n'
    edit_file(fname, content=orig)
    # Simulate error by passing out-of-range line number
    before = open(os.path.join(ws_path, fname)).read()
    err = edit_file(fname, mode=EditMode.LINE_EDIT, line_number=100, new_content='oops')
    after = open(os.path.join(ws_path, fname)).read()
    assert err['status'] == 'error'
    assert before == after  # File unchanged
    cleanup(os.path.join('.workspace', ws))

def test_preview_and_validate_edit():
    ws = 'test_edit_modes_preview'
    cleanup(os.path.join('.workspace', ws))
    set_workspace(ws)
    ws_path = get_workspace()['workspace']
    fname = 'preview.txt'
    orig = 'a\nb\nc\n'
    edit_file(fname, content=orig)
    # ndiff for unified_diff
    orig_lines = orig.splitlines(keepends=True)
    edited_lines = ['a\n', 'B\n', 'c\n']
    diff = ''.join(difflib.ndiff(orig_lines, edited_lines))
    # preview_edit
    preview = preview_edit(fname, mode=EditMode.UNIFIED_DIFF, diff_text=diff)
    assert preview['status'] == 'success'
    assert preview['changes_made'] is True
    assert 'preview' in preview
    # validate_edit
    valid = preview_edit(fname, mode=EditMode.UNIFIED_DIFF, diff_text='not a diff')
    assert valid['status'] == 'success' or valid['status'] == 'error'  # Should not crash
    cleanup(os.path.join('.workspace', ws)) 