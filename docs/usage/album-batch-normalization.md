# Album/Batch Normalization

When normalizing an album or collection of tracks, you typically want to shift all files by the same amount rather than normalizing each file independently. This is where batch mode comes in. Batch normalization means shifting all tracks by the same gain amount – just like turning up or down the volume.

Music albums are already mastered with the correct relative loudness between tracks, so you want to preserve this exactly.

!!! question "Why RMS or Peak? Why not EBU?"

    While EBU batch mode works, it's **not recommended for albums** because EBU normalization applies different processing to each track based on its perceived loudness characteristics. This can alter the carefully balanced relative loudness between tracks that the mixing engineer intended.

    In contrast, RMS and Peak normalization apply a uniform gain adjustment across all tracks, preserving the original album's dynamics. See [this discussion](https://github.com/slhck/ffmpeg-normalize/issues/145) for more details.

## How it works (RMS/Peak)

1. ffmpeg-normalize will analyze all files (first pass)
2. It will calculate the average RMS or the highest sample peak across the selected audio streams
3. A single gain adjustment needed to reach the target is calculated; RMS gain is reduced if necessary to keep all measured sample peaks at or below 0 dBFS
4. The same adjustment is applied to all selected streams, preserving relative loudness

With `--lower-only`, the shared gain is capped at 0 dB. This applies to the album as a whole, so quieter tracks are still attenuated when the album needs to be turned down.

For example, if an album's average RMS is -26 dB, and the target is -20 dB, the program will calculate a +6 dB adjustment and apply it to all tracks equally, rather than normalizing each track to -20 dB individually. This will make relatively louder tracks louder, and vice-versa.

## Usage Examples

```bash
# Recommended: RMS-based album normalization
# Shifts entire album to average RMS of -20 dB
ffmpeg-normalize album/*.flac --batch -nt rms -t -20

# Or peak-based album normalization
# Shifts entire album so its highest sample peak is at -1 dBFS
ffmpeg-normalize album/*.wav --batch -nt peak -t -1
```

## Windows Usage

On Windows, wildcards like `*.flac` are not expanded by the shell. Use one of these approaches instead:

With PowerShell (recommended):

```powershell
ffmpeg-normalize (Get-ChildItem album\*.flac).FullName --batch -nt rms -t -20
```

With an input list:

```bat
dir /b album\*.flac > filelist.txt
ffmpeg-normalize --input-list filelist.txt --batch -nt rms -t -20
```

!!! warning

    Do **not** use a CMD `for` loop with `--batch`. The loop runs `ffmpeg-normalize` once per file, so batch mode has no effect — each file is normalized independently.

## Best Practices

- Use RMS (`-nt rms`) for most music albums
- Use Peak (`-nt peak`) if you want to avoid any clipping
- Set a reasonable target level (e.g., `-t -20` for RMS, `-t -1` for peak)
- Use lossless codecs (FLAC, WAV) to preserve quality

## What about clipping?

Peak batch normalization uses the highest measured sample peak across the album as its reference. For example, if two tracks peak at -1 and -11 dBFS and the target is -1 dBFS, both receive 0 dB gain. Their peaks remain -1 and -11 dBFS.

RMS batch normalization targets the average RMS level but reduces the shared gain when necessary to avoid sample clipping. For example:

- Album average RMS: -26 dB
- Target RMS: -20 dB
- Requested gain: +6 dB
- Highest input sample peak: -1 dBFS
- Applied gain: +1 dB to every track

The program warns that the requested RMS target cannot be reached. Reducing the gain for the entire album preserves the relative levels without applying a limiter.

These limits use sample peaks measured during analysis. Lossy encoding, resampling, and post-filters can change the final peaks; this is not a true-peak guarantee. Use EBU normalization when you need a true-peak target.
