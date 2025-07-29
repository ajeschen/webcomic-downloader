@echo off
cd /d %~dp0

REM Install dependencies
pip install -r requirements.txt

REM Activate virtual environment if it exists
if exist env\Scripts\activate.bat (
    call env\Scripts\activate.bat
)

python main.py
pause 