from __future__ import annotations

import os
import re
import tempfile
import shutil
from tqdm import tqdm
import shlex
from typing import List, Tuple, TypedDict, TYPE_CHECKING

from ._streams import AudioStream, VideoStream, SubtitleStream
from ._errors import FFmpegNormalizeError
from ._cmd_utils import NUL, CommandRunner, DUR_REGEX, to_ms
from ._logger import setup_custom_logger

# types
if TYPE_CHECKING:
    from ffmpeg_normalize import FFmpegNormalize

logger = setup_custom_logger("ffmpeg_normalize")

AUDIO_ONLY_FORMATS = {"aac", "ast", "flac", "mp3", "mka", "oga", "ogg", "opus", "wav"}
ONE_STREAM = {"aac", "ast", "flac", "mp3", "wav"}

class StreamDict(TypedDict):
    audio: dict[int, AudioStream]
    video: dict[int, VideoStream]
    subtitle: dict[int, SubtitleStream]

class MediaFile:
    """
    Class that holds a file, its streams and adjustments
    """

    def __init__(self, ffmpeg_normalize: FFmpegNormalize, input_file: str, output_file: str):
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
        self.output_ext = os.path.splitext(output_file)[1][1:]
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
        logger.debug(f"Parsing streams of {self.input_file}")

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
            NUL,
        ]

        cmd_runner = CommandRunner(cmd)
        cmd_runner.run_command()
        output = cmd_runner.get_output()

        logger.debug("Stream parsing command output:")
        logger.debug(output)

        output_lines = [line.strip() for line in output.split("\n")]

        duration = None
        for line in output_lines:

            if "Duration" in line:
                duration_search = DUR_REGEX.search(line)
                if not duration_search:
                    logger.warning("Could not extract duration from input file!")
                else:
                    duration = duration_search.groupdict()
                    duration = to_ms(**duration) / 1000
                    logger.debug(f"Found duration: {duration} s")

            if not line.startswith("Stream"):
                continue

            stream_id_match = re.search(r"#0:([\d]+)", line)
            if stream_id_match:
                stream_id = int(stream_id_match.group(1))
                if stream_id in self._stream_ids():
                    continue
            else:
                continue

            if "Audio" in line:
                logger.debug(f"Found audio stream at index {stream_id}")
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
                logger.debug(f"Found video stream at index {stream_id}")
                self.streams["video"][stream_id] = VideoStream(
                    self.ffmpeg_normalize, self, stream_id
                )

            elif "Subtitle" in line:
                logger.debug(f"Found subtitle stream at index {stream_id}")
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
            logger.warning(
                "Output file only supports one stream. "
                "Keeping only first audio stream."
            )
            first_stream = list(self.streams["audio"].values())[0]
            self.streams["audio"] = {first_stream.stream_id: first_stream}
            self.streams["video"] = {}
            self.streams["subtitle"] = {}

    def run_normalization(self):
        """
        Run the normalization process for this file.
        """
        logger.debug(f"Running normalization for {self.input_file}")

        # run the first pass to get loudness stats
        self._first_pass()

        # run the second pass as a whole
        if self.ffmpeg_normalize.progress:
            with tqdm(total=100, position=1, desc="Second Pass") as pbar:
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

    def _first_pass(self):
        """
        Run the first pass of the normalization process.
        """
        logger.debug(f"Parsing normalization info for {self.input_file}")

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
                ) as pbar:
                    for progress in fun():
                        pbar.update(progress - pbar.n)
            else:
                for _ in fun():
                    pass

        if self.ffmpeg_normalize.print_stats:
            stats = [
                audio_stream.get_stats()
                for audio_stream in self.streams["audio"].values()
            ]
            self.ffmpeg_normalize.stats.extend(stats)

    def _get_audio_filter_cmd(self) -> Tuple[str, List[str]]:
        """
        Return the audio filter command and output labels needed.

        Returns:
            Tuple[str, List[str]]: filter_complex command and the required output labels
        """
        filter_chains = []
        output_labels = []

        for audio_stream in self.streams["audio"].values():
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

    def _second_pass(self) -> None:
        """
        Construct the second pass command and run it.

        FIXME: make this method simpler
        """
        logger.info(f"Running second pass for {self.input_file}")

        # get the target output stream types depending on the options
        output_stream_types = ["audio"]
        if self._can_write_output_video():
            output_stream_types.append("video")
        if not self.ffmpeg_normalize.subtitle_disable:
            output_stream_types.append("subtitle")

        # base command, here we will add all other options
        cmd = [self.ffmpeg_normalize.ffmpeg_exe, "-y", "-nostdin"]

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
                    logger.warning(
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
            cmd.extend(["-b:a", str(self.ffmpeg_normalize.audio_bitrate)])
        if self.ffmpeg_normalize.sample_rate:
            cmd.extend(["-ar", str(self.ffmpeg_normalize.sample_rate)])

        # ... and subtitles
        if not self.ffmpeg_normalize.subtitle_disable:
            for s in self.streams["subtitle"].keys():
                cmd.extend(["-map", f"0:{s}"])
            # copy subtitles
            cmd.extend(["-c:s", "copy"])

        if self.ffmpeg_normalize.keep_original_audio:
            highest_index = len(self.streams["audio"])
            for index, (_, s) in enumerate(self.streams["audio"].items()):
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
            cmd_runner = CommandRunner(cmd, dry=True)
            cmd_runner.run_command()
            yield 100
            return

        # create a temporary output file name
        temp_dir = tempfile.gettempdir()
        output_file_suffix = os.path.splitext(self.output_file)[1]
        temp_file_name = os.path.join(
            temp_dir, next(tempfile._get_candidate_names()) + output_file_suffix
        )
        cmd.append(temp_file_name)

        # run the actual command
        try:
            cmd_runner = CommandRunner(cmd)
            try:
                yield from cmd_runner.run_ffmpeg_command()
            except Exception as e:
                cmd_str = " ".join([shlex.quote(c) for c in cmd])
                logger.error(f"Error while running command {cmd_str}! Error: {e}")
                raise e
            else:
                # move file from TMP to output file
                logger.debug(
                    f"Moving temporary file from {temp_file_name} to {self.output_file}"
                )
                shutil.move(temp_file_name, self.output_file)
        except Exception as e:
            # remove dangling temporary file
            if os.path.isfile(temp_file_name):
                os.remove(temp_file_name)
            raise e

        logger.debug("Normalization finished")
