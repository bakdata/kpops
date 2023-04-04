#!/usr/bin/env bash

scriptDir=$(dirname -- "$(readlink -f -- "${BASH_SOURCE[0]}" )")
output="$scriptDir"/docs/docs/user/references/cli-commands.md

echo "generate CLI Usage"
poetry run typer "$scriptDir"/kpops/cli/main.py utils docs --name kpops --output "$output"

echo "Changing title to CLI Usage"
sed -i '1s/.*/# CLI Usage/' "$output"

if [ -n "$(git diff --exit-code "$scriptDir"/docs)" ]
then
    echo "::error::Generatable documentation is not up-to-date. Updating..." && exit 1
else
    echo "::notice::Documentation is up-to-date."
fi
