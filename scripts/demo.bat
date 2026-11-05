@echo off
cd /d "%~dp0.."
python src\main.py --package requests --repository https://pypi.org/pypi
python src\main.py --package A --repository examples\repository.json --test-repo --ascii-tree --filter B
pause
