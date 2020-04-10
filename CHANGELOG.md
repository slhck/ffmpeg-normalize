# Changelog


## v1.17.0 (2020-04-10)

* Bump version to 1.17.0. [Werner Robitza]

* Update release script and changelog template. [Werner Robitza]

* Apply pre-filters in all first passes, fixes #118. [Werner Robitza]

  This allows properly reading the level for any kind of normalization, even if
  filters affect the loudness in the first pass.


## v1.16.0 (2020-04-07)

* Bump version to 1.16.0. [Werner Robitza]

* Add all commits to changelog. [Werner Robitza]

* Remove python 2 support. [Werner Robitza]

* Add quiet option, fixes #116. [Werner Robitza]

  - Add a new quiet option
  - Promote some warnings to actual errors that need to be shown
  - Add a very basic test case


## v1.15.8 (2020-03-15)

* Bump version to 1.15.8. [Werner Robitza]

* Improve release script. [Werner Robitza]

* Python 3.8. [Werner Robitza]


## v1.15.7 (2020-03-14)

* Bump version to 1.15.7. [Werner Robitza]

* Only print length warning for non-EBU type normalization. [Werner Robitza]


## v1.15.6 (2019-12-04)

* Bump version to 1.15.6. [Werner Robitza]

* Remove build and dist folder on release. [Werner Robitza]

* Do not exit on error in batch processing. [Werner Robitza]

  Simply process the next file if one has errors, addresses #110.


## v1.15.5 (2019-11-19)

* Bump version to 1.15.5. [Werner Robitza]

* Use minimal dependency for tqdm. [Werner Robitza]

* Remove specific python version requirement. [Werner Robitza]


## v1.15.4 (2019-11-19)

* Bump version to 1.15.4. [Werner Robitza]

* Freeze tqdm version. [Werner Robitza]

* Update python to 3.7. [Werner Robitza]

* Improve release documentation. [Werner Robitza]


## v1.15.3 (2019-10-15)

* Bump version to 1.15.3. [Werner Robitza]

* Do not print stream warning when there is only one stream. [Werner Robitza]

* Remove previous dist versions before release. [Werner Robitza]


## v1.15.2 (2019-07-12)

* Bump version to 1.15.2. [Werner Robitza]

* Warn when duration cannot be read, fixes #105. [Werner Robitza]

* Update README. [Werner Robitza]

  minor improvements in the description


## v1.15.1 (2019-06-17)

* Bump version to 1.15.1. [Werner Robitza]

* Add output to unit test failures. [Werner Robitza]

* Fix input label for audio stream. [Werner Robitza]


## v1.15.0 (2019-06-17)

* Bump version to 1.15.0. [Werner Robitza]

* Add pre-and post-filter hooks, fixes #67. [Werner Robitza]

  This allows users to specify filters to be run before or after the actual
  normalization call, using regular ffmpeg syntax.
  Only applies to audio.

* Document audiostream class. [Werner Robitza]

* Warn when file is too short, fixes #87. [Werner Robitza]

* Update release method to twine. [Werner Robitza]


## v1.14.1 (2019-06-14)

* Bump version to 1.14.1. [Werner Robitza]

* Handle progress output from ffmpeg, fixes #10. [Werner Robitza]

* Merge pull request #99 from Nottt/patch-1. [Werner Robitza]

  fix -cn description

* Fix -cn description. [Nottt]

* Add nicer headers for options in README. [Werner Robitza]


## v1.14.0 (2019-04-24)

* Bump version to 1.14.0. [Werner Robitza]

* Add version file in release script before committing. [Werner Robitza]

* Add option to keep original audio, fixes #83. [Werner Robitza]

* Add pypi badge. [Werner Robitza]

* Allow release script to add changelog for future version; upload to pypi. [Werner Robitza]

* Bump version to 1.13.11. [Werner Robitza]


## v1.13.11 (2019-04-16)

* Bump version to 1.13.11. [Werner Robitza]

* Add release script. [Werner Robitza]

* Add small developer guide on releasing. [Werner Robitza]

* Move HISTORY.md to CHANGELOG.md. [Werner Robitza]

* Fix ffmpeg static build download location. [Werner Robitza]


## v1.3.10 (2019-02-22)

* Bump version. [Werner Robitza]

* Cap measured input loudness, fixes #92. [Werner Robitza]


