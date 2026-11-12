#!/bin/sh
cd "$(dirname "$0")/.." || exit 1
python3 src/main.py --package A --repository examples/single.json --test-repo
python3 src/main.py --package A --repository examples/chain.json --test-repo
python3 src/main.py --package A --repository examples/diamond.json --test-repo
python3 src/main.py --package A --repository examples/cycle.json --test-repo
python3 src/main.py --package A --repository examples/self_cycle.json --test-repo
python3 src/main.py --package A --repository examples/disconnected.json --test-repo
python3 src/main.py --package A --repository examples/diamond.json --test-repo --filter B
python3 src/main.py --package A --repository examples/diamond.json --test-repo --ascii-tree
