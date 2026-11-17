"""Tests for the golden task 1 checker. No model or network needed."""

import importlib.util
from pathlib import Path


_spec = importlib.util.spec_from_file_location(
    "check_refs", Path(__file__).with_name("check_refs.py")
)
check_refs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_refs)


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / "app" / "agent").mkdir(parents=True)
    (repo / "app" / "llm.py").write_text("\n".join(f"line {i}" for i in range(1, 301)))
    (repo / "app" / "agent" / "toolcall.py").write_text("a\nb\nc\n" * 20)
    (repo / "config").mkdir()
    (repo / "config" / "config.example.toml").write_text("[llm]\nmodel = 'x'\n")
    return repo


GOOD_DOC = """
# How tool_choice travels
- The client is built in app/llm.py:216-223.
- `ask_tool` takes tool_choice at app/llm.py:250.
- The agent passes it from app/agent/toolcall.py:30 and app/agent/toolcall.py:45.
- Model settings come from config/config.example.toml:1.
- See also [the source](https://github.com/FoundationAgents/OpenManus/blob/main/app/llm.py#L216).
"""


def test_good_doc_passes(tmp_path):
    repo = _make_repo(tmp_path)
    doc = tmp_path / "doc.md"
    doc.write_text(GOOD_DOC)
    result = check_refs.check(doc, repo)
    assert result.passed, result.problems
    assert len(result.refs) == 5


def test_line_past_end_fails(tmp_path):
    repo = _make_repo(tmp_path)
    doc = tmp_path / "doc.md"
    doc.write_text(GOOD_DOC.replace("app/llm.py:250", "app/llm.py:999"))
    result = check_refs.check(doc, repo)
    assert not result.passed
    assert any("999" in p for p in result.problems)


def test_missing_file_fails(tmp_path):
    repo = _make_repo(tmp_path)
    doc = tmp_path / "doc.md"
    doc.write_text(GOOD_DOC + "\n- app/flow/nope.py:3\n")
    result = check_refs.check(doc, repo)
    assert any("not in clone" in p for p in result.problems)


def test_too_few_refs_and_no_term_fail(tmp_path):
    repo = _make_repo(tmp_path)
    doc = tmp_path / "doc.md"
    doc.write_text("Built in app/llm.py:216.")
    result = check_refs.check(doc, repo)
    assert any("need 5" in p for p in result.problems)
    assert any("tool_choice" in p for p in result.problems)


def test_missing_doc_fails(tmp_path):
    result = check_refs.check(tmp_path / "absent.md", _make_repo(tmp_path))
    assert not result.passed


def test_windows_backslash_paths(tmp_path):
    repo = _make_repo(tmp_path)
    doc = tmp_path / "doc.md"
    doc.write_text(GOOD_DOC.replace("app/agent/toolcall.py:30", r"app\agent\toolcall.py:30"))
    assert check_refs.check(doc, repo).passed
