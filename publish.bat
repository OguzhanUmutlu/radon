@echo off

pushd %~dp0

cd src
python setup.py sdist bdist_wheel
REM pip install . --upgrade
REM radon
twine upload dist/*

popd