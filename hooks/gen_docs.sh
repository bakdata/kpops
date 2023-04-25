#!/usr/bin/env bash

SCRIPT_DIR=$(realpath ${BASH_SOURCE[0]} --canonicalize-existing)
OUTPUT="${SCRIPT_DIR%/*/*}"/docs/docs/user/references/cli-commands.md

# Generate "CLI Usage"
poetry run typer "$SCRIPT_DIR"/kpops/cli/main.py utils docs --name kpops --output "$OUTPUT"

# Change title to "CLI Usage"
sed -i '1s/.*/# CLI Usage/' "$OUTPUT"
