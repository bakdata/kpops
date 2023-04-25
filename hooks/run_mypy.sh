#!/usr/bin/env bash
# from https://jaredkhan.com/blog/mypy-pre-commit

set -o errexit

SCRIPT_DIR=$(realpath ${BASH_SOURCE[0]} --canonicalize-existing)
ROOT_DIR=${SCRIPT_DIR%/*/*}

# change directory to the project root directory.
cd $ROOT_DIR

mypy --pretty kpops tests
