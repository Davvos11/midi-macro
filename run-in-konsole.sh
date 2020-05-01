#!/usr/bin/env bash
cd "$(dirname "$BASH_SOURCE")" || exit
konsole -e pipenv run python main.py &> /dev/null &