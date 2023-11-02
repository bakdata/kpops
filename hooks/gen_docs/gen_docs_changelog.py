"""Copies ``CHANGELOG.md`` from root to the docs."""
from hooks.gen_docs.utils import copy_file
from hooks import ROOT

SOURCE = ROOT / "CHANGELOG.md"
DEST = ROOT / "docs/docs/user/changelog.md"

copy_file(SOURCE, DEST)
