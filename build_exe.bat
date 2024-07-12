@echo off

nuitka src/main.py --onefile --standalone --windows-icon-from-ico=icon.ico --remove-output --output-dir=dist --output-file=radon
