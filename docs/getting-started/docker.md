# Docker Usage

You can use the pre-built image from Docker Hub:

```bash
docker run -v "$(pwd):/tmp" -it slhck/ffmpeg-normalize
```

Alternatively, download this repository and run

```bash
docker build -t ffmpeg-normalize .
```

Then run the container with:

```bash
docker run  -v "$(pwd):/tmp" -it ffmpeg-normalize
```

This will mount your current directory to the `/tmp` directory inside the container. Everything else works the same way as if you had installed the program locally. For example, to normalize a file:

```bash
docker run  -v "$(pwd):/tmp" -it ffmpeg-normalize /tmp/yourfile.mp4 -o /tmp/yourfile-normalized.wav
```

You will then find the normalized file in your current directory.
