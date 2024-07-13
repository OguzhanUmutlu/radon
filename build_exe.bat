@echo off

pushd %~dp0

nuitka src/main.py --onefile --standalone --windows-icon-from-ico=assets/icon.ico --remove-output --output-dir=dist --output-file=radon

popd