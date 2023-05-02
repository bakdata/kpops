"""KPOps pre-commit hooks"""
import os
from contextlib import contextmanager
from pathlib import Path

PATH_ROOT = Path(__file__).parents[1]

# Taken from https://stackoverflow.com/a/24176022/11610149a
@contextmanager
def cd(newdir: Path = PATH_ROOT):
    """Changes current working dir to :param: newdir

    :param newdir: The desired workign directory, defaults to the root KPOps dir path
    :type newdir: Path, optional
    """
    prevdir = Path().resolve()
    os.chdir(newdir.expanduser())
    try:
        yield
    finally:
        os.chdir(prevdir)