## v1.3.9 (2019-01-10)

* Bump version. [Werner Robitza]

* Fix handling of errors with tqdm. [Werner Robitza]

* Improve readme. [Werner Robitza]

* Delete issue template. [Werner Robitza]

* Bump version. [Werner Robitza]

* Clarify extra argument options, move to main entry point. [Werner Robitza]

* Update issue templates. [Werner Robitza]


## v1.3.8 (2018-11-28)

* Bump version. [Werner Robitza]

* Clarify extra argument options, move to main entry point. [Werner Robitza]


## v1.3.7 (2018-10-28)

* Bump version. [Werner Robitza]

* Copy metadata from individual streams, fixes #86. [Werner Robitza]

* Add python version for pyenv. [Werner Robitza]


## v1.3.6 (2018-07-09)

* Bump version. [Werner Robitza]

* Update README, fixes #79 and addresses #80. [Werner Robitza]


## v1.3.5 (2018-06-12)

* Bump version. [Werner Robitza]

* Minor README updates. [Werner Robitza]

* Fix documentation of TMPDIR parameter. [Werner Robitza]


## v1.3.4 (2018-05-05)

* Bump version. [Werner Robitza]

* New way to specify extra options. [Werner Robitza]


## v1.3.3 (2018-05-05)

* Update README. [Werner Robitza]

* Decode strings in extra options. [Werner Robitza]


## v1.3.2 (2018-04-25)

* Bump version. [Werner Robitza]

* Merge pull request #69 from UbiCastTeam/master. [Werner Robitza]

  Stderror decoding ignoring utf8 encoding errors

* Stderror decoding ignoring utf8 encoding errors. [Anthony Violo]


## v1.3.1 (2018-04-24)

* Bump version. [Werner Robitza]

* Do not require main module in setup.py, fixes #68. [Werner Robitza]


## v1.3.0 (2018-04-15)

* Bump version. [Werner Robitza]

* Remove dead code. [Werner Robitza]

* Fix for python2 division. [Werner Robitza]

* Update documentation. [Werner Robitza]

* Progress bar. [Werner Robitza]

* Remove imports from test file. [Werner Robitza]

* Fix travis file. [Werner Robitza]

* WIP: progress bar. [Werner Robitza]

* Minor typo in option group. [Werner Robitza]

* Add simple unit test for disabling chapters. [Werner Robitza]


## v1.2.3 (2018-04-11)

* Fix unit test. [Werner Robitza]

* Bump version. [Werner Robitza]

* Add option to disable chapters, fixes #65, also fix issue with metadata. [Werner Robitza]


## v1.2.2 (2018-04-10)

* Bump version. [Werner Robitza]

* Set default loudness target to -23, fixes #48. [Werner Robitza]


## v1.2.1 (2018-04-04)

* Bump version. [Werner Robitza]

* Merge pull request #64 from UbiCastTeam/encoding-issue. [Werner Robitza]

  Stdout and stderror decoding ignoring utf8 encoding errors

* Stdout and stderror decoding ignoring utf8 encoding errors. [Anthony Violo]


## v1.2.0 (2018-03-22)

* Bump version. [Werner Robitza]

* Add errors for impossible format combinations, fixes #60. [Werner Robitza]

* Fix ordering of output maps, fixes #63. [Werner Robitza]

* Improve documentation. [Werner Robitza]


## v1.1.0 (2018-03-06)

* Add option to print first pass statistics. [Werner Robitza]


## v1.0.10 (2018-03-04)

* Bump version. [Werner Robitza]

* Restrict parsing to valid JSON part only, fixes #61. [Werner Robitza]

* Add an example for MP3 encoding. [Werner Robitza]

* Update paypal link. [Werner Robitza]


## v1.0.9 (2018-02-08)

* Bump version. [Werner Robitza]

* Add normalized folder to gitignore. [Werner Robitza]

* Do not print escape sequences on Windows. [Werner Robitza]

* Do not check for file existence, fixes #57. [Werner Robitza]

* Add github issue template. [Werner Robitza]


## v1.0.8 (2018-02-01)

* Bump version. [Werner Robitza]

* Do not check for ffmpeg upon module import. [Werner Robitza]


## v1.0.7 (2018-02-01)

* Bump version. [Werner Robitza]

* Rename function test. [Werner Robitza]

