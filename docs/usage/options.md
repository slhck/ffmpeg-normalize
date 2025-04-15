# Detailed Options

## File Input/Output

- `input`: Input media file(s)

- `-o OUTPUT [OUTPUT ...], --output OUTPUT [OUTPUT ...]`: Output file names.

    Will be applied per input file.

    If no output file name is specified for an input file, the output files
    will be written to the default output folder with the name `<input>.<ext>`, where `<ext>` is the output extension (see `-ext` option).

    Example: `ffmpeg-normalize 1.wav 2.wav -o 1n.wav 2n.wav`

- `-of OUTPUT_FOLDER, --output-folder OUTPUT_FOLDER`: Output folder (default: `normalized`)

    This folder will be used for input files that have no explicit output name specified.

## General

- `-f, --force`: Force overwrite existing files

- `-d, --debug`: Print debugging output

- `-v, --verbose`: Print verbose output

- `-q, --quiet`: Only print errors

- `-n, --dry-run`: Do not run normalization, only print what would be done

- `-pr`, `--progress`: Show progress bar for files and streams

- `--version`: Print version and exit

## Normalization

- `-nt {ebu,rms,peak}, --normalization-type {ebu,rms,peak}`: Normalization type (default: `ebu`).

    EBU normalization performs two passes and normalizes according to EBU R128.

    RMS-based normalization brings the input file to the specified RMS level.

    Peak normalization brings the signal to the specified peak level.

- `-t TARGET_LEVEL, --target-level TARGET_LEVEL`: Normalization target level in dB/LUFS (default: -23).

    For EBU normalization, it corresponds to Integrated Loudness Target in LUFS. The range is -70.0 - -5.0.

    Otherwise, the range is -99 to 0.

- `-p, --print-stats`: Print loudness statistics for both passes formatted as JSON to stdout.

