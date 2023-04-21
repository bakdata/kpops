#!/usr/bin/env bash

scriptDir=$(realpath ${BASH_SOURCE[0]} --canonicalize-existing)
output="${scriptDir%/*/*/*}"/docs/docs/user/references/cli-commands.md

# Generate "CLI Usage"
poetry run typer "$scriptDir"/kpops/cli/main.py utils docs --name kpops --output "$output"

# Change title to "CLI Usage"
sed -i '1s/.*/# CLI Usage/' "$output"
