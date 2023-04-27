#!/usr/bin/env bash

ROOT_DIR=$(realpath ${0%/*/*})
OUTPUT="$ROOT_DIR"/docs/docs/user/references/cli-commands.md

# Generate "CLI Usage"
poetry run typer "$ROOT_DIR"/kpops/cli/main.py utils docs --name kpops --output "$OUTPUT"
