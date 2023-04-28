"""Generates the whole 'generatable' KPOps documentation"""
import subprocess

from hooks import PATH_ROOT

# TODO: try to use typer_cli.main.docs here instead
subprocess.run(PATH_ROOT / "hooks/gen_docs.sh")

text: list[str] = []
with open(PATH_ROOT / "docs/docs/user/references/cli-commands.md", "r") as f:
    text = f.readlines()
text[0] = "# CLI Usage\n"
with open(PATH_ROOT / "docs/docs/user/references/cli-commands.md", "w") as f:
    f.writelines(text)
