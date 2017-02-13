#!/usr/bin/env python
# -*- coding: utf-8 -*-
from setuptools import setup


with open('README.rst') as readme_file:
    readme = readme_file.read()

with open('HISTORY.rst') as history_file:
    history = history_file.read().replace('.. :changelog:', '')

requirements = [
    'docopt',
]

test_requirements = [
    # 'pytest',
]

import ffmpeg_normalize

setup(
    name='ffmpeg-normalize',
    version=ffmpeg_normalize.__version__,
    description="Normalize audio via ffmpeg / avconv",
    long_description=readme + '\n\n' + history,
    author="Werner Robitza",
    author_email='werner.robitza@gmail.com',
    url='https://github.com/slhck/ffmpeg-normalize',
    packages=[
        'ffmpeg_normalize',
    ],
    include_package_data=True,
    install_requires=requirements,
    license="MIT",
    zip_safe=False,
    keywords='avconv, ffmpeg, libav, normalize, audio',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
    ],
    # test_suite='tests',
    # cmdclass={'test': PyTest},
    # tests_require=test_requirements,
    entry_points={
        'console_scripts': [
            'ffmpeg-normalize = ffmpeg_normalize.__main__:main'
        ]
    },
)
