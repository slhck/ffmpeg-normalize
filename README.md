# ffmpeg-normalize

[![PyPI version](https://img.shields.io/pypi/v/ffmpeg-normalize.svg)](https://pypi.org/project/ffmpeg-normalize)
[![Docker Image Version](https://img.shields.io/docker/v/slhck/ffmpeg-normalize?sort=semver&label=Docker%20image)](https://hub.docker.com/r/slhck/ffmpeg-normalize)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/slhck/ffmpeg-normalize/python-package.yml)

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-22-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

A utility for batch-normalizing audio using ffmpeg.

This program normalizes media files to a certain loudness level using the EBU R128 loudness normalization procedure. It can also perform RMS-based normalization (where the mean is lifted or attenuated), or peak normalization to a certain target level.

## ✨ Features

- EBU R128 loudness normalization — Two-pass by default, with an option for one-pass dynamic normalization
- RMS-based normalization — Adjust audio to a specific RMS level
- Peak normalization — Adjust audio to a specific peak level
- Selective audio stream normalization — Normalize specific audio streams or only default streams
- Video file support — Process video files while preserving video streams
- Docker support — Run via Docker container
- Python API — Use programmatically in your Python projects
- Shell completions — Available for bash, zsh, and fish
- Album Batch normalization – Process files jointly, preserving relative loudness

## 🚀 Quick Start

1. Install a recent version of [ffmpeg](https://ffmpeg.org/download.html)
2. Run `pip3 install ffmpeg-normalize` and `ffmpeg-normalize /path/to/your/file.mp4`, alternatively install [`uv`](https://docs.astral.sh/uv/getting-started/installation/) and run `uvx ffmpeg-normalize /path/to/your/file.mp4`
3. Done! 🎧 (the normalized file will be called `normalized/file.mkv`)


## 🆕 What's New

- Version 1.36.0 introduces **presets** with `--preset`! Save and reuse your favorite normalization configurations for different use cases. Comes with three built-in presets: `podcast` (AES standard), `music` (RMS-based batch normalization), and `streaming-video` (video content). Create custom presets too!

    Example:

    ```bash
    ffmpeg-normalize input.mp3 --preset podcast
    ```

    applies the podcast preset (EBU R128, -16 LUFS) to your file. Learn more in the [presets guide](https://slhck.info/ffmpeg-normalize/usage/presets/).

- Version 1.35.0 has **batch/album normalization** with `--batch`. It preserves relative loudness between files! Perfect for music albums where you want to shift all tracks by the same amount.

    Example:

    ```bash
    ffmpeg-normalize album/*.flac --batch -nt rms -t -20
    ```

    shifts the entire album so the average RMS is -20 dB, preserving the original relative loudness as mastered.

- Version 1.34.0 brings **selective audio stream normalization**! You can now:

  - Normalize specific audio streams with `-as/--audio-streams` (e.g., `-as 1,2` to normalize only streams 1 and 2)
  - Normalize only default audio streams with `--audio-default-only` (useful for files with multiple language tracks)
  - Keep other streams unchanged with `--keep-other-audio` (copy non-selected streams without normalization)

    Example:

    ```bash
    ffmpeg-normalize input.mkv -as 1 --keep-other-audio
    ```

    normalizes stream 1 and copies all other audio streams unchanged.

Other recent additions:

- **Shell completions** (v1.31.0) — Tab completion for bash, zsh, and fish shells. See the [installation guide](https://slhck.info/ffmpeg-normalize/getting-started/installation/#shell-completions) for setup instructions.
- **`--lower-only` option** — Prevent audio from increasing in loudness, only lower it if needed (works with all normalization types).

See the [full changelog](https://github.com/slhck/ffmpeg-normalize/blob/master/CHANGELOG.md) for all updates.

## 📓 Documentation

Check out our [documentation](https://slhck.info/ffmpeg-normalize/) for more info!

## 🤝 Contributors

The only reason this project exists in its current form is because [@benjaoming](https://github.com/slhck/ffmpeg-normalize/issues?q=is%3Apr+author%3Abenjaoming)'s initial PRs. Thanks for everyone's support!

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://overtag.dk/"><img src="https://avatars.githubusercontent.com/u/374612?v=4?s=100" width="100px;" alt="Benjamin Balder Bach"/><br /><sub><b>Benjamin Balder Bach</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=benjaoming" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://chaos.social/@eleni"><img src="https://avatars.githubusercontent.com/u/511547?v=4?s=100" width="100px;" alt="Eleni Lixourioti"/><br /><sub><b>Eleni Lixourioti</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=Geekfish" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/thenewguy"><img src="https://avatars.githubusercontent.com/u/77731?v=4?s=100" width="100px;" alt="thenewguy"/><br /><sub><b>thenewguy</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=thenewguy" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/aviolo"><img src="https://avatars.githubusercontent.com/u/560229?v=4?s=100" width="100px;" alt="Anthony Violo"/><br /><sub><b>Anthony Violo</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=aviolo" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://jacobs.af/"><img src="https://avatars.githubusercontent.com/u/952830?v=4?s=100" width="100px;" alt="Eric Jacobs"/><br /><sub><b>Eric Jacobs</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=jetpks" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/kostalski"><img src="https://avatars.githubusercontent.com/u/34033008?v=4?s=100" width="100px;" alt="kostalski"/><br /><sub><b>kostalski</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=kostalski" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://justinppearson.com/"><img src="https://avatars.githubusercontent.com/u/8844823?v=4?s=100" width="100px;" alt="Justin Pearson"/><br /><sub><b>Justin Pearson</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=justinpearson" title="Code">💻</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Nottt"><img src="https://avatars.githubusercontent.com/u/13532436?v=4?s=100" width="100px;" alt="ad90xa0-aa"/><br /><sub><b>ad90xa0-aa</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=Nottt" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/Mathijsz"><img src="https://avatars.githubusercontent.com/u/1891187?v=4?s=100" width="100px;" alt="Mathijs"/><br /><sub><b>Mathijs</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=Mathijsz" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/mpuels"><img src="https://avatars.githubusercontent.com/u/2924816?v=4?s=100" width="100px;" alt="Marc Püls"/><br /><sub><b>Marc Püls</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=mpuels" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://www.mvbattista.com/"><img src="https://avatars.githubusercontent.com/u/158287?v=4?s=100" width="100px;" alt="Michael V. Battista"/><br /><sub><b>Michael V. Battista</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=mvbattista" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://auto-editor.com"><img src="https://avatars.githubusercontent.com/u/57511737?v=4?s=100" width="100px;" alt="WyattBlue"/><br /><sub><b>WyattBlue</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=WyattBlue" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/g3n35i5"><img src="https://avatars.githubusercontent.com/u/17593457?v=4?s=100" width="100px;" alt="Jan-Frederik Schmidt"/><br /><sub><b>Jan-Frederik Schmidt</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=g3n35i5" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/mjhalwa"><img src="https://avatars.githubusercontent.com/u/8994014?v=4?s=100" width="100px;" alt="mjhalwa"/><br /><sub><b>mjhalwa</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=mjhalwa" title="Code">💻</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/07416"><img src="https://avatars.githubusercontent.com/u/14923168?v=4?s=100" width="100px;" alt="07416"/><br /><sub><b>07416</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=07416" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/sian1468"><img src="https://avatars.githubusercontent.com/u/58017832?v=4?s=100" width="100px;" alt="sian1468"/><br /><sub><b>sian1468</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=sian1468" title="Tests">⚠️</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/psavva"><img src="https://avatars.githubusercontent.com/u/1454758?v=4?s=100" width="100px;" alt="Panayiotis Savva"/><br /><sub><b>Panayiotis Savva</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=psavva" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/HighMans"><img src="https://avatars.githubusercontent.com/u/42877729?v=4?s=100" width="100px;" alt="HighMans"/><br /><sub><b>HighMans</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=HighMans" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/kanjieater"><img src="https://avatars.githubusercontent.com/u/32607317?v=4?s=100" width="100px;" alt="kanjieater"/><br /><sub><b>kanjieater</b></sub></a><br /><a href="#ideas-kanjieater" title="Ideas, Planning, & Feedback">🤔</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://ahmetsait.com/"><img src="https://avatars.githubusercontent.com/u/8372246?v=4?s=100" width="100px;" alt="Ahmet Sait"/><br /><sub><b>Ahmet Sait</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=ahmetsait" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/georgev93"><img src="https://avatars.githubusercontent.com/u/39860568?v=4?s=100" width="100px;" alt="georgev93"/><br /><sub><b>georgev93</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=georgev93" title="Code">💻</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://davidbern.com/"><img src="https://avatars.githubusercontent.com/u/371066?v=4?s=100" width="100px;" alt="David Bern"/><br /><sub><b>David Bern</b></sub></a><br /><a href="https://github.com/slhck/ffmpeg-normalize/commits?author=odie5533" title="Code">💻</a></td>
    </tr>
  </tbody>
  <tfoot>
    <tr>
      <td align="center" size="13px" colspan="7">
        <img src="https://raw.githubusercontent.com/all-contributors/all-contributors-cli/1b8533af435da9854653492b1327a23a4dbd0a10/assets/logo-small.svg">
          <a href="https://all-contributors.js.org/docs/en/bot/usage">Add your contributions</a>
        </img>
      </td>
    </tr>
  </tfoot>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->
