from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path


def collect_pipeline_paths(pipeline_path: Path) -> Iterator[Path]:
    """Generate paths to pipeline files.

    :param pipeline_path: The path to the pipeline file or directory.

    :yields: Path: Paths to pipeline files. If `pipeline_path` file yields the given path.
             For a directory it yields all the pipeline.yaml paths.

    :raises: RuntimeError: If `pipeline_path` is neither a file nor a directory.
    """
    if pipeline_path.is_file():
        yield pipeline_path
    elif pipeline_path.is_dir():
        yield from pipeline_path.glob("**/pipeline*.yaml")
    else:
        msg = f"The entered pipeline path '{pipeline_path}' should be a directory or file."
        raise RuntimeError(msg)
