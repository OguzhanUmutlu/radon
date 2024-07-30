@echo off
setlocal enabledelayedexpansion

clear

set "folders="

for /D %%d in (examples/*) do (
    if defined folders (
        set "folders=!folders!|%~dp0examples\%%~nd"
    ) else (
        set "folders=%~dp0examples\%%~nd"
    )
)

python -m src.radon -d="%folders%"

endlocal