from pathlib import Path

from tools.filesystem import delete_file, edit_file, find_files, read_file, write_file


def test_write_read_edit_delete(tmp_path: Path) -> None:
    cwd = str(tmp_path)
    target = "sample.txt"

    write_result = write_file(path=target, content="hello world", cwd=cwd)
    assert write_result["bytes_written"] > 0

    read_result = read_file(path=target, cwd=cwd)
    assert read_result["content"] == "hello world"

    edit_result = edit_file(path=target, search="world", replace="agent", cwd=cwd)
    assert edit_result["occurrences_replaced"] == 1

    read_result = read_file(path=target, cwd=cwd)
    assert read_result["content"] == "hello agent"

    find_result = find_files(pattern="*.txt", root=".", cwd=cwd)
    assert any(item.endswith("sample.txt") for item in find_result["matches"])

    delete_result = delete_file(path=target, cwd=cwd)
    assert delete_result["deleted"] == "file"
