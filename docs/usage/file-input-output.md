# File Input/Output

Here are some examples of how to specify input and output files when using `ffmpeg-normalize`.

## Normalize multiple files

Normalize two WAV files and write them to the specified output files with uncompressed PCM WAV as audio codec:

```bash
ffmpeg-normalize file1.wav file2.wav -o file1-normalized.wav file2-normalized.wav
```

!!! tip

    If these are part of an album, you might want to use the [`--batch` option](normalization-options.md#albumbatch-normalization) to ensure consistent normalization across all files.

## Overwrite the input file

You can (if you really need to!) also overwrite your input file. Warning, this will destroy data:

```bash
ffmpeg-normalize input.mp4 -o input.mp4 -f
```

## Normalize videos, compress audio

Normalize a number of videos in the current folder and write them to a folder called `normalized`, converting all audio streams to AAC with 192 kBit/s.

```bash
ffmpeg-normalize *.mkv -c:a aac -b:a 192k
```

## Use Windows loops for multiple files

For Windows CMD (Batch), the above would be written as a loop:

```bat
for %i in (*.mkv) do ffmpeg-normalize "%i" -c:a aac -b:a 192k
```

With PowerShell:

```powershell
ls *.mkv | ForEach-Object { ffmpeg-normalize $_.FullName -c:a aac -b:a 192k }
```

## Create an MP3 file as output

Normalize an MP3 file and write an MP3 file (you have to explicitly specify the encoder):

```bash
ffmpeg-normalize input.mp3 -c:a libmp3lame -b:a 320k -o output.mp3
```

## Change the output container from the default (MKV)

Normalize many files, keeping PCM audio, but choosing a different container:

```bash
ffmpeg-normalize *.wav -c:a pcm_s16le -ext aif
```
