#!/usr/bin/env bash

SCRIPT_DIR=$(realpath ${BASH_SOURCE[0]} --canonicalize-existing)
OUTPUT="${SCRIPT_DIR%/*/*}"/docs/docs/schema

# Generate pipeline schema
poetry run kpops schema pipeline > "$OUTPUT"/pipeline.json

# Generate config schema
poetry run kpops schema config > "$OUTPUT"/config.json
