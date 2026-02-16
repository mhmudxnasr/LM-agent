from pathlib import Path

from lm_agent.core.shell import run_command, run_python


def test_run_command_echo(tmp_path: Path) -> None:
    result = run_command(command="Write-Output hello", cwd=str(tmp_path))
    assert result["ok"] is True
    assert "hello" in result["stdout"].lower()


def test_run_python_snippet(tmp_path: Path) -> None:
    result = run_python(code="print('fib')", cwd=str(tmp_path))
    assert result["ok"] is True
    assert "fib" in result["stdout"]
