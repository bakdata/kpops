"""Generates the documentation on KPOps CLI usage."""

import subprocess

from hooks import ROOT

PATH_KPOPS_MAIN = ROOT / "kpops/cli/main.py"
PATH_CLI_COMMANDS_DOC = ROOT / "docs/docs/user/references/cli-commands.md"

# TODO(Ivan Yordanov): try to use typer_cli.main.docs here instead
# https://github.com/bakdata/kpops/issues/297

if __name__ == "__main__":
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
    subprocess.run(typer_args, check=True, capture_output=True)

    # Replace wrong title in CLI Usage doc
    with PATH_CLI_COMMANDS_DOC.open("r") as f:
        text = f.readlines()
    text[0] = "# CLI Usage\n"
    with PATH_CLI_COMMANDS_DOC.open("w") as f:
        f.writelines(text)
