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
