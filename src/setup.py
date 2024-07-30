from setuptools import setup, find_packages
from radon.utils import VERSION_RADON

setup(
    name="radonmc",
    version=VERSION_RADON,
    packages=find_packages(),
    package_data={
        "radon": ["builtin/*", "cpl/*"],
    },
    entry_points={
        "console_scripts": [
            "radon=radon.__main__:main",
        ],
    },
    install_requires=[],
    author="OguzhanUmutlu",
    description="Radon is a programming language that gets compiled to Minecraft: Java Edition's mcfunction files.",
    long_description=open("../README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/OguzhanUmutlu/radon",
    license="MIT"
)
