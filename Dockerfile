FROM python:3.13-alpine as base

FROM base as builder
RUN mkdir /ffmpeg
WORKDIR /ffmpeg
RUN wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz
RUN tar -xf ffmpeg-master-latest-linux64-gpl.tar.xz -C /ffmpeg --strip-components=1

FROM base
COPY --from=builder /ffmpeg/bin/ffmpeg /usr/local/bin
COPY --from=builder /ffmpeg/bin/ffprobe /usr/local/bin
RUN pip3 install ffmpeg-normalize
RUN chmod +x /usr/local/bin/ffmpeg /usr/local/bin/ffprobe

ENTRYPOINT ["ffmpeg-normalize"]
