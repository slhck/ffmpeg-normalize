# Requirements

You need Python 3.9 or higher, and ffmpeg.

## ffmpeg

- ffmpeg 7.x is recommended, although it works with 5.x and above (these may contain already solved bugs with regard to loudness normalization)
- Download a [static build](https://ffmpeg.org/download.html) for your system
- Place the `ffmpeg` executable in your `$PATH`, or specify the path to the binary with the `FFMPEG_PATH` environment variable in `ffmpeg-normalize`

### Installation Examples

#### Linux

You can use the static build from [johnvansickle.com](https://johnvansickle.com/ffmpeg/releases/):

```bash
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
mkdir -p ffmpeg
tar -xf ffmpeg-release-amd64-static.tar.xz -C ffmpeg --strip-components=1
sudo cp ffmpeg/ffmpeg /usr/local/bin
sudo cp ffmpeg/ffprobe /usr/local/bin
sudo chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
```

!!! note
    Using distribution packages (e.g., `apt install ffmpeg`) is not recommended, as these are often outdated.

#### Windows

Follow [this guide](https://www.wikihow.com/Install-FFmpeg-on-Windows).

#### macOS and Linux (Homebrew)

You can use [Homebrew](https://brew.sh/) to install ffmpeg:

```bash
brew install ffmpeg
```

However, this might install a lot of dependencies and take some time. If you don't want to use Homebrew, you can use a static build from [evermeet.cx](https://evermeet.cx/ffmpeg/).
