@echo off
cd /d "%~dp0.."
python src\main.py --package requests --repository https://pypi.org/pypi
python src\main.py --package six --repository https://pypi.org/pypi
python src\main.py --package peppercorn --repository https://pypi.org/pypi
pause
