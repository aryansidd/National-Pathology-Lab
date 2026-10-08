@echo off
cd /d "%~dp0"
title National Pathology Lab - Local Development
if not exist venv\Scripts\python.exe (
  py -3 -m venv venv
  if errorlevel 1 (echo Python 3.11/3.12 is required. & pause & exit /b 1)
  call venv\Scripts\activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
) else call venv\Scripts\activate
python app.py
