#!/usr/bin/env bash
# from https://jaredkhan.com/blog/mypy-pre-commit

set -o errexit

ROOT_DIR=$(realpath ${0%/*/*} --canonicalize-existing)

# change directory to the project root directory.
cd $ROOT_DIR

mypy --pretty kpops tests
