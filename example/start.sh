#!/usr/bin/env bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"/.. || (echo "Failed to cd" & exit)
export PYTHONPATH="${PYTHONPATH}:$DIR"
pipenv run python example/main.py