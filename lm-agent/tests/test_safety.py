from lm_agent.safety import SafetyManager


def test_blocked_command_detection() -> None:
    safety = SafetyManager(yolo=False)
    blocked, reason = safety.is_blocked_command("format C:")
    assert blocked is True
    assert reason is not None


def test_confirmation_prompt_decline(monkeypatch) -> None:
    safety = SafetyManager(yolo=False)
    monkeypatch.setattr("builtins.input", lambda _: "n")
    approved = safety.confirm_execution("write_file", {"path": "a.txt", "content": "hello"})
    assert approved is False


def test_confirmation_prompt_accept(monkeypatch) -> None:
    safety = SafetyManager(yolo=False)
    monkeypatch.setattr("builtins.input", lambda _: "y")
    approved = safety.confirm_execution("write_file", {"path": "a.txt", "content": "hello"})
    assert approved is True
