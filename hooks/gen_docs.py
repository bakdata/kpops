import subprocess

# TODO: try to use typer_cli.main.docs here instead
subprocess.run("./hooks/gen_docs.sh")

text = []
with open("./docs/docs/user/references/cli-commands.md", "r") as f:
    text = f.readlines()
text[0]="# CLI Usage\n"
with open("./docs/docs/user/references/cli-commands.md", "w") as f:
    f.writelines(text)
