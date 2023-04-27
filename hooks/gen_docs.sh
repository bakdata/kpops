#!/usr/bin/env bash

ROOT_DIR=$(realpath ${0%/*/*})
OUTPUT="$ROOT_DIR"/docs/docs/user/references/cli-commands.md

# Generate "CLI Usage"
poetry run typer "$ROOT_DIR"/kpops/cli/main.py utils docs --name kpops --output "$OUTPUT"

# Change title to "CLI Usage"
(sed -i '' '1s/.*/# CLI Usage/' "$OUTPUT" || sed -i '1s/.*/# CLI Usage/' "$OUTPUT") 2>/dev/null

# The line above will always throw an error, one side works only in bash, the other in zsh
# Hence, hide the output and only detect whether both failed
if [ $? != 0 ]
then
    echo "sed failed"
fi
