@echo off
cd /d "%~dp0.."
python src\main.py --repository https://pypi.org/pypi
python src\main.py --package "bad name" --repository https://pypi.org/pypi
python src\main.py --package requests --repository ftp://host
python src\main.py --package A --repository missing.json --test-repo
python src\main.py --package requests --repository https://pypi.org/pypi --test-repo=maybe
python src\main.py --package requests --repository https://pypi.org/pypi --ascii-tree=maybe
python src\main.py --package requests --repository https://pypi.org/pypi --filter
python src\main.py --package requests --repository https://pypi.org/pypi --filter " "
pause
