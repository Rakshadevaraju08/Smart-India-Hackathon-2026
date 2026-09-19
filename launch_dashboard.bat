@echo off
echo ======================================================================
echo    KAIROS COMMAND TWIN - URBAN FLOOD NOWCASTING SYSTEM (SIH 2026)
echo    Ministry of Earth Sciences (MoES) / NCMRWF - Chennai Pilot #26085
echo ======================================================================
echo Launching Web GIS Command Dashboard in default browser...
start "" "%~dp0frontend\index.html"
echo.
echo [SUCCESS] Dashboard launched in your default web browser!
echo If the browser does not open automatically, open this file directly:
echo %~dp0frontend\index.html
echo ======================================================================
exit /b 0
