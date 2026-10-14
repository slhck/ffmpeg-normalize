# API

This program has a simple API that can be used to integrate it into other Python programs.

The API docs are [available here](https://htmlpreview.github.io/?https://github.com/slhck/ffmpeg-normalize/blob/master/docs-api/ffmpeg_normalize.html).

## Custom Environment Variables

If you need to pass custom environment variables to ffmpeg (e.g., for setting `LD_LIBRARY_PATH` or other runtime configuration), use the `ffmpeg_env` context manager:

```python
import os
from ffmpeg_normalize import FFmpegNormalize, ffmpeg_env

# Create a custom environment with additional variables
custom_env = os.environ.copy()
custom_env["LD_LIBRARY_PATH"] = "/custom/lib/path"

# Run normalization with custom environment
with ffmpeg_env(custom_env):
    normalizer = FFmpegNormalize()
    normalizer.add_media_file("input.mp4", "output.mp4")
    normalizer.run_normalization()
```

The context manager is thread-safe (uses `contextvars`), so concurrent normalizations in different threads can use different environments.

## Before/After Summary

After `run_normalization()`, `get_summary()` returns one entry per audio stream with the input level, output level, output peak and applied gain in dB, along with the file names, stream index and status. `format_summary()` returns the same data as the table printed by `--print-summary`.

```python
from ffmpeg_normalize import FFmpegNormalize

normalizer = FFmpegNormalize(normalization_type="rms", target_level=-20)
normalizer.add_media_file("input.wav", "output.wav")
normalizer.run_normalization()

for row in normalizer.get_summary():
    print(row["input_file"], row["input_level"], row["output_level"], row["gain"])

print(normalizer.format_summary())
```

Values that are not available (for example, EBU output values in a dry run) are `None`. Pass `print_summary=True` to print the table to stderr at the end of `run_normalization()`.
