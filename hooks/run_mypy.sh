#!/usr/bin/env bash

set -o errexit

ROOT_DIR=$(realpath ${0%/*/*})

# change directory to the project root directory.
cd $ROOT_DIR

mypy --pretty kpops tests hooks
