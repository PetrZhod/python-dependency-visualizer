@echo off
cd /d "%~dp0.."
python src\main.py --package python-dateutil --repository https://pypi.org/pypi --ascii-tree
python src\main.py --package six --repository https://pypi.org/pypi --ascii-tree
python src\main.py --package pytz --repository https://pypi.org/pypi --ascii-tree
pause
