FROM python:3.13-slim as base

FROM base as builder
RUN mkdir /ffmpeg
WORKDIR /ffmpeg

# Install wget and xz-utils for downloading and extracting FFmpeg
RUN apt-get update && apt-get install -y wget xz-utils && rm -rf /var/lib/apt/lists/*

# Detect architecture and download appropriate FFmpeg build
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        FFMPEG_ARCH="linux64"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        FFMPEG_ARCH="linuxarm64"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-${FFMPEG_ARCH}-gpl.tar.xz && \
    tar -xf ffmpeg-master-latest-${FFMPEG_ARCH}-gpl.tar.xz -C /ffmpeg --strip-components=1

FROM base
COPY --from=builder /ffmpeg/bin/ffmpeg /usr/local/bin
COPY --from=builder /ffmpeg/bin/ffprobe /usr/local/bin
RUN pip3 install ffmpeg-normalize
RUN chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe

ENTRYPOINT ["ffmpeg-normalize"]
