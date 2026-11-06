@echo off
setlocal
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
title JPG do PDF

rem --- Najit Python (py launcher, jinak python) ---
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY (
    python --version >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo CHYBA: Python neni nainstalovany nebo neni v PATH.
    echo Nainstalujte ho z https://www.python.org a zaskrtnete "Add Python to PATH".
    goto konec
)

rem --- Zkontrolovat knihovny, pripadne doinstalovat ---
%PY% -c "import img2pdf, PIL" >nul 2>&1
if errorlevel 1 (
    echo Instaluji potrebne knihovny img2pdf a pillow - jen poprve...
    if exist "%~dp0balicky\" (
        %PY% -m pip install --disable-pip-version-check --no-index --find-links "%~dp0balicky" img2pdf pillow
    ) else (
        %PY% -m pip install --disable-pip-version-check img2pdf pillow
    )
    %PY% -c "import img2pdf, PIL" >nul 2>&1
    if errorlevel 1 (
        echo CHYBA: knihovny se nepodarilo nainstalovat.
        goto konec
    )
    echo.
)

rem --- Spustit skript (pretazena slozka se preda jako parametr) ---
%PY% "%~dp0jpg2pdf.py" %1

:konec
echo.
pause