* Fix issue with wrong adjustment parameters, fixes #54. [Werner Robitza]


## v1.0.6 (2018-01-30)

* Allow setting FFMPEG_PATH and document TMP. [Werner Robitza]


## v1.0.5 (2018-01-26)

* Handle edge case for short input clips. [Werner Robitza]


## v1.0.4 (2018-01-26)

* Bump version. [Werner Robitza]

* Do not try to remove nonexisting file in case of error in command. [Werner Robitza]


## v1.0.3 (2018-01-26)

* Bump version. [Werner Robitza]

* Always streamcopy when detecting streams to avoid initializing encoder. [Werner Robitza]

* Fix handling of temporary file. [Werner Robitza]

* Add build status. [Werner Robitza]

* Travis tests. [Werner Robitza]


## v1.0.2 (2018-01-25)

* Fix bug with target level for peak/RMS. [Werner Robitza]

* Update documentation formatting. [Werner Robitza]

* Update history. [Werner Robitza]


## v1.0.1 (2018-01-24)

* Bump version. [Werner Robitza]

* Set default target to -23. [Werner Robitza]


## v1.0.0 (2018-01-23)

* Add version info and test case for dry run. [Werner Robitza]

* New feature detection, add documentation, contributors guide etc. [Werner Robitza]

* WIP: v1.0 rewrite. [Werner Robitza]


## v0.7.3 (2017-10-09)

* Use shutil.move instead of os.rename. [Werner Robitza]


## v0.7.2 (2017-09-17)

* Allow setting threshold to 0. [Werner Robitza]


## v0.7.1 (2017-09-14)

* Bump version. [Werner Robitza]

* Update HISTORY.md. [Werner Robitza]

* Merge pull request #37 from Mathijsz/fix-which-path-expansion. [Werner Robitza]

  expand tilde and environment variables, fixes #36

* Expand tilde and environment variables, fixes #36. [Mathijs]

* Update HISTORY.md. [Werner Robitza]

* Update README w.r.t. loudnorm filter. [Werner Robitza]

* Update README and indentation. [Werner Robitza]


## v0.7.0 (2017-08-02)

* Bump version. [Werner Robitza]

* Fix handling of extra options with spaces. [Werner Robitza]

* Include test script. [Werner Robitza]

* Logging and other improvements. [Werner Robitza]

* Add test files. [Werner Robitza]

* Autopep8 that thing. [Werner Robitza]

* Logger improvements. [Werner Robitza]

* Add example for overwriting. [Werner Robitza]


## v0.6.0 (2017-07-31)

* Allow overwriting input file, fixes #22. [Werner Robitza]

* Version bump. [Werner Robitza]

* Better handle cmd arguments. [Werner Robitza]

* Update README.md. [Werner Robitza]

  add another example


## v0.5.1 (2017-04-04)

* Fix for problem introduced in 304e8df. [Werner Robitza]


## v0.5 (2017-04-02)

* Fix pypi topics. [Werner Robitza]

* Bump version and README. [Werner Robitza]

* Fix issue where output was wrong format. [Werner Robitza]

* Add EBU R128 filter. [Werner Robitza]

* Use Markdown instead of RST for README/HISTORY. [Werner Robitza]

* Define file encode for python3, fixes #24. [Werner Robitza]

* Fix history. [Werner Robitza]

* Fix option -np. [Werner Robitza]

* Clarify merge option. [Werner Robitza]

* Minor documentation improvements. [Werner Robitza]

  - change README from CRLF to LF
  - add "attenuated" in description
  - extend LICENSE year
  - add license to main README


## v0.4.1 (2017-02-13)

* Update for release. [Werner Robitza]

* Merge pull request #21 from mpuels/patch-1. [Werner Robitza]

  Fix for #13

* Fix for #13. [mpuels]

* Mention Python 3. [Werner Robitza]

  mention that Python 3 may work, just didn't have time to test

* Fix README's code blocks. [Werner Robitza]


## v0.4 (2017-01-24)

* Code cleanup, add option to set format and audio codec. [Werner Robitza]


## v0.3 (2017-01-19)

* Add option for no prefix, fixes #20. [Werner Robitza]

* Handle multiple spaces in path; fixes issue #18. [Werner Robitza]

* Handle spaces in path, fixes #12. [Werner Robitza]

