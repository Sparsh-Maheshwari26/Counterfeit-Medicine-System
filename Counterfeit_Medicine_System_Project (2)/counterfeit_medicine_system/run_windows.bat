cls@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Creating project virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 (
        echo Could not create a virtual environment. Install Python 3.10 or newer and try again.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo Could not activate the virtual environment.
    pause
    exit /b 1
)

python -m pip install --upgrade pip
if errorlevel 1 goto :install_error
python -m pip install -r requirements.txt
if errorlevel 1 goto :install_error
python -m streamlit run app.py
if errorlevel 1 goto :run_error
goto :end

:install_error
echo Dependency installation failed. Check your internet connection and requirements.txt.
pause
exit /b 1

:run_error
echo The app stopped with an error. Copy the terminal message if you need help fixing it.
pause
exit /b 1

:end
endlocal
