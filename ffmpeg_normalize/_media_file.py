from __future__ import annotations

import logging
import os
import re
import shlex
from shutil import move, rmtree
from tempfile import mkdtemp
from typing import TYPE_CHECKING, Iterable, Iterator, Literal, TypedDict

from tqdm import tqdm

from ._cmd_utils import DUR_REGEX, CommandRunner
from ._errors import FFmpegNormalizeError
from ._streams import (
    AudioStream,
    LoudnessStatisticsWithMetadata,
    SubtitleStream,
    VideoStream,
)

if TYPE_CHECKING:
    from ffmpeg_normalize import FFmpegNormalize

_logger = logging.getLogger(__name__)

# Note: this does not contain MP3, see https://github.com/slhck/ffmpeg-normalize/issues/246
# We may need to remove other formats as well, to be checked.
AUDIO_ONLY_FORMATS = {"aac", "ast", "flac", "mka", "oga", "ogg", "opus", "wav"}
ONE_STREAM = {"aac", "ast", "flac", "mp3", "wav"}

TQDM_BAR_FORMAT = "{desc}: {percentage:3.2f}% |{bar}{r_bar}"


def _to_ms(**kwargs: str) -> int:
    hour = int(kwargs.get("hour", 0))
    minute = int(kwargs.get("min", 0))
    sec = int(kwargs.get("sec", 0))
    ms = int(kwargs.get("ms", 0))

    return (hour * 60 * 60 * 1000) + (minute * 60 * 1000) + (sec * 1000) + ms


class StreamDict(TypedDict):
    audio: dict[int, AudioStream]
    video: dict[int, VideoStream]
    subtitle: dict[int, SubtitleStream]


