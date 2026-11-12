#!/bin/sh
cd "$(dirname "$0")/.." || exit 1
python3 src/main.py --package python-dateutil --repository https://pypi.org/pypi
python3 src/main.py --package six --repository https://pypi.org/pypi
python3 src/main.py --package pytz --repository https://pypi.org/pypi
