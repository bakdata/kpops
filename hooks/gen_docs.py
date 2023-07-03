"""Generates the whole 'generatable' KPOps documentation"""
import subprocess

from hooks import PATH_ROOT
from kpops import __version__
from kpops.utils.yaml_loading import substitute

PATH_KPOPS_MAIN = PATH_ROOT / "kpops/cli/main.py"
PATH_CLI_COMMANDS_DOC = PATH_ROOT / "docs/docs/user/references/cli-commands.md"
PATH_DOCS_RESOURCES = PATH_ROOT / "docs/docs/resources"

#####################
# EXAMPLES          #
#####################

# Keep the example editor-integration settings up to date.
with open(PATH_DOCS_RESOURCES / "editor_integration/settings_template.json", "r") as template:
    with open(PATH_DOCS_RESOURCES / "editor_integration/settings.json", "w+") as settings:
        settings.write(substitute(template.read(), {"kpops_version": ".".join(__version__.split(".")[:2])}))

#####################
# CLI-USAGE         #
#####################

# Run typer-cli on kpops to generate doc on CLI usage
# TODO: try to use typer_cli.main.docs here instead
typer_args: list[str] = [
    "typer",
    str(PATH_KPOPS_MAIN),
    "utils",
    "docs",
    "--name",
    "kpops",
    "--output",
    str(PATH_CLI_COMMANDS_DOC),
]
subprocess.run(typer_args)

# Replace wrong title in CLI Usage doc
with open(PATH_CLI_COMMANDS_DOC, "r") as f:
    text = f.readlines()
text[0] = "# CLI Usage\n"
with open(PATH_CLI_COMMANDS_DOC, "w") as f:
    f.writelines(text)



