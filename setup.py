#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup
# To use a consistent encoding
from codecs import open
from os import path
from ffmpeg_normalize import __version__ as version

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Get the history from the HISTORY file
with open(path.join(here, 'HISTORY.md'), encoding='utf-8') as f:
    history = f.read()

try:
    import pypandoc
    long_description = pypandoc.convert_text(long_description, 'rst', format='md')
    history = pypandoc.convert_text(history, 'rst', format='md')
except ImportError:
    print("pypandoc module not found, could not convert Markdown to RST")

setup(
    name='ffmpeg-normalize',
    version=version,
    description="Normalize audio via ffmpeg",
    long_description=long_description + '\n\n' + history,
    author="Werner Robitza",
    author_email='werner.robitza@gmail.com',
    url='https://github.com/slhck/ffmpeg-normalize',
    packages=['ffmpeg_normalize'],
    include_package_data=True,
    license="MIT",
    zip_safe=False,
    keywords='ffmpeg, normalize, audio',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Multimedia :: Sound/Audio',
        'Topic :: Multimedia :: Sound/Audio :: Analysis',
        'Topic :: Multimedia :: Sound/Audio :: Conversion',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    entry_points={
        'console_scripts': [
            'ffmpeg-normalize = ffmpeg_normalize.__main__:main'
        ]
    },
)
