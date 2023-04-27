from pathlib import Path
import subprocess

# TODO: try to use typer_cli.main.docs here instead

ROOT_PATH = Path(__file__).parents[1]

subprocess.run(ROOT_PATH / "hooks/gen_docs.sh")

text = []
with open(ROOT_PATH / "docs/docs/user/references/cli-commands.md", "r") as f:
    text = f.readlines()
text[0]="# CLI Usage\n"
with open(ROOT_PATH / "docs/docs/user/references/cli-commands.md", "w") as f:
    f.writelines(text)
