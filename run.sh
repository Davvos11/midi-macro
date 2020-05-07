#!/usr/bin/env bash
set -o history -o histexpand
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

cd "$DIR" || exit &> log.txt
pipenv run python main.py &> log.txt