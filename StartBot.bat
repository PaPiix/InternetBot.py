@echo off

cls
echo   ###                ###
echo  # InternetBot #
echo ###                ###
echo.

set "botFile=Main.py"
set "pyPath=python"
set "autoRestart=Yes"
set "update=Yes"

set "thisDir=%~dp0"

goto start

:update
pushd "%thisDir%"
echo Updating...
echo.
git pull
echo.
popd
goto :EOF

:start
if /i "%update%" == "Yes" (
    call :update
)
"%pyPath%" "%botFile%"
if /i "%autoRestart%"=="Yes" (
    timeout 10
    goto start
)
pause
