FROM python:3.12.0a7-alpine3.17 as base

FROM base as builder
RUN mkdir /ffmpeg
WORKDIR /ffmpeg
RUN wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
RUN tar -xf ffmpeg-release-amd64-static.tar.xz -C /ffmpeg --strip-components=1

FROM base
COPY --from=builder /ffmpeg/ffmpeg /usr/local/bin
COPY --from=builder /ffmpeg/ffprobe /usr/local/bin
RUN pip3 install ffmpeg-normalize
RUN chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe
