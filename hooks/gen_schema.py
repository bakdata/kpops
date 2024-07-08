"""Generates the stock KPOps editor integration schemas."""

from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from hooks import ROOT
from kpops.const.file_type import KpopsFileType
from kpops.utils.gen_schema import (
    gen_config_schema,
    gen_defaults_schema,
    gen_pipeline_schema,
)

PATH_TO_SCHEMA = ROOT / "docs/docs/schema"


def gen_schema(scope: KpopsFileType):
    """Generate the specified schema and save it to a file.

    The file is located in docs/docs/schema and is named ``<scope.value>.json``

    :param scope: Scope of the generated schema
    """
    with redirect_stdout(StringIO()) as f:
        match scope:
            case KpopsFileType.PIPELINE:
                gen_pipeline_schema()
            case KpopsFileType.DEFAULTS:
                gen_defaults_schema()
            case KpopsFileType.CONFIG:
                gen_config_schema()
        Path(PATH_TO_SCHEMA / f"{scope.value}.json").write_text(f.getvalue())


if __name__ == "__main__":
    gen_schema(KpopsFileType.PIPELINE)
    gen_schema(KpopsFileType.DEFAULTS)
    gen_schema(KpopsFileType.CONFIG)
