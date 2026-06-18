from __future__ import annotations

from collections.abc import Iterable, Iterator
from glob import glob
from pathlib import Path

from kpops.const.file_type import PIPELINE_YAML


def collect_pipeline_paths(pipeline_paths: Iterable[Path]) -> Iterator[Path]:
    """Generate paths to pipeline files.

    :param pipeline_paths: The list of paths to the pipeline files or directories.

    :yields: Path: Paths to pipeline files. If `pipeline_path` file yields the given path.
             For a directory it yields all the pipeline.yaml paths.

    :raises: ValueError: If `pipeline_path` is neither a file nor a directory.
    """
    for pipeline_path in pipeline_paths:
        if pipeline_path.is_file():
            yield pipeline_path
        elif pipeline_path.is_dir():
            # TODO: In python 3.13 symbolic links become supported by Path.glob
            # docs.python.org/3.13#pathlib.Path.glob, probably it make sense to use it after ugprading,
            # likely the code will look like:
            # yield from sorted(pipeline_path.glob(f"**/{PIPELINE_YAML}", recurse_symlinks=True))
            yield from sorted(
                Path(p).resolve()
                for p in glob(f"{pipeline_path}/**/{PIPELINE_YAML}", recursive=True)  # noqa: PTH207
            )
        else:
            msg = f"The entered pipeline path '{pipeline_path}' should be a directory or file."
            raise ValueError(msg)
