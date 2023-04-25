#!/usr/bin/env bash
# from https://jaredkhan.com/blog/mypy-pre-commit

set -o errexit

scriptDir=$(realpath ${BASH_SOURCE[0]} --canonicalize-existing)
rootDir=${scriptDir%/*/*}

# change directory to the project root directory.
cd $rootDir

mypy --pretty kpops tests
