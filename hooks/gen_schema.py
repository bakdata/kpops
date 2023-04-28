"""Generates the stock KPOps editor integration schemas"""
from contextlib import redirect_stdout
from io import StringIO

from hooks import PATH_ROOT
from kpops.utils.gen_schema import gen_config_schema, gen_pipeline_schema

PATH_TO_SCHEMA = PATH_ROOT / "docs/docs/schema"

schema = ""
with redirect_stdout(StringIO()) as f:
    gen_pipeline_schema()
    schema = f.getvalue()

with open(PATH_TO_SCHEMA / "pipeline.json", "w") as file:
    file.write(schema)

with redirect_stdout(StringIO()) as f:
    gen_config_schema()
    schema = f.getvalue()

with open(PATH_TO_SCHEMA / "config.json", "w") as file:
    file.write(schema)
