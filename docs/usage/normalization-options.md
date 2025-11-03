# Normalization Options

Here are some more examples on how to use different normalization options with `ffmpeg-normalize`.

If you've made it this far, you probably want to understand more about the EBU R128 normalization method and its options, so please read on below.

## What options should I choose for the EBU R128 filter? What is linear and dynamic mode?

EBU R128 is a method for normalizing audio loudness across different tracks or programs. It works by analyzing the audio content and adjusting it to meet specific loudness targets. The main components are:

* Integrated Loudness (I): The overall loudness of the entire audio.
* Loudness Range (LRA): The variation in loudness over time.
* True Peak (TP): The maximum level of the audio signal.

The normalization process involves measuring these values (input) and then applying gain adjustments to meet target levels (output), typically -23 LUFS for integrated loudness. You can also specify a target loudness range (LRA) and true peak level (TP).

**Linear mode** applies a constant gain adjustment across the entire audio file. This is generally preferred because:

* It preserves the original dynamic range of the audio.
* It maintains the relative loudness between different parts of the audio.
* It avoids potential artifacts or pumping effects that can occur with dynamic processing.

**Dynamic mode**, on the other hand, can change the volume dynamically throughout the file. While this can achieve more consistent loudness, it may alter the original artistic intent. There were some bugs in older versions of the `loudnorm` filter that could cause artifacts, but these have been fixed in recent versions of ffmpeg.

For most cases, linear mode is recommended. Dynamic mode should only be used when linear mode is not suitable or when a specific effect is desired. In some cases, `loudnorm` will still fall back to dynamic mode, and a warning will be printed to the console. Here's when this can happen:

* When the input loudness range (LRA) is larger than the target loudness range: If the input file has a loudness range that exceeds the specified loudness range target, the loudnorm filter will automatically switch to dynamic mode. This is because linear normalization alone cannot reduce the loudness range without dynamic processing (limiting). The `--keep-loudness-range-target` option can be used to keep the input loudness range target above the specified target.

* When the required gain adjustment to meet the integrated loudness target would result in the true peak exceeding the specified true peak limit. This is because linear processing alone cannot reduce peaks without affecting the entire signal. For example, if a file needs to be amplified by 6 dB to reach the target integrated loudness, but doing so would push the true peak above the specified limit, the filter might switch to dynamic mode to handle this situation. If your content allows for it, you can increase the true peak target to give more headroom for linear processing. If you're consistently running into true peak issues, you might also consider lowering your target integrated loudness level.

At this time, the `loudnorm` filter in ffmpeg does not provide a way to force linear mode when the input loudness range exceeds the target or when the true peak would be exceeded. There are some options to mitigate this:

- The `--keep-lra-above-loudness-range-target` option can be used to keep the input loudness range above the specified target, but it will not force linear mode in all cases.
- Similarly, the `--keep-loudness-range-target` option can be used to keep the input loudness range target.
- The `--lower-only` option can be used to skip the normalization pass completely if the measured loudness is lower than the target loudness.

If instead you want to use dynamic mode, you can use the `--dynamic` option; this will also speed up the normalization process because only one pass is needed.

## When to use peak versus RMS normalization

R128 normalizaion may not always be the best choice for every situation due to the complex settings, so peak/RMS are valid alternatives.

Peak normalization simply looks at the loudest single point in your audio and scales everything so that this peak hits your target level (usually 0 dB). It doesn't account for the perceived loudness of the audio though. You might end up with audio that technically peaks at the right level but sounds much quieter than you'd expect because there was one short peak that you normalized to, but the majority of the file was more quiet. This approach is useful when you have technical requirements to prevent clipping or when working with audio that needs strict headroom for downstream processing.

RMS (root mean square) normalization, on the other hand, measures the average loudness of the audio over time and normalizes based on that. This means the resulting audio will sound more consistently loud compared to other files normalized with the same settings. RMS is generally better for most audio work because it aligns with how our ears perceive loudness. It's particularly useful when you're normalizing a batch of files that need to sound similar in volume relative to each other. However, RMS normalization may introduce clipping if there are sudden peaks in the audio that exceed the target level after normalization. In such cases, adding a compressor before normalization, or a peak limiter after normalization can help manage these peaks; see [audio filters](audio-filters.md) for some examples.

## Perform peak normalization

To use simple peak normalization to 0 dB:

```bash
ffmpeg-normalize test.wav --normalization-type peak --target-level 0 --output normalized.wav
ffmpeg-normalize test.wav -nt peak -t 0 -o normalized.wav
```

## Perform RMS-based normalization

RMS-based normalization can be done like this:

```bash
ffmpeg-normalize test.wav --normalization-type rms --target-level -20 --output normalized.wav
ffmpeg-normalize test.wav -nt rms -t -20 -o normalized.wav
```

## Extra options for the ffmpeg command

If you need some fancy extra options, such as setting `vbr` for the `libfdk_aac` encoder, pass them to the `-e`/`--extra-options` argument:

```bash
ffmpeg-normalize input.m4a -c:a libfdk_aac -e='-vbr 3' -o output.m4a
```

You can pass any valid ffmpeg options this way. These are applied to the output command after the normalization filter.

If you need extra *input* options, use `-ei`/`--extra-input-options`:

```bash
ffmpeg-normalize <INPUT> -ei="-f mpegts -r 24" -o output.mkv
```

This sets everything *before+ the input file, which ffmpeg may need to parse the input properly.

## Check the loudness statistics

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

## Changing the loudness range

By specifying a different loudness range target (`-lrt`), you can change the dynamics of the EBU R128 normalization. For more info about loudness range, see [this page](https://www.masteringthemix.com/pages/mixing-with-levels#LoudnessRange).

The default is 7, but by setting a lower value, you can "squeeze" the signal more:

```bash
ffmpeg-normalize test/test.wav -lrt 1
```
