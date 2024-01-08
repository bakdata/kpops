import json
from pathlib import Path
from kpops.utils.cli_commands import create_config
from pprint import pprint

Path(Path() / "conf.yaml").unlink(missing_ok=True)

create_config("conf", Path())
# with Path("/home/sujuka99/Projects/bakdata/kpops/docs/docs/schema/config.json").open() as conf_schema:
#     conf_dict = json.load(conf_schema)
#     pprint(conf_dict)
