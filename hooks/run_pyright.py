"""Runs Pyright"""
from pyright import run

from hooks import cd

with cd():
    run()
