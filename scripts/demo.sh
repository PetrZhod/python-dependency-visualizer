#!/bin/sh
cd "$(dirname "$0")/.." || exit 1
python3 src/main.py --package requests --repository https://pypi.org/pypi
python3 src/main.py --package A --repository examples/repository.json --test-repo --ascii-tree --filter B
