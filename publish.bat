@echo off

pushd %~dp0

cd src
python setup.py sdist bdist_wheel
twine upload dist/*
rmdir /s /q ".\radonmc.egg-info"
rmdir /s /q ".\dist"
rmdir /s /q ".\build"

popd