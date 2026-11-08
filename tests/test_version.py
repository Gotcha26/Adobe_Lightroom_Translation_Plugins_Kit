"""Version unique et absence de références obsolètes dans le code (#31)."""

import re
import tomllib
from pathlib import Path

import core

ROOT = Path(__file__).resolve().parent.parent

STALE_NAMES = (
    "Translator_main.py",
    "Extractor_main.py",
    "Applicator_main.py",
    "Delete_temp_dir.py",
    "Restore_backup.py",
    "common.paths",
    "common.colors",
)


def _python_sources():
    yield ROOT / "LocalizationToolKit.py"
    for folder in ("core", "tools"):
        yield from (ROOT / folder).rglob("*.py")


def test_version_matches_pyproject():
    with open(ROOT / "pyproject.toml", "rb") as f:
        declared = tomllib.load(f)["project"]["version"]
    assert core.__version__ == declared == "1.1.0"


def test_po_header_uses_same_version():
    po = (ROOT / "locale" / "en" / "LC_MESSAGES" / "messages.po").read_text(encoding="utf-8")
    match = re.search(r'"Project-Id-Version: (.+?)\\n"', po)
    assert match and match.group(1) == f"LocalizationToolKit {core.__version__}"


def test_no_stale_names_in_sources():
    offenders = []
    for path in _python_sources():
        text = path.read_text(encoding="utf-8")
        for name in STALE_NAMES:
            if name in text:
                offenders.append(f"{path.relative_to(ROOT)}: {name}")
    assert not offenders, offenders
