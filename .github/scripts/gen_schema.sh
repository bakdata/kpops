#!/usr/bin/env bash

scriptDir=$(realpath ${BASH_SOURCE[0]} --canonicalize-existing)
output="${scriptDir%/*/*/*}"/docs/docs/schema

# Generate pipeline schema
poetry run kpops schema pipeline > "$output"/pipeline.json

# Generate config schema
poetry run kpops schema config > "$output"/config.json
