# Audio Filters

Audio filters allow you to modify the audio signal before or after normalization. You can specify audio filters using the `-prf` / `--pre-audio-filter` and `-pof` / `--post-audio-filter` options.
The available filters correspond to the filters provided by FFmpeg. See the [FFmpeg audio filters documentation](https://ffmpeg.org/ffmpeg-filters.html#Audio-Filters) for a complete list of available filters and their options.

Here are some examples of audio filters.

## Dynamic normalization

You can use pre-filters to modify the audio signal before or after it is normalized, e.g. by using dynamic compression. This smooths out any volume differences in the signal.

Examples for low, mid, and high dynamic compression:

```bash
ffmpeg-normalize test.wav -prf "dynaudnorm=p=0.9:s=0"
ffmpeg-normalize test.wav -prf "dynaudnorm=p=0.5:s=5"
ffmpeg-normalize test.wav -prf "dynaudnorm=p=0.3:s=15"
```

## Denoising

Apply a denoiser, e.g. `anlmdn`. This removes background white noise, for example.

Examples for low, mid, and high denoising:

```bash
ffmpeg-normalize test.wav -prf "anlmdn=s=0.0001:p=0.1:m=15"
ffmpeg-normalize test.wav -prf "anlmdn=s=0.0001:p=0.01:m=15"
ffmpeg-normalize test.wav -prf "anlmdn=s=0.001:p=0.01:m=15"
```

You can combine this with dynamic audio compression, of course:

```bash
ffmpeg-normalize test.wav -prf "anlmdn=s=0.001:p=0.01:m=15,dynaudnorm=p=0.3:s=15"
```

## High-pass filtering

Remove low rumbling noise:

```bash
ffmpeg-normalize test.wav -prf "highpass=f=100"
```
