#!/bin/sh
# One command, no human input.
set -e
cd "$(dirname "$0")"
python3 agent.py "$@"
