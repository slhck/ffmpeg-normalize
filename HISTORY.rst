.. :changelog:

History
-------

0.4.1 (2017-02-13)
__________________

* Fix #13

0.4 (2017-01-24)
__________________

* Cleanup in code, make it class-based
* Drop avconv support, it was never good anyway
* Add support for specifying codec for non-merging operations
* Add support for specifying output format
* README improvements

0.3 (2017-01-19)
__________________

* Add option to remove prefix

0.2.4 (2016-10-27)
__________________

* Fixed issue where multiple spaces were collapsed into one

0.2.3 (2016-02-12)
__________________

* Fixed issue where ffmpeg could not be found if path included spaces

0.2.2 (2016-02-09)
__________________

* Change default level back to -26

0.2.1 (2016-02-08)
__________________

* Documentation fixes


0.2.0 (2016-02-08)
__________________

* Support multiple input files
* Allow merging with input file instead of creating separate WAV
* Write to directory instead of using prefix
* Set the audio codec when merging
* Set additional encoder or ffmpeg options

Note: avconv support is very limited, use the real ffmpeg from http://ffmpeg.org/ instead.

0.1.3 (2015-12-15)
__________________

* Bugfix for detecting ffmpeg or avconv on Windows (as .exe)
* Add version to Usage message
* Update year

0.1.2 (2015-11-13)
__________________

* Bugfix for missing ffmpeg or avconv


0.1.0 (2015-08-01)
__________________

* First release, changing name to ffmpeg-normalize
