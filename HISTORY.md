# History

0.7.2 (2017-09-17)
------------------

- Allow setting threshold to 0 to always normalize file, see #38

0.7.1 (2017-09-14)
------------------

- Fix for expanding variables in `$PATH`

0.7.0 (2017-08-02)
------------------

- Internal code cleanup
- Add more examples
- Add simple test suite

0.6.0 (2017-07-31)
------------------

- Allow overwriting input file

0.5.2 (2017-07-31)
------------------

- Improve command-line handling

0.5.1 (2017-04-04)
------------------

- Fix --merge/-u option not working

0.5 (2017-04-02)
----------------

- Add new EBU R128 normalization filter
- Fix issue with output file extension not being WAV by default
- Fix issue #24 where setup.py fails on Windows / Python 3.6

0.4.3 (2017-02-27)
------------------

-   Fix option `-np`, should be `-x` short
-   Abort when input and output file are the same (ffmpeg can't
    overwrite it)

0.4.2 (2017-02-27)
------------------

-   Map metadata from input to output when merging
-   Clarify use of merge option

0.4.1 (2017-02-13)
------------------

-   Fix #13

0.4 (2017-01-24)
----------------

-   Cleanup in code, make it class-based
-   Drop avconv support, it was never good anyway
-   Add support for specifying codec for non-merging operations
-   Add support for specifying output format
-   README improvements

0.3 (2017-01-19)
----------------

-   Add option to remove prefix

0.2.4 (2016-10-27)
------------------

-   Fixed issue where multiple spaces were collapsed into one

0.2.3 (2016-02-12)
------------------

-   Fixed issue where ffmpeg could not be found if path included spaces

0.2.2 (2016-02-09)
------------------

-   Change default level back to -26

0.2.1 (2016-02-08)
------------------

-   Documentation fixes

0.2.0 (2016-02-08)
------------------

-   Support multiple input files
-   Allow merging with input file instead of creating separate WAV
-   Write to directory instead of using prefix
-   Set the audio codec when merging
-   Set additional encoder or ffmpeg options

Note: avconv support is very limited, use the real ffmpeg from
<http://ffmpeg.org/> instead.

0.1.3 (2015-12-15)
------------------

-   Bugfix for detecting ffmpeg or avconv on Windows (as .exe)
-   Add version to Usage message
-   Update year

0.1.2 (2015-11-13)
------------------

-   Bugfix for missing ffmpeg or avconv

0.1.0 (2015-08-01)
------------------

-   First release, changing name to ffmpeg-normalize

