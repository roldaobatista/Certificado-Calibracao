@echo off
setlocal EnableExtensions EnableDelayedExpansion

if not defined USERPROFILE (
  for /f "tokens=2,*" %%A in ('reg query "HKCU\Volatile Environment" /v USERPROFILE 2^>nul ^| findstr /I "USERPROFILE"') do set "USERPROFILE=%%B"
)

if not defined USERPROFILE if defined HOMEDRIVE if defined HOMEPATH set "USERPROFILE=%HOMEDRIVE%%HOMEPATH%"
if not defined USERPROFILE if defined SystemDrive if defined USERNAME set "USERPROFILE=%SystemDrive%\Users\%USERNAME%"
if not defined USERPROFILE if defined USERNAME set "USERPROFILE=C:\Users\%USERNAME%"
if not defined HOME set "HOME=%USERPROFILE%"
if not defined APPDATA if defined USERPROFILE set "APPDATA=%USERPROFILE%\AppData\Roaming"
if not defined LOCALAPPDATA if defined USERPROFILE set "LOCALAPPDATA=%USERPROFILE%\AppData\Local"
if not defined PROGRAMDATA set "PROGRAMDATA=C:\ProgramData"
if not defined SystemRoot set "SystemRoot=C:\Windows"
if not defined windir set "windir=C:\Windows"
if not defined TEMP if defined USERPROFILE set "TEMP=%USERPROFILE%\AppData\Local\Temp"
if not defined TMP if defined USERPROFILE set "TMP=%USERPROFILE%\AppData\Local\Temp"

set "_PATH=;!PATH!;"
if exist "%APPDATA%\npm" (
  set "_CANDIDATE=;%APPDATA%\npm;"
  if /I "!_PATH:%_CANDIDATE%=!"=="!_PATH!" (
    set "PATH=!PATH!;%APPDATA%\npm"
    set "_PATH=;!PATH!;"
  )
)

if exist "%USERPROFILE%\.local\bin" (
  set "_CANDIDATE=;%USERPROFILE%\.local\bin;"
  if /I "!_PATH:%_CANDIDATE%=!"=="!_PATH!" (
    set "PATH=!PATH!;%USERPROFILE%\.local\bin"
    set "_PATH=;!PATH!;"
  )
)

if "%~1"=="" goto :done

set "COMMAND=%~1"
shift
call "%COMMAND%" %*
set "EXIT_CODE=%ERRORLEVEL%"
exit /b %EXIT_CODE%

:done
endlocal
exit /b 0
