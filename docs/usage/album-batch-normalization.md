# Album/Batch Normalization

When normalizing an album or collection of tracks, you typically want to shift all files by the same amount rather than normalizing each file independently. This is where batch mode comes in. Batch normalization means shifting all tracks by the same gain amount – just like turning up or down the volume.

Music albums are already mastered with the correct relative loudness between tracks, so you want to preserve this exactly.

!!! question "Why RMS or Peak? Why not EBU?"

    While EBU batch mode works, it's **not recommended for albums** because EBU normalization applies different processing to each track based on its perceived loudness characteristics. This can alter the carefully balanced relative loudness between tracks that the mixing engineer intended.

    In contrast, RMS and Peak normalization apply a uniform gain adjustment across all tracks, preserving the original album's dynamics. See [this discussion](https://github.com/slhck/ffmpeg-normalize/issues/145) for more details.

## How it works (RMS/Peak)

1. ffmpeg-normalize will analyze all files (first pass)
2. It will calculate the average RMS or peak across all tracks
3. A single gain adjustment needed to reach the target is calculated
4. The same adjustment is applied to all tracks

For example, if an album's average RMS is -26 dB, and the target is -20 dB, the program will calculate a +6 dB adjustment and apply it to all tracks equally, rather than normalizing each track to -20 dB individually. This will make relatively louder tracks louder, and vice-versa.

## Usage Examples

```bash
# Recommended: RMS-based album normalization
# Shifts entire album to average RMS of -20 dB
ffmpeg-normalize album/*.flac --batch -nt rms -t -20

# Or peak-based album normalization
# Shifts entire album so average peak is at -1 dB
ffmpeg-normalize album/*.wav --batch -nt peak -t -1
```

## Best Practices

- Use RMS (`-nt rms`) for most music albums
- Use Peak (`-nt peak`) if you want to avoid any clipping
- Set a reasonable target level (e.g., `-t -20` for RMS, `-t -1` for peak)
- Use lossless codecs (FLAC, WAV) to preserve quality

## What about clipping?

When using RMS batch normalization, the same gain adjustment is applied to all tracks. This means some tracks might clip if they have higher peaks than average.

For example:

- Album average RMS: -26 dB
- Target RMS: -20 dB
- Adjustment needed: +6 dB (applied to all tracks)
- Track A has peak at -1 dB → after +6 dB = **+5 dB** → ⚠️ Clipping!
- Track B has peak at -8 dB → after +6 dB = -2 dB → ✅ No clipping

The program will warn you for each track that will clip:

> `WARNING: Adjusting will lead to clipping of 5.0 dB`

There are different strategies to deal with this:

1. Use Peak normalization instead – guarantees no clipping:

      ```bash
      ffmpeg-normalize album/*.flac --batch -nt peak -t -1 -c:a flac
      ```

2. Use a more conservative RMS target – leave more headroom:

      ```bash
      ffmpeg-normalize album/*.flac --batch -nt rms -t -23 -c:a flac  # More conservative
      ```

3. Accept minor clipping – if clipping is < 0.5 dB, it may be inaudible in most cases

4. Pre-process with a limiter – use `--pre-filter` to apply limiting before normalization:

      ```bash
      ffmpeg-normalize album/*.flac --batch -nt rms -t -20 -prf "alimiter=limit=0.99" -c:a flac
      ```
