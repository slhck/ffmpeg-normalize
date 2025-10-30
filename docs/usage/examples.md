# Examples

## File Input/Output

### Normalize multiple files

Normalize two WAV files and write them to the specified output files with uncompressed PCM WAV as audio codec:

```bash
ffmpeg-normalize file1.wav file2.wav -o file1-normalized.wav file2-normalized.wav
```

### Overwrite the input file

You can (if you really need to!) also overwrite your input file. Warning, this will destroy data:

```bash
ffmpeg-normalize input.mp4 -o input.mp4 -f
```

### Normalize videos, compress audio

Normalize a number of videos in the current folder and write them to a folder called `normalized`, converting all audio streams to AAC with 192 kBit/s.

```bash
ffmpeg-normalize *.mkv -c:a aac -b:a 192k
```

### Use Windows loops for multiple files

For Windows CMD (Batch), the above would be written as a loop:

```bat
for %i in (*.mkv) do ffmpeg-normalize "%i" -c:a aac -b:a 192k
```

With PowerShell:

```powershell
ls *.mkv | ForEach-Object { ffmpeg-normalize $_.FullName -c:a aac -b:a 192k }
```

### Create an MP3 file as output

Normalize an MP3 file and write an MP3 file (you have to explicitly specify the encoder):

```bash
ffmpeg-normalize input.mp3 -c:a libmp3lame -b:a 320k -o output.mp3
```

### Change the output container from the default (MKV)

Normalize many files, keeping PCM audio, but choosing a different container:

```bash
ffmpeg-normalize *.wav -c:a pcm_s16le -ext aif
```

## Normalization Options

### Perform peak normalization

Instead of EBU R128, one might just want to use simple peak normalization to 0 dB:

```bash
ffmpeg-normalize test.wav --normalization-type peak --target-level 0 --output normalized.wav
ffmpeg-normalize test.wav -nt peak -t 0 -o normalized.wav
```

### Extra options

If you need some fancy extra options, such as setting `vbr` for the `libfdk_aac` encoder, pass them to the `-e`/`--extra-options` argument:

```bash
ffmpeg-normalize input.m4a -c:a libfdk_aac -e='-vbr 3' -o output.m4a
```

### Check the loudness statistics

You can check the statistics of a file to verify the levels with `-p`. Pass `-n` to avoid running the normalization:

```bash
ffmpeg-normalize test/test.wav -p -n -f
```

This will return a valid JSON object:

```json
[
{
    "input_file": "test/test.wav",
    "output_file": "normalized/test.mkv",
    "stream_id": 0,
    "ebu": {
        "input_i": -39.77,
        "input_tp": -27.49,
        "input_lra": 2.1,
        "input_thresh": -49.82,
        "output_i": -22.15,
        "output_tp": -9.46,
        "output_lra": 2.1,
        "output_thresh": -32.24,
        "normalization_type": "dynamic",
        "target_offset": -0.85
    },
    "mean": null,
    "max": null
}
]
```

### Changing the loudness range

By specifying a different loudness range target (`-lrt`), you can change the dynamics of the EBU R128 normalization. For more info about loudness range, see [this page](https://www.masteringthemix.com/pages/mixing-with-levels#LoudnessRange).

The default is 7, but by setting a lower value, you can "squeeze" the signal more:

```bash
ffmpeg-normalize test/test.wav -lrt 1
```

### Album/Batch Normalization

When normalizing an album or collection of tracks, you typically want to shift all files by the same amount rather than normalizing each file independently. This is where batch mode comes in.

```bash
# Recommended: RMS-based album normalization
# Shifts entire album to average RMS of -20 dB
ffmpeg-normalize album/*.flac --batch -nt rms -t -20 -c:a flac

# Or peak-based album normalization
# Shifts entire album so average peak is at -1 dB
ffmpeg-normalize album/*.wav --batch -nt peak -t -1 -c:a pcm_s16le
```

Best practices for album normalization:

- Use RMS (`-nt rms`) for most music albums
- Use Peak (`-nt peak`) if you want to avoid any clipping
- Set a reasonable target level (e.g., `-t -20` for RMS, `-t -1` for peak)
- Use lossless codecs (FLAC, WAV) to preserve quality

**What about clipping?**

When using RMS batch normalization, the same gain adjustment is applied to all tracks. This means some tracks might clip if they have higher peaks than average.

For example:
- Album average RMS: -26 dB
- Target RMS: -20 dB
- Adjustment needed: +6 dB (applied to all tracks)
- Track A has peak at -1 dB → after +6 dB = **+5 dB** → ⚠️ Clipping!
- Track B has peak at -8 dB → after +6 dB = -2 dB → ✅ No clipping

The program will **warn you** for each track that will clip:
```
WARNING: Adjusting will lead to clipping of 5.0 dB
```

**How to avoid clipping:**

1. **Use Peak normalization instead** - guarantees no clipping:
   ```bash
   ffmpeg-normalize album/*.flac --batch -nt peak -t -1 -c:a flac
   ```

2. **Use a more conservative RMS target** - leave more headroom:
   ```bash
   ffmpeg-normalize album/*.flac --batch -nt rms -t -23 -c:a flac  # More conservative
   ```

3. **Accept minor clipping** - if clipping is < 0.5 dB, it may be inaudible in most cases

4. **Pre-process with a limiter** - use `--pre-filter` to apply limiting before normalization:
   ```bash
   ffmpeg-normalize album/*.flac --batch -nt rms -t -20 -prf "alimiter=limit=0.99" -c:a flac
   ```

## Filters

### Dynamic normalization

You can use pre-filters to modify the audio signal before or after it is normalized, e.g. by using dynamic compression. This smooths out any volume differences in the signal.

Examples for low, mid, and high dydnamic compression:

```bash
ffmpeg-normalize test.wav -prf "dynaudnorm=p=0.9:s=0"
ffmpeg-normalize test.wav -prf "dynaudnorm=p=0.5:s=5"
ffmpeg-normalize test.wav -prf "dynaudnorm=p=0.3:s=15"
```

### Denoising

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

### High-pass filtering

Remove low rumbling noise:

```bash
ffmpeg-normalize test.wav -prf "highpass=f=100"
```
