#!/usr/bin/env bash

OUTPUT=./docs/docs/user/references/cli-commands.md

# Generate "CLI Usage"
poetry run typer ./kpops/cli/main.py utils docs --name kpops --output "$OUTPUT"
