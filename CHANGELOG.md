# Changelog


## v1.21.1 (2021-03-05)

* Adjusted handling of FFMPEG_PATH for binaries available via $PATH (#149)

  * adjusted handling of FFMPEG_PATH for binaries available via $PATH

  fixes #147

  * adjusted use of %s to {} to match style

  * documented the feature

  * condensed error message as other lines are longer


## v1.21.0 (2021-02-27)

* Fix JSON output for multiple files.

* Update badge URL.

* Update README.md (#142)

  * Update README.md

  Added example of verifying levels

  Fixes #141

  * shorten example, add link to wiki page

* Error if no ffmpeg exec exists.

* Add stalebot.


## v1.20.2 (2020-11-06)

* Fixing stdin corruption caused by new subprocess (#138)

* Update issue template.

* Create FUNDING.yml.

* Fix usage, addresses #132.


## v1.20.1 (2020-07-22)

* Manually specify usage string, fixes #132.

* Fix local import for tests.


## v1.20.0 (2020-07-04)

* Add extra input options.


## v1.19.1 (2020-06-25)

* Add colorama to requirements, fixes #131.

* Fix warning that is printed with default options.


## v1.19.0 (2020-05-02)

* Fix issue with output folder, fixes #126.

* Fix typo in README's table of contents link to "File Input/Output". (#124)

* Clarify readme, fixes #122.


## v1.18.2 (2020-04-19)

* Add warning for automatic sample rate conversion, addresses #122.

* Ignore vscode folder.

* Fix printing of errors in conversion.


## v1.18.1 (2020-04-16)

* Fix unit tests.

* Improve handling of output file folder and errors.

* Clarify usage of output options, add warning.

* Improve documentation, fixes #120.

* Do not include bump messages in changelog.


## v1.18.0 (2020-04-13)

* Use measured offset in second pass, fixes #119.

* Update release instructions.

* Remove author names from changelog.


## v1.17.0 (2020-04-10)

* Update release script and changelog template.

* Apply pre-filters in all first passes, fixes #118.

  This allows properly reading the level for any kind of normalization, even if
  filters affect the loudness in the first pass.


## v1.16.0 (2020-04-07)

* Add all commits to changelog.

* Remove python 2 support.

* Add quiet option, fixes #116.

  - Add a new quiet option
  - Promote some warnings to actual errors that need to be shown
  - Add a very basic test case


## v1.15.8 (2020-03-15)

* Improve release script.

* Python 3.8.


## v1.15.7 (2020-03-14)

* Only print length warning for non-EBU type normalization.


## v1.15.6 (2019-12-04)

* Remove build and dist folder on release.

* Do not exit on error in batch processing.

  Simply process the next file if one has errors, addresses #110.


## v1.15.5 (2019-11-19)

* Use minimal dependency for tqdm.

* Remove specific python version requirement.


## v1.15.4 (2019-11-19)

* Freeze tqdm version.

* Update python to 3.7.

* Improve release documentation.


## v1.15.3 (2019-10-15)

* Do not print stream warning when there is only one stream.

* Remove previous dist versions before release.


## v1.15.2 (2019-07-12)

* Warn when duration cannot be read, fixes #105.

* Update README.

  minor improvements in the description


## v1.15.1 (2019-06-17)

* Add output to unit test failures.

* Fix input label for audio stream.


## v1.15.0 (2019-06-17)

* Add pre-and post-filter hooks, fixes #67.

  This allows users to specify filters to be run before or after the actual
  normalization call, using regular ffmpeg syntax.
  Only applies to audio.

* Document audiostream class.

* Warn when file is too short, fixes #87.

* Update release method to twine.


## v1.14.1 (2019-06-14)

* Handle progress output from ffmpeg, fixes #10.

* Merge pull request #99 from Nottt/patch-1.

  fix -cn description

* Fix -cn description.

* Add nicer headers for options in README.


## v1.14.0 (2019-04-24)

* Add version file in release script before committing.

* Add option to keep original audio, fixes #83.

* Add pypi badge.

* Allow release script to add changelog for future version; upload to pypi.


## v1.13.11 (2019-04-16)

* Add release script.

* Add small developer guide on releasing.

* Move HISTORY.md to CHANGELOG.md.

* Fix ffmpeg static build download location.


## v1.3.10 (2019-02-22)

* Bump version.

* Cap measured input loudness, fixes #92.


## v1.3.9 (2019-01-10)

* Bump version.

* Fix handling of errors with tqdm.

* Improve readme.

* Delete issue template.

* Bump version.

* Clarify extra argument options, move to main entry point.

* Update issue templates.


## v1.3.8 (2018-11-28)

* Bump version.

* Clarify extra argument options, move to main entry point.


## v1.3.7 (2018-10-28)

* Bump version.

* Copy metadata from individual streams, fixes #86.

* Add python version for pyenv.


## v1.3.6 (2018-07-09)

* Bump version.

* Update README, fixes #79 and addresses #80.


## v1.3.5 (2018-06-12)

* Bump version.

* Minor README updates.

* Fix documentation of TMPDIR parameter.


## v1.3.4 (2018-05-05)

* Bump version.

* New way to specify extra options.


## v1.3.3 (2018-05-05)

* Update README.

* Decode strings in extra options.


## v1.3.2 (2018-04-25)

* Bump version.

* Merge pull request #69 from UbiCastTeam/master.

  Stderror decoding ignoring utf8 encoding errors

* Stderror decoding ignoring utf8 encoding errors.


## v1.3.1 (2018-04-24)

* Bump version.

* Do not require main module in setup.py, fixes #68.


## v1.3.0 (2018-04-15)

* Bump version.

* Remove dead code.

* Fix for python2 division.

* Update documentation.

* Progress bar.

* Remove imports from test file.

* Fix travis file.

* WIP: progress bar.

* Minor typo in option group.

* Add simple unit test for disabling chapters.


## v1.2.3 (2018-04-11)

* Fix unit test.

* Bump version.

* Add option to disable chapters, fixes #65, also fix issue with metadata.


## v1.2.2 (2018-04-10)

* Bump version.

* Set default loudness target to -23, fixes #48.


## v1.2.1 (2018-04-04)

* Bump version.

* Merge pull request #64 from UbiCastTeam/encoding-issue.

  Stdout and stderror decoding ignoring utf8 encoding errors

* Stdout and stderror decoding ignoring utf8 encoding errors.


## v1.2.0 (2018-03-22)

* Bump version.

* Add errors for impossible format combinations, fixes #60.

* Fix ordering of output maps, fixes #63.

* Improve documentation.


## v1.1.0 (2018-03-06)

* Add option to print first pass statistics.


## v1.0.10 (2018-03-04)

* Bump version.

* Restrict parsing to valid JSON part only, fixes #61.

* Add an example for MP3 encoding.

* Update paypal link.


## v1.0.9 (2018-02-08)

* Bump version.

* Add normalized folder to gitignore.

* Do not print escape sequences on Windows.

* Do not check for file existence, fixes #57.

* Add github issue template.


## v1.0.8 (2018-02-01)

* Bump version.

* Do not check for ffmpeg upon module import.


## v1.0.7 (2018-02-01)

* Bump version.

* Rename function test.

* Fix issue with wrong adjustment parameters, fixes #54.


## v1.0.6 (2018-01-30)

* Allow setting FFMPEG_PATH and document TMP.


## v1.0.5 (2018-01-26)

* Handle edge case for short input clips.


## v1.0.4 (2018-01-26)

* Bump version.

* Do not try to remove nonexisting file in case of error in command.


## v1.0.3 (2018-01-26)

* Bump version.

* Always streamcopy when detecting streams to avoid initializing encoder.

* Fix handling of temporary file.

* Add build status.

* Travis tests.


## v1.0.2 (2018-01-25)

* Fix bug with target level for peak/RMS.

* Update documentation formatting.

* Update history.


## v1.0.1 (2018-01-24)

* Bump version.

* Set default target to -23.


## v1.0.0 (2018-01-23)

* Add version info and test case for dry run.

* New feature detection, add documentation, contributors guide etc.

* WIP: v1.0 rewrite.


## v0.7.3 (2017-10-09)

* Use shutil.move instead of os.rename.


## v0.7.2 (2017-09-17)

* Allow setting threshold to 0.


## v0.7.1 (2017-09-14)

* Bump version.

* Update HISTORY.md.

* Merge pull request #37 from Mathijsz/fix-which-path-expansion.

  expand tilde and environment variables, fixes #36

* Expand tilde and environment variables, fixes #36.

* Update HISTORY.md.

* Update README w.r.t. loudnorm filter.

* Update README and indentation.


## v0.7.0 (2017-08-02)

* Bump version.

* Fix handling of extra options with spaces.

* Include test script.

* Logging and other improvements.

* Add test files.

* Autopep8 that thing.

* Logger improvements.

* Add example for overwriting.


## v0.6.0 (2017-07-31)

* Allow overwriting input file, fixes #22.

* Version bump.

* Better handle cmd arguments.

* Update README.md.

  add another example


## v0.5.1 (2017-04-04)

* Fix for problem introduced in 304e8df.


## v0.5 (2017-04-02)

* Fix pypi topics.

* Bump version and README.

* Fix issue where output was wrong format.

* Add EBU R128 filter.

* Use Markdown instead of RST for README/HISTORY.

* Define file encode for python3, fixes #24.

* Fix history.

* Fix option -np.

* Clarify merge option.

* Minor documentation improvements.

  - change README from CRLF to LF
  - add "attenuated" in description
  - extend LICENSE year
  - add license to main README


## v0.4.1 (2017-02-13)

* Update for release.

* Merge pull request #21 from mpuels/patch-1.

  Fix for #13

* Fix for #13.

* Mention Python 3.

  mention that Python 3 may work, just didn't have time to test

* Fix README's code blocks.


## v0.4 (2017-01-24)

* Code cleanup, add option to set format and audio codec.


## v0.3 (2017-01-19)

* Add option for no prefix, fixes #20.

* Handle multiple spaces in path; fixes issue #18.

* Handle spaces in path, fixes #12.

* Update README.rst.

* Change default level back  to -26.

* Typo in README example.

* Update documentation.

* Bump to v0.2.0.

  * Support for multiple files and output directories.
  * Support merging of audio with input file
  * Set audio codec and additional options
  * User-definable threshold
  * Better error handling and logging
  * Deprecates avconv

* Change default level back to -28.

* Merge pull request #15 from auricgoldfinger/master.

  Add extended normalisation options

* Add extended normalisation options.

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

* Update README, fixes #11.


## v0.1.3 (2015-12-15)

* Check for Windows .exe, fixes #10.

* Check path and fix #9.

* Merge pull request #8 from benjaoming/master.

  Add MANIFEST.in

* Bump version.

* Add manifest to include missing files in sdist.

* Merge pull request #6 from jetpks/master.

  Fixed ffmpeg v2.6.3 compatibility and docopt config

* Updated to work with ffmpeg v2.6.3, and fixed broken docopt config.

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

* Removed Windows carraige returns from __main__.py.

* Merge pull request #5 from mvbattista/master.

  Installation update to ffmpeg

* Installation update to ffmpeg.

* Update to ffmpeg.

* Update HISTORY.rst.

* Update to ffmpeg.

* Merge pull request #4 from benjaoming/rename.

  Rename project

* Make at least one file mandatory.

* Rename project and remove pyc file.

* Merge pull request #2 from benjaoming/docopt-setuptools-avconv.

  Docopt, Setuptools, avconv compatibility

* Use docopt.

* Use normalize-audio when using avconv because it doesn't have a way to measure volume.

* Functional setup.py, communicate with avconv/ffmpeg about overwriting.

* Also detect avconv.

* Use a main function instead.

* Add a history for the project.

* Move to more unique module name.

* Update README.rst.

* Change the README to rst (PyPi)

* Delete .gitignore.

* Update README.md.

* Various improvements, fixes #1.

* License.

* Livense.

* Update README.md.

* Merge branch 'master' of https://github.com/slhck/audio-normalize.

* Initial commit.

* Initial commit.


