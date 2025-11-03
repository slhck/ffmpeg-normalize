# Using Presets

Presets allow you to save and reuse common configurations for different use cases. Instead of specifying the same options every time, you can create a preset file and reference it with `--preset`.

## Overview

A preset is a JSON file containing a set of ffmpeg-normalize options. When you use `--preset <name>`, the options from the preset file are applied to your command. Any options you specify on the command line take precedence over the preset values.

Presets are stored in a platform-specific configuration directory.

### Linux/macOS

By default:
```
~/.config/ffmpeg-normalize/presets/
```

If you have `XDG_CONFIG_HOME` set:
```
$XDG_CONFIG_HOME/ffmpeg-normalize/presets/
```

### Windows

```
%APPDATA%\ffmpeg-normalize\presets\
```

## Built-in Presets

ffmpeg-normalize comes with three built-in presets:

### `podcast`

Optimized for podcast audio normalization using the [AES recommended standard](https://www.aes.org/technical/documents/AESTD1004_1_15_10.pdf).

- Normalization type: EBU R128
- Target level: -16 LUFS
- Loudness range target: 7.0 LUFS
- True peak: -2.0 dBTP

### `music`

Optimized for music album normalization. Preserves relative loudness between tracks using RMS-based normalization in batch mode for consistent loudness across albums.

- Normalization type: RMS
- Target level: -20.0 dB
- Batch mode: enabled (preserves relative loudness between tracks)

### `streaming-video`

Optimized for video streaming platforms with the standard loudness level for video content.

- Normalization type: EBU R128
- Target level: -14.0 LUFS
- Loudness range target: 7.0 LUFS
- True peak: -2.0 dBTP

## Using Presets

To see all available presets:

```bash
ffmpeg-normalize --list-presets
```

To apply a preset to your files:

```bash
ffmpeg-normalize input.mp3 --preset podcast
```

This will automatically apply all options defined in the `podcast` preset to your command.

CLI options take precedence over preset values. For example, to use the podcast preset but with a different output codec:

```bash
ffmpeg-normalize input.mp3 --preset podcast --audio-codec libmp3lame
```

The `--audio-codec` option will then override the preset's codec choice.

## Creating Custom Presets

You can create your own presets by creating a JSON file in your presets directory.
A preset file is a simple JSON object with option names as keys and their values:

```json
{
  "normalization-type": "ebu",
  "target-level": -23.0,
  "loudness-range-target": 7.0,
  "true-peak": -2.0,
  "audio-codec": "aac",
  "audio-bitrate": "192k",
  "progress": true
}
```

Use the long form of option names (with hyphens) in presets. Examples:

- `normalization-type` (not `-nt`)
- `target-level` (not `-t`)
- `audio-codec` (not `-c:a`)
- `audio-bitrate` (not `-b:a`)
- `sample-rate` (not `-ar`)
- `audio-channels` (not `-ac`)
- `loudness-range-target` (not `-lrt`)
- `true-peak` (not `-tp`)

Boolean options should be `true` in the JSON:

```json
{
  "progress": true,
  "batch": true
}
```

Note: It's not required to include options that are `false` because they are the default.

### Example: Custom Voice Preset

Create a file `~/.config/ffmpeg-normalize/presets/voice.json`:

```json
{
  "normalization-type": "ebu",
  "target-level": -18.0,
  "loudness-range-target": 4.0,
  "true-peak": -3.0,
  "audio-codec": "libopus",
  "audio-bitrate": "96k",
  "audio-channels": 1,
  "progress": true,
  "verbose": true
}
```

Then use it:

```bash
ffmpeg-normalize voice_recording.wav --preset voice
```

### Example: Custom Streaming Audio Preset

Create a file `~/.config/ffmpeg-normalize/presets/streaming-audio.json`:

```json
{
  "normalization-type": "ebu",
  "target-level": -14.0,
  "loudness-range-target": 7.0,
  "true-peak": -2.0,
  "audio-codec": "aac",
  "audio-bitrate": "192k",
  "progress": true
}
```

This preset normalizes audio to the streaming video standard and encodes it as AAC at 192 kbps.
