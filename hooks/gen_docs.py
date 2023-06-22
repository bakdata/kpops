"""Generates the whole 'generatable' KPOps documentation"""
import subprocess
from pathlib import Path

from hooks import PATH_ROOT

PATH_KPOPS_MAIN = PATH_ROOT / "kpops/cli/main.py"
PATH_CLI_COMMANDS_DOC = PATH_ROOT / "docs/docs/user/references/cli-commands.md"
PATH_DOCS_RESOURCES = PATH_ROOT / "docs/docs/resources"


def concatenate_text_files(*file_paths: Path, target: Path):
    """Concatenates the given files into one

    :param *file_paths: Files to be conatenated. The order of the inputs will be
        retained in the result
    :param target: File to store the result in. Note that any previous contents
        will be deleted.
    """
    res = ""
    for file in file_paths:
        with open(file, "r") as f:
            res += f.read()
    with open(target, "w+") as f:
        f.write(res)


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

# Concatenate individual examples into the complete files
pipeline_components = (
    "kubernetes-app.yaml",
    "kafka-app.yaml",
    "streams-app.yaml",
    "producer.yaml",
    "kafka-source-connector.yaml",
    "kafka-sink-connector.yaml",
)
pipeline_component_defaults = (
    "defaults-" + f for f in (*pipeline_components, "kafka-connector.yaml")
)
concatenate_text_files(
    *(PATH_DOCS_RESOURCES / "pipeline-components" / s for s in pipeline_components),
    target=PATH_DOCS_RESOURCES / "pipeline-components" / "pipeline.yaml",
)
concatenate_text_files(
    *(
        PATH_DOCS_RESOURCES / "pipeline-defaults" / s
        for s in pipeline_component_defaults
    ),
    target=PATH_DOCS_RESOURCES / "pipeline-defaults" / "defaults.yaml",
)
