@echo off
echo Building Docker image (this is fast if already built)...
docker build -t qabot .
python run_wizard.py
pause