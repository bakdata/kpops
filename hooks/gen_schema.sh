#!/usr/bin/env bash

ROOT_DIR=$(realpath ${0%/*/*})
OUTPUT="$ROOT_DIR"/docs/docs/schema

# Generate pipeline schema
poetry run kpops schema pipeline > "$OUTPUT"/pipeline.json

# Generate config schema
poetry run kpops schema config > "$OUTPUT"/config.json
