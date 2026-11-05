#!/bin/sh
cd "$(dirname "$0")/.." || exit 1
python3 src/main.py --repository https://pypi.org/pypi
python3 src/main.py --package "bad name" --repository https://pypi.org/pypi
python3 src/main.py --package requests --repository ftp://host
python3 src/main.py --package A --repository missing.json --test-repo
python3 src/main.py --package requests --repository https://pypi.org/pypi --test-repo=maybe
python3 src/main.py --package requests --repository https://pypi.org/pypi --ascii-tree=maybe
python3 src/main.py --package requests --repository https://pypi.org/pypi --filter
python3 src/main.py --package requests --repository https://pypi.org/pypi --filter " "
