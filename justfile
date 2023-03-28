set shell := ["bash", "-uc"]

base-directory := justfile_directory()

_default:
    @just --list --unsorted

###############################################################################
## Documentation
###############################################################################

docs-config := base-directory / "docs/mkdocs.yml"

# Serve current docs located in ./docs/docs
serve-docs port="8000":
    typer {{base-directory}}/kpops/cli/main.py utils docs --name kpops --output {{base-directory}}/docs/docs/user/references/cli-commands.md
    sed -i '1s/.*/# CLI Usage/' {{base-directory}}/docs/docs/user/references/cli-commands.md
    poetry run mkdocs serve --config-file {{ docs-config }} --dev-addr localhost:{{ port }}
