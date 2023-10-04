"""Generates the stock KPOps editor integration schemas"""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from hooks import PATH_ROOT
from kpops.utils.gen_schema import SchemaScope, gen_config_schema, gen_pipeline_schema

PATH_TO_SCHEMA = PATH_ROOT / "docs/docs/schema"


def gen_schema(scope: SchemaScope):
    """Generates the specified schema and saves it to a file.

    The file is located in docs/docs/schema and is named ``<scope.value>.json``

    :param scope: Scope of the generated schema
    """
    with redirect_stdout(StringIO()) as f:
        match scope:
            case SchemaScope.PIPELINE:
                gen_pipeline_schema()
            case SchemaScope.CONFIG:
                gen_config_schema()
        Path(PATH_TO_SCHEMA / f"{scope.value}.json").write_text(f.getvalue())


if __name__ == "__main__":
    gen_schema(SchemaScope.PIPELINE)
    # gen_schema(SchemaScope.CONFIG)
