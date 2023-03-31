#!/usr/bin/env bash

scriptDir=$(dirname -- "$(readlink -f -- "$BASH_SOURCE")")

echo "generate CLI Usage"
poetry run typer $scriptDir/kpops/cli/main.py utils docs --name kpops --output $scriptDir/docs/docs/user/references/cli-commands.md

echo "Fix name"
sed -i '1s/.*/# CLI Usage/' $scriptDir/docs/docs/user/references/cli-commands.md

echo "Diff docs, fail if existing changes"
git diff --exit-code $scriptDir/docs