- `--replaygain`: Write [ReplayGain](https://en.wikipedia.org/wiki/ReplayGain) tags to the original file without normalizing.

    This mode will overwrite the input file and ignore other options.

    Only works with EBU normalization, and only with .mp3, .mp4/.m4a, .ogg, .opus for now.

## EBU R128 Normalization

- `-lrt LOUDNESS_RANGE_TARGET, --loudness-range-target LOUDNESS_RANGE_TARGET`: EBU Loudness Range Target in LUFS (default: 7.0).

    Range is 1.0 - 50.0.

- `--keep-loudness-range-target`: Keep the input loudness range target to allow for linear normalization.

- `--keep-lra-above-loudness-range-target`: Keep input loudness range above loudness range target.

    Can be used as an alternative to `--keep-loudness-range-target` to allow for linear normalization.

- `-tp TRUE_PEAK, --true-peak TRUE_PEAK`: EBU Maximum True Peak in dBTP (default: -2.0).

    Range is -9.0 - +0.0.

- `--offset OFFSET`: EBU Offset Gain (default: 0.0).

    The gain is applied before the true-peak limiter in the first pass only. The offset for the second pass will be automatically determined based on the first pass statistics.

    Range is -99.0 - +99.0.

- `--lower-only`: Whether the audio should not increase in loudness.

    If the measured loudness from the first pass is lower than the target loudness then normalization pass will be skipped for the measured audio source.

- `--auto-lower-loudness-target`: Automatically lower EBU Integrated Loudness Target.

    Automatically lower EBU Integrated Loudness Target to prevent falling back to dynamic filtering.

    Makes sure target loudness is lower than measured loudness minus peak loudness (input_i - input_tp) by a small amount.

- `--dual-mono`: Treat mono input files as "dual-mono".

    If a mono file is intended for playback on a stereo system, its EBU R128 measurement will be perceptually incorrect. If set, this option will compensate for this effect. Multi-channel input files are not affected by this option.

- `--dynamic`: Force dynamic normalization mode.

    Instead of applying linear EBU R128 normalization, choose a dynamic normalization. This is not usually recommended.

    Dynamic mode will automatically change the sample rate to 192 kHz. Use `-ar`/`--sample-rate` to specify a different output sample rate.

## Audio Encoding

- `-c:a AUDIO_CODEC, --audio-codec AUDIO_CODEC`: Audio codec to use for output files.

    See `ffmpeg -encoders` for a list.

    Will use PCM audio with input stream bit depth by default.

- `-b:a AUDIO_BITRATE, --audio-bitrate AUDIO_BITRATE`: Audio bitrate in bits/s, or with K suffix.

    If not specified, will use codec default.

- `-ar SAMPLE_RATE, --sample-rate SAMPLE_RATE`: Audio sample rate to use for output files in Hz.

    Will use input sample rate by default, except for EBU normalization, which will change the input sample rate to 192 kHz.

- `-ac`, `--audio-channels`: Set the number of audio channels. If not specified, the input channel layout will be used. This is equivalent to `-ac` in ffmpeg.

- `-koa, --keep-original-audio`: Copy original, non-normalized audio streams to output file

- `-prf PRE_FILTER, --pre-filter PRE_FILTER`: Add an audio filter chain before applying normalization.

    Multiple filters can be specified by comma-separating them.

- `-pof POST_FILTER, --post-filter POST_FILTER`: Add an audio filter chain after applying normalization.

    Multiple filters can be specified by comma-separating them.

    For EBU, the filter will be applied during the second pass.

## Other Encoding Options

- `-vn, --video-disable`: Do not write video streams to output

- `-c:v VIDEO_CODEC, --video-codec VIDEO_CODEC`: Video codec to use for output files (default: 'copy').

    See `ffmpeg -encoders` for a list.

    Will attempt to copy video codec by default.

- `-sn, --subtitle-disable`: Do not write subtitle streams to output

- `-mn, --metadata-disable`: Do not write metadata to output

- `-cn, --chapters-disable`: Do not write chapters to output

## Input/Output Format

- `-ei EXTRA_INPUT_OPTIONS, --extra-input-options EXTRA_INPUT_OPTIONS`: Extra input options list.

    A list of extra ffmpeg command line arguments valid for the input, applied before ffmpeg's `-i`.

    You can either use a JSON-formatted list (i.e., a list of comma-separated, quoted elements within square brackets), or a simple string of space-separated arguments.

    If JSON is used, you need to wrap the whole argument in quotes to prevent shell expansion and to preserve literal quotes inside the string. If a simple string is used, you need to specify the argument with `-e=`.

    Examples: `-ei '[ "-f", "mpegts", "-r", "24" ]'` or `-ei="-f mpegts -r 24"`

- `-e EXTRA_OUTPUT_OPTIONS, --extra-output-options EXTRA_OUTPUT_OPTIONS`: Extra output options list.

    A list of extra ffmpeg command line arguments valid for the output.

    You can either use a JSON-formatted list (i.e., a list of comma-separated, quoted elements within square brackets), or a simple string of space-separated arguments.

    If JSON is used, you need to wrap the whole argument in quotes to prevent shell expansion and to preserve literal quotes inside the string. If a simple string is used, you need to specify the argument with `-e=`.

    Examples: `-e '[ "-vbr", "3", "-preset:v", "ultrafast" ]'` or `-e="-vbr 3 -preset:v ultrafast"`

- `-ofmt OUTPUT_FORMAT, --output-format OUTPUT_FORMAT`: Media format to use for output file(s).

    See `ffmpeg -formats` for a list.

    If not specified, the format will be inferred by ffmpeg from the output file name. If the output file name is not explicitly specified, the extension will govern the format (see '--extension' option).

- `-ext EXTENSION, --extension EXTENSION`: Output file extension to use for output files that were not explicitly specified. (Default: `mkv`)

## Environment Variables

The program additionally respects environment variables:

- `TMP` / `TEMP` / `TMPDIR`

    Sets the path to the temporary directory in which files are
    stored before being moved to the final output directory.
    Note: You need to use full paths.

- `FFMPEG_PATH`

    Sets the full path to an `ffmpeg` executable other than
    the system default or you can provide a file name available on $PATH
