"""Golden task 1 check: every path:line reference in a doc resolves in a repo clone.

Usage: python tests/golden/check_refs.py DOC REPO_ROOT
Exit code 0 on pass, 1 on fail; prints one line per problem.
"""

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


# path:line, path:line-line, or path#Lline (GitHub style); paths need a file extension
REF_PATTERN = re.compile(
    r"(?P<path>[A-Za-z0-9_.\-/\\]+\.[A-Za-z0-9]+)"
    r"(?::(?P<start>\d+)(?:-(?P<end>\d+))?|#L(?P<gstart>\d+)(?:-L(?P<gend>\d+))?)"
)

MIN_REFS = 5
REQUIRED_FILE = "app/llm.py"
REQUIRED_TERM = "tool_choice"


@dataclass
class Ref:
    path: str
    start: int
    end: int


@dataclass
class Result:
    refs: list[Ref] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.problems


def find_refs(text: str) -> list[Ref]:
    refs = []
    for m in REF_PATTERN.finditer(text):
        raw = m.group("path").replace("\\", "/")
        # skip URLs such as https://github.com/.../app/llm.py#L216
        if "//" in raw or text[max(0, m.start() - 1) : m.start()] == ":":
            continue
        path = raw[2:] if raw.startswith("./") else raw
        start = int(m.group("start") or m.group("gstart"))
        end = int(m.group("end") or m.group("gend") or start)
        refs.append(Ref(path, start, end))
    return refs


def check(doc: Path, repo_root: Path) -> Result:
    result = Result()
    if not doc.is_file():
        result.problems.append(f"doc not found: {doc}")
        return result
    if not repo_root.is_dir():
        result.problems.append(f"repo clone not found: {repo_root}")
        return result

    text = doc.read_text(encoding="utf-8", errors="replace")
    result.refs = find_refs(text)

    if len(result.refs) < MIN_REFS:
        result.problems.append(
            f"only {len(result.refs)} path:line references, need {MIN_REFS}"
        )
    if not any(r.path == REQUIRED_FILE for r in result.refs):
        result.problems.append(f"no reference to {REQUIRED_FILE}")
    if REQUIRED_TERM not in text:
        result.problems.append(f"doc never mentions {REQUIRED_TERM}")

    line_counts: dict[str, int] = {}
    for ref in result.refs:
        target = repo_root / ref.path
        if not target.is_file():
            result.problems.append(f"{ref.path}:{ref.start}: file not in clone")
            continue
        if ref.path not in line_counts:
            with target.open(encoding="utf-8", errors="replace") as f:
                line_counts[ref.path] = sum(1 for _ in f)
        n = line_counts[ref.path]
        if ref.start < 1 or ref.end < ref.start or ref.end > n:
            result.problems.append(
                f"{ref.path}:{ref.start}-{ref.end}: outside the file's {n} lines"
            )
    return result


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__.strip())
        return 2
    result = check(Path(argv[1]), Path(argv[2]))
    for problem in result.problems:
        print(f"FAIL {problem}")
    if result.passed:
        print(f"PASS {len(result.refs)} references, all resolve")
    return 0 if result.passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