* Update README.rst. [Werner Robitza]

* Change default level back  to -26. [Werner Robitza]

* Typo in README example. [Werner Robitza]

* Update documentation. [Werner Robitza]

* Bump to v0.2.0. [Werner Robitza]

  * Support for multiple files and output directories.
  * Support merging of audio with input file
  * Set audio codec and additional options
  * User-definable threshold
  * Better error handling and logging
  * Deprecates avconv

* Change default level back to -28. [Werner Robitza]

* Merge pull request #15 from auricgoldfinger/master. [Werner Robitza]

  Add extended normalisation options

* Add extended normalisation options. [bert]

  - add program option to write output in a separate directory in stead of
     prefixing it

  - add program option to merge the normalized audio in the original
     (video) file rather than creating a separate WAV file

  - change the maximum setting: will now normalize so that max
     volume is set to 0, adjusted with the given level.
     e.g. : -m -l -5 will increase the audio level to max = -5.0dB

  - improve verbose logging: number of files are written to the
     info log

  - improve performance: check first whether the output file
     exists before calculating the volume levels + not modifying
     the file if the adjustment < 0.5dB (level is never exactly 0)

* Update README, fixes #11. [Werner Robitza]


## v0.1.3 (2015-12-15)

* Check for Windows .exe, fixes #10. [Werner Robitza]

* Check path and fix #9. [Werner Robitza]

* Merge pull request #8 from benjaoming/master. [Werner Robitza]

  Add MANIFEST.in

* Bump version. [Benjamin Bach]

* Add manifest to include missing files in sdist. [Benjamin Bach]

* Merge pull request #6 from jetpks/master. [Werner Robitza]

  Fixed ffmpeg v2.6.3 compatibility and docopt config

* Updated to work with ffmpeg v2.6.3, and fixed broken docopt config. [Eric Jacobs]

  ffmpeg update:

  ffmpeg v2.6.3 puts mean_volume on stderr instead of stdout, causing
  `output` in `ffmpeg_get_mean` to be completely empty, and no match for
  mean_volume or max_volume to be found.

  Fixed by adding `stderr=subprocess.PIPE` in both Popen calls in
  `run_command`, and combining stdout and stderr on return. We already
  exit with non-zero return, so combining stderr/stdout shouldn't cause
  any poor side-effects.

  docopt config:

  - args['--level'] was not recognizing its default because there was
    an errant comma between -l and --level, and it needed <level> after
    the arguments.
  - Fixed spacing for --max
  - Removed quotes around 'normalized' so single quote characters don't
    end up in the output file names.

* Removed Windows carraige returns from __main__.py. [Eric Jacobs]

* Merge pull request #5 from mvbattista/master. [Werner Robitza]

  Installation update to ffmpeg

* Installation update to ffmpeg. [Michael V. Battista]

* Update to ffmpeg. [Werner Robitza]

* Update HISTORY.rst. [Werner Robitza]

* Update to ffmpeg. [Werner Robitza]

* Merge pull request #4 from benjaoming/rename. [Werner Robitza]

  Rename project

* Make at least one file mandatory. [Benjamin Bach]

* Rename project and remove pyc file. [Benjamin Bach]

* Merge pull request #2 from benjaoming/docopt-setuptools-avconv. [Werner Robitza]

  Docopt, Setuptools, avconv compatibility

* Use docopt. [Benjamin Bach]

* Use normalize-audio when using avconv because it doesn't have a way to measure volume. [Benjamin Bach]

* Functional setup.py, communicate with avconv/ffmpeg about overwriting. [Benjamin Bach]

* Also detect avconv. [Benjamin Bach]

* Use a main function instead. [Benjamin Bach]

* Add a history for the project. [Benjamin Bach]

* Move to more unique module name. [Benjamin Bach]

* Update README.rst. [benjaoming]

* Change the README to rst (PyPi) [Benjamin Bach]

* Delete .gitignore. [Werner Robitza]

* Update README.md. [Werner Robitza]

* Various improvements, fixes #1. [Werner Robitza]

* License. [Werner Robitza]

* Livense. [Werner Robitza]

* Update README.md. [Werner]

* Merge branch 'master' of https://github.com/slhck/audio-normalize. [Werner Robitza]

* Initial commit. [Werner]

* Initial commit. [Werner Robitza]