class MediaFile:
    """
    Class that holds a file, its streams and adjustments
    """

    def __init__(
        self, ffmpeg_normalize: FFmpegNormalize, input_file: str, output_file: str
    ):
        """
        Initialize a media file for later normalization by parsing the streams.

        Args:
            ffmpeg_normalize (FFmpegNormalize): reference to overall settings
            input_file (str): Path to input file
            output_file (str): Path to output file
        """
        self.ffmpeg_normalize = ffmpeg_normalize
        self.skip = False
        self.input_file = input_file
        self.output_file = output_file
        current_ext = os.path.splitext(output_file)[1][1:]
        # we need to check if it's empty, e.g. /dev/null or NUL
        if current_ext == "" or self.output_file == os.devnull:
            self.output_ext = self.ffmpeg_normalize.extension
        else:
            self.output_ext = current_ext
        self.streams: StreamDict = {"audio": {}, "video": {}, "subtitle": {}}

        self.parse_streams()

    def _stream_ids(self) -> list[int]:
        """
        Get all stream IDs of this file.

        Returns:
            list: List of stream IDs
        """
        return (
            list(self.streams["audio"].keys())
            + list(self.streams["video"].keys())
            + list(self.streams["subtitle"].keys())
        )

    def __repr__(self) -> str:
        return os.path.basename(self.input_file)

    def parse_streams(self) -> None:
        """
        Try to parse all input streams from file and set them in self.streams.

        Raises:
            FFmpegNormalizeError: If no audio streams are found
        """
        _logger.debug(f"Parsing streams of {self.input_file}")

        cmd = [
            self.ffmpeg_normalize.ffmpeg_exe,
            "-i",
            self.input_file,
            "-c",
            "copy",
            "-t",
            "0",
            "-map",
            "0",
            "-f",
            "null",
            os.devnull,
        ]

        output = CommandRunner().run_command(cmd).get_output()

        _logger.debug("Stream parsing command output:")
        _logger.debug(output)

        output_lines = [line.strip() for line in output.split("\n")]

        duration = None
        for line in output_lines:
            if "Duration" in line:
                if duration_search := DUR_REGEX.search(line):
                    duration = _to_ms(**duration_search.groupdict()) / 1000
                    _logger.debug(f"Found duration: {duration} s")
                else:
                    _logger.warning("Could not extract duration from input file!")

            if not line.startswith("Stream"):
                continue

            if stream_id_match := re.search(r"#0:([\d]+)", line):
                stream_id = int(stream_id_match.group(1))
                if stream_id in self._stream_ids():
                    continue
            else:
                continue

            if "Audio" in line:
                _logger.debug(f"Found audio stream at index {stream_id}")
                sample_rate_match = re.search(r"(\d+) Hz", line)
                sample_rate = (
                    int(sample_rate_match.group(1)) if sample_rate_match else None
                )
                bit_depth_match = re.search(r"[sfu](\d+)(p|le|be)?", line)
                bit_depth = int(bit_depth_match.group(1)) if bit_depth_match else None
                self.streams["audio"][stream_id] = AudioStream(
                    self.ffmpeg_normalize,
                    self,
                    stream_id,
                    sample_rate,
                    bit_depth,
                    duration,
                )

            elif "Video" in line:
                _logger.debug(f"Found video stream at index {stream_id}")
                self.streams["video"][stream_id] = VideoStream(
                    self.ffmpeg_normalize, self, stream_id
                )

            elif "Subtitle" in line:
                _logger.debug(f"Found subtitle stream at index {stream_id}")
                self.streams["subtitle"][stream_id] = SubtitleStream(
                    self.ffmpeg_normalize, self, stream_id
                )

        if not self.streams["audio"]:
            raise FFmpegNormalizeError(
                f"Input file {self.input_file} does not contain any audio streams"
            )

        if (
            self.output_ext.lower() in ONE_STREAM
            and len(self.streams["audio"].values()) > 1
        ):
            _logger.warning(
                "Output file only supports one stream. Keeping only first audio stream."
            )
            first_stream = list(self.streams["audio"].values())[0]
            self.streams["audio"] = {first_stream.stream_id: first_stream}
            self.streams["video"] = {}
            self.streams["subtitle"] = {}

    def run_normalization(self, pass_=None) -> None:
        """
        Run the normalization process for this file.
        """

        if pass_ == 1:
            # run the first pass to get loudness stats
            _logger.debug(f"Running first pass for {self.input_file}")
            self._first_pass()
            return

        if pass_ == 2:
            # run the second pass as a whole
            _logger.debug(f"Running second pass for {self.input_file}")
            if self.ffmpeg_normalize.progress:
                with tqdm(total=100, position=1, desc="Second Pass") as pbar:
                    for progress in self._second_pass():
                        pbar.update(progress - pbar.n)
            else:
                for _ in self._second_pass():
                    pass

            return

        _logger.debug(f"Running normalization for {self.input_file}")

        # run the first pass to get loudness stats
        self._first_pass()

        # no. this would only work in async code
        """
        if self.ffmpeg_normalize.batch:
            # TODO
            # wait for all files to finish their first pass
            # then average all first passes
            # dual_mono
        """

        # run the second pass as a whole
        if self.ffmpeg_normalize.progress:
            with tqdm(
                total=100,
                position=1,
                desc="Second Pass",
                bar_format=TQDM_BAR_FORMAT,
            ) as pbar:
                for progress in self._second_pass():
                    pbar.update(progress - pbar.n)
        else:
            for _ in self._second_pass():
                pass

    def _can_write_output_video(self) -> bool:
        """
        Determine whether the output file can contain video at all.

        Returns:
            bool: True if the output file can contain video, False otherwise
        """
        if self.output_ext.lower() in AUDIO_ONLY_FORMATS:
            return False

        return not self.ffmpeg_normalize.video_disable

    def _first_pass(self) -> None:
        """
        Run the first pass of the normalization process.
        """
        _logger.debug(f"Parsing normalization info for {self.input_file}")

        for index, audio_stream in enumerate(self.streams["audio"].values()):
            if self.ffmpeg_normalize.normalization_type == "ebu":
                fun = getattr(audio_stream, "parse_loudnorm_stats")
            else:
                fun = getattr(audio_stream, "parse_astats")

            if self.ffmpeg_normalize.progress:
                with tqdm(
                    total=100,
                    position=1,
                    desc=f"Stream {index + 1}/{len(self.streams['audio'].values())}",
                    bar_format=TQDM_BAR_FORMAT,
                ) as pbar:
                    for progress in fun():
                        pbar.update(progress - pbar.n)
            else:
                for _ in fun():
                    pass

    def _get_audio_filter_cmd(self) -> tuple[str, list[str]]:
        """
        Return the audio filter command and output labels needed.

        Returns:
            tuple[str, list[str]]: filter_complex command and the required output labels
        """
        filter_chains = []
        output_labels = []

        for audio_stream in self.streams["audio"].values():
            skip_normalization = False
            if self.ffmpeg_normalize.lower_only:
                if self.ffmpeg_normalize.normalization_type == "ebu":
                    if (
                        audio_stream.loudness_statistics["ebu_pass1"] is not None
                        and audio_stream.loudness_statistics["ebu_pass1"]["input_i"]
                        < self.ffmpeg_normalize.target_level
                    ):
                        skip_normalization = True
                elif self.ffmpeg_normalize.normalization_type == "peak":
                    if (
                        audio_stream.loudness_statistics["max"] is not None
                        and audio_stream.loudness_statistics["max"]
                        < self.ffmpeg_normalize.target_level
                    ):
                        skip_normalization = True
                elif self.ffmpeg_normalize.normalization_type == "rms":
                    if (
                        audio_stream.loudness_statistics["mean"] is not None
                        and audio_stream.loudness_statistics["mean"]
                        < self.ffmpeg_normalize.target_level
                    ):
                        skip_normalization = True

            if skip_normalization:
                _logger.warning(
                    f"Stream {audio_stream.stream_id} had measured input loudness lower than target, skipping normalization."
                )
                normalization_filter = "acopy"
            else:
                if self.ffmpeg_normalize.normalization_type == "ebu":
                    normalization_filter = audio_stream.get_second_pass_opts_ebu()
                else:
                    normalization_filter = audio_stream.get_second_pass_opts_peakrms()

            input_label = f"[0:{audio_stream.stream_id}]"
            output_label = f"[norm{audio_stream.stream_id}]"
            output_labels.append(output_label)

            filter_chain = []

            if self.ffmpeg_normalize.pre_filter:
                filter_chain.append(self.ffmpeg_normalize.pre_filter)

            filter_chain.append(normalization_filter)

            if self.ffmpeg_normalize.post_filter:
                filter_chain.append(self.ffmpeg_normalize.post_filter)

            filter_chains.append(input_label + ",".join(filter_chain) + output_label)

        filter_complex_cmd = ";".join(filter_chains)

        return filter_complex_cmd, output_labels

    def _second_pass(self) -> Iterator[float]:
        """
        Construct the second pass command and run it.

        FIXME: make this method simpler
        """
        _logger.info(f"Running second pass for {self.input_file}")

        # get the target output stream types depending on the options
        output_stream_types: list[Literal["audio", "video", "subtitle"]] = ["audio"]
        if self._can_write_output_video():
            output_stream_types.append("video")
        if not self.ffmpeg_normalize.subtitle_disable:
            output_stream_types.append("subtitle")

        # base command, here we will add all other options
        cmd = [self.ffmpeg_normalize.ffmpeg_exe, "-hide_banner", "-y"]

        # extra options (if any)
        if self.ffmpeg_normalize.extra_input_options:
            cmd.extend(self.ffmpeg_normalize.extra_input_options)

        # get complex filter command
        audio_filter_cmd, output_labels = self._get_audio_filter_cmd()

        # add input file and basic filter
        cmd.extend(["-i", self.input_file, "-filter_complex", audio_filter_cmd])

        # map metadata, only if needed
        if self.ffmpeg_normalize.metadata_disable:
            cmd.extend(["-map_metadata", "-1"])
        else:
            # map global metadata
            cmd.extend(["-map_metadata", "0"])
            # map per-stream metadata (e.g. language tags)
            for stream_type in output_stream_types:
                stream_key = stream_type[0]
                if stream_type not in self.streams:
                    continue
                for idx, _ in enumerate(self.streams[stream_type].items()):
                    cmd.extend(
                        [
                            f"-map_metadata:s:{stream_key}:{idx}",
                            f"0:s:{stream_key}:{idx}",
                        ]
                    )

        # map chapters if needed
        if self.ffmpeg_normalize.chapters_disable:
            cmd.extend(["-map_chapters", "-1"])
        else:
            cmd.extend(["-map_chapters", "0"])

        # collect all '-map' and codecs needed for output video based on input video
        if self.streams["video"]:
            if self._can_write_output_video():
                for s in self.streams["video"].keys():
                    cmd.extend(["-map", f"0:{s}"])
                # set codec (copy by default)
                cmd.extend(["-c:v", self.ffmpeg_normalize.video_codec])
            else:
                if not self.ffmpeg_normalize.video_disable:
                    _logger.warning(
                        f"The chosen output extension {self.output_ext} does not support video/cover art. It will be disabled."
                    )

        # ... and map the output of the normalization filters
        for ol in output_labels:
            cmd.extend(["-map", ol])

        # set audio codec (never copy)
        if self.ffmpeg_normalize.audio_codec:
            cmd.extend(["-c:a", self.ffmpeg_normalize.audio_codec])
        else:
            for index, (_, audio_stream) in enumerate(self.streams["audio"].items()):
                cmd.extend([f"-c:a:{index}", audio_stream.get_pcm_codec()])

        # other audio options (if any)
        if self.ffmpeg_normalize.audio_bitrate:
            if self.ffmpeg_normalize.audio_codec == "libvorbis":
                # libvorbis takes just a "-b" option, for some reason
                # https://github.com/slhck/ffmpeg-normalize/issues/277
                cmd.extend(["-b", str(self.ffmpeg_normalize.audio_bitrate)])
            else:
                cmd.extend(["-b:a", str(self.ffmpeg_normalize.audio_bitrate)])
        if self.ffmpeg_normalize.sample_rate:
            cmd.extend(["-ar", str(self.ffmpeg_normalize.sample_rate)])
        if self.ffmpeg_normalize.audio_channels:
            cmd.extend(["-ac", str(self.ffmpeg_normalize.audio_channels)])

        # ... and subtitles
        if not self.ffmpeg_normalize.subtitle_disable:
            for s in self.streams["subtitle"].keys():
                cmd.extend(["-map", f"0:{s}"])
            # copy subtitles
            cmd.extend(["-c:s", "copy"])

        if self.ffmpeg_normalize.keep_original_audio:
            highest_index = len(self.streams["audio"])
            for index, _ in enumerate(self.streams["audio"].items()):
                cmd.extend(["-map", f"0:a:{index}"])
                cmd.extend([f"-c:a:{highest_index + index}", "copy"])

        # extra options (if any)
        if self.ffmpeg_normalize.extra_output_options:
            cmd.extend(self.ffmpeg_normalize.extra_output_options)

        # output format (if any)
        if self.ffmpeg_normalize.output_format:
            cmd.extend(["-f", self.ffmpeg_normalize.output_format])

        # if dry run, only show sample command
        if self.ffmpeg_normalize.dry_run:
            cmd.append(self.output_file)
            _logger.warning("Dry run used, not actually running second-pass command")
            CommandRunner(dry=True).run_command(cmd)
            yield 100
            return

        # special case: if output is a null device, write directly to it
        if self.output_file == os.devnull:
            cmd.append(self.output_file)
        else:
            temp_dir = mkdtemp()
            temp_file = os.path.join(temp_dir, f"out.{self.output_ext}")
            cmd.append(temp_file)

        cmd_runner = CommandRunner()
        try:
            try:
                yield from cmd_runner.run_ffmpeg_command(cmd)
            except Exception as e:
                _logger.error(
                    f"Error while running command {shlex.join(cmd)}! Error: {e}"
                )
                raise e
            else:
                if self.output_file != os.devnull:
                    _logger.debug(
                        f"Moving temporary file from {temp_file} to {self.output_file}"
                    )
                    move(temp_file, self.output_file)
                    rmtree(temp_dir, ignore_errors=True)
        except Exception as e:
            if self.output_file != os.devnull:
                rmtree(temp_dir, ignore_errors=True)
            raise e

        output = cmd_runner.get_output()
        # in the second pass, we do not normalize stream-by-stream, so we set the stats based on the
        # overall output (which includes multiple loudnorm stats)
        if self.ffmpeg_normalize.normalization_type == "ebu":
            all_stats = AudioStream.prune_and_parse_loudnorm_output(output)
            for stream_id, audio_stream in self.streams["audio"].items():
                if stream_id in all_stats:
                    audio_stream.set_second_pass_stats(all_stats[stream_id])

        # warn if self.media_file.ffmpeg_normalize.dynamic == False and any of the second pass stats contain "normalization_type" == "dynamic"
        if self.ffmpeg_normalize.dynamic is False:
            for audio_stream in self.streams["audio"].values():
                pass2_stats = audio_stream.get_stats()["ebu_pass2"]
                if pass2_stats is None:
                    continue
                if pass2_stats["normalization_type"] == "dynamic":
                    _logger.warning(
                        "You specified linear normalization, but the loudnorm filter reverted to dynamic normalization. "
                        "This may lead to unexpected results."
                        "Consider your input settings, e.g. choose a lower target level or higher target loudness range."
                    )

        _logger.debug("Normalization finished")

    def get_stats(self) -> Iterable[LoudnessStatisticsWithMetadata]:
        return (
            audio_stream.get_stats() for audio_stream in self.streams["audio"].values()
        )
