from contextlib import redirect_stdout
from pathlib import Path
from kpops.utils.gen_schema import gen_pipeline_schema, gen_config_schema
from io import StringIO

PATH_TO_SCHEMA = Path(__file__).parents[1] / "docs/docs/schema"

schema = ""
with redirect_stdout(StringIO()) as f:
    gen_pipeline_schema()
    schema = f.getvalue()

with open(PATH_TO_SCHEMA / "pipeline.json", "w") as file:
    file = schema

with redirect_stdout(StringIO()) as f:
    gen_config_schema()
    schema = f.getvalue()

with open(PATH_TO_SCHEMA / "config.json", "w") as file:
    file = schema


