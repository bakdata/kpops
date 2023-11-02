"""Copies ``CONTRIBUTING.md`` from root to the docs."""
from hooks import ROOT
from hooks.gen_docs.utils import copy_file

SOURCE = ROOT / "CONTRIBUTING.md"
DEST = ROOT / "docs/docs/developer/contributing.md"

copy_file(SOURCE, DEST)
