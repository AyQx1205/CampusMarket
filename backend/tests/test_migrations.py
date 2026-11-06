"""Alembic 迁移链：必须单头，且 0002 接在 0001 之后。"""

import re
from pathlib import Path

VERSIONS = Path(__file__).resolve().parents[1] / "alembic" / "versions"


def _read_revision(path: Path) -> tuple[str, str | None]:
    text = path.read_text(encoding="utf-8")
    revision = re.search(r'^revision:\s*str\s*=\s*"([^"]+)"', text, re.MULTILINE)
    down = re.search(
        r'^down_revision:\s*[^=]+=\s*(?:"([^"]+)"|None)', text, re.MULTILINE
    )
    assert revision, f"缺少 revision: {path.name}"
    return revision.group(1), (down.group(1) if down and down.group(1) else None)


def test_migration_chain_has_single_head() -> None:
    revisions = {path.name: _read_revision(path) for path in VERSIONS.glob("*.py")}
    assert revisions, "没有找到迁移文件"

    all_revisions = {revision for revision, _ in revisions.values()}
    parents = {down for _, down in revisions.values() if down}
    heads = all_revisions - parents

    assert len(heads) == 1, f"迁移应只有一个 head，实际: {heads}"
    assert "0001" in all_revisions
    assert "0002" in all_revisions


def test_0002_extends_0001() -> None:
    by_revision = {
        revision: path
        for path in VERSIONS.glob("*.py")
        for revision, _ in [_read_revision(path)]
    }
    _, down = _read_revision(by_revision["0002"])
    assert down == "0001"