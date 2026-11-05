@echo off
cd /d "%~dp0.."
python src\main.py --package A --repository examples\single.json --test-repo
python src\main.py --package A --repository examples\chain.json --test-repo
python src\main.py --package A --repository examples\diamond.json --test-repo
python src\main.py --package A --repository examples\cycle.json --test-repo
python src\main.py --package A --repository examples\self_cycle.json --test-repo
python src\main.py --package A --repository examples\disconnected.json --test-repo
python src\main.py --package A --repository examples\empty.json --test-repo
python src\main.py --package A --repository examples\invalid.json --test-repo
python src\main.py --package A --repository examples\diamond.json --test-repo --filter B
python src\main.py --package A --repository examples\chain.json --test-repo --filter B
pause
