#!/usr/bin/env python

from os import path

from setuptools import setup

here = path.abspath(path.dirname(__file__))

# read version string
with open(path.join(here, "ffmpeg_normalize", "_version.py")) as version_file:
    version = eval(version_file.read().split("=")[1].strip())

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf8") as f:
    long_description = f.read()

# Get the history from the CHANGELOG file
with open(path.join(here, "CHANGELOG.md"), encoding="utf8") as f:
    history = f.read()

setup(
    name="ffmpeg-normalize",
    version=version,
    description="Normalize audio via ffmpeg",
    long_description=long_description + "\n\n" + history,
    long_description_content_type="text/markdown",
    author="Werner Robitza",
    author_email="werner.robitza@gmail.com",
    url="https://github.com/slhck/ffmpeg-normalize",
    packages=["ffmpeg_normalize"],
    include_package_data=True,
    package_data={
        "ffmpeg_normalize": ["py.typed"],
    },
    install_requires=[
        "tqdm",
        "colorama;platform_system=='Windows'",
        "ffmpeg-progress-yield",
        "colorlog",
    ],
    license="MIT",
    zip_safe=False,
    keywords="ffmpeg, normalize, audio",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": ["ffmpeg-normalize = ffmpeg_normalize.__main__:main"]
    },
)
