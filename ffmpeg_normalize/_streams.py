from __future__ import annotations

import json
import logging
import os
import re
from typing import TYPE_CHECKING, Iterator, Literal, TypedDict, cast

from ._cmd_utils import NUL, CommandRunner, dict_to_filter_opts
from ._errors import FFmpegNormalizeError

if TYPE_CHECKING:
    from ._ffmpeg_normalize import FFmpegNormalize
    from ._media_file import MediaFile

_logger = logging.getLogger(__name__)


class EbuLoudnessStatistics(TypedDict):
    input_i: float
    input_tp: float
    input_lra: float
    input_thresh: float
    output_i: float
    output_tp: float
    output_lra: float
    output_thresh: float
    target_offset: float


class LoudnessStatistics(TypedDict):
    ebu: EbuLoudnessStatistics | None
    mean: float | None
    max: float | None


class LoudnessStatisticsWithMetadata(LoudnessStatistics):
    input_file: str
    output_file: str
    stream_id: int


class MediaStream:
    def __init__(
        self,
        ffmpeg_normalize: FFmpegNormalize,
        media_file: MediaFile,
        stream_type: Literal["audio", "video", "subtitle"],
        stream_id: int,
    ):
        """
        Create a MediaStream object.

        Args:
            ffmpeg_normalize (FFmpegNormalize): The FFmpegNormalize object.
            media_file (MediaFile): The MediaFile object.
            stream_type (Literal["audio", "video", "subtitle"]): The type of the stream.
            stream_id (int): The stream ID.
        """
        self.ffmpeg_normalize = ffmpeg_normalize
        self.media_file = media_file
        self.stream_type = stream_type
        self.stream_id = stream_id

    def __repr__(self) -> str:
        return (
            f"<{os.path.basename(self.media_file.input_file)}, "
            f"{self.stream_type} stream {self.stream_id}>"
        )


class VideoStream(MediaStream):
    def __init__(
        self, ffmpeg_normalize: FFmpegNormalize, media_file: MediaFile, stream_id: int
    ):
        super().__init__(ffmpeg_normalize, media_file, "video", stream_id)


class SubtitleStream(MediaStream):
    def __init__(
        self, ffmpeg_normalize: FFmpegNormalize, media_file: MediaFile, stream_id: int
    ):
        super().__init__(ffmpeg_normalize, media_file, "subtitle", stream_id)


class AudioStream(MediaStream):
    def __init__(
        self,
        ffmpeg_normalize: FFmpegNormalize,
        media_file: MediaFile,
        stream_id: int,
        sample_rate: int | None,
        bit_depth: int | None,
        duration: float | None,
    ):
        """
        Create an AudioStream object.

        Args:
            ffmpeg_normalize (FFmpegNormalize): The FFmpegNormalize object.
            media_file (MediaFile): The MediaFile object.
            stream_id (int): The stream ID.
            sample_rate (int): sample rate in Hz
            bit_depth (int): bit depth in bits
            duration (float): duration in seconds
        """
        super().__init__(ffmpeg_normalize, media_file, "audio", stream_id)

        self.loudness_statistics: LoudnessStatistics = {
            "ebu": None,
            "mean": None,
            "max": None,
        }

        self.sample_rate = sample_rate
        self.bit_depth = bit_depth

        self.duration = duration

    @staticmethod
    def _constrain(
        number: float, min_range: float, max_range: float, name: str | None = None
    ) -> float:
        """
        Constrain a number between two values.

        Args:
            number (float): The number to constrain.
            min_range (float): The minimum value.
            max_range (float): The maximum value.
            name (str): The name of the number (for logging).

        Returns:
            float: The constrained number.

        Raises:
            ValueError: If min_range is greater than max_range.
        """
        if min_range > max_range:
            raise ValueError("min must be smaller than max")
        result = max(min(number, max_range), min_range)
        if result != number and name is not None:
            _logger.warning(
                f"Constraining {name} to range of [{min_range}, {max_range}]: {number} -> {result}"
            )
        return result

    def get_stats(self) -> LoudnessStatisticsWithMetadata:
        """
        Return loudness statistics for the stream.

        Returns:
            dict: A dictionary containing the loudness statistics.
        """
        stats: LoudnessStatisticsWithMetadata = {
            "input_file": self.media_file.input_file,
            "output_file": self.media_file.output_file,
            "stream_id": self.stream_id,
            "ebu": self.loudness_statistics["ebu"],
            "mean": self.loudness_statistics["mean"],
            "max": self.loudness_statistics["max"],
        }
        return stats

    def get_pcm_codec(self) -> str:
        """
        Get the PCM codec string for the stream.

        Returns:
            str: The PCM codec string.
        """
        if not self.bit_depth:
            return "pcm_s16le"
        elif self.bit_depth <= 8:
            return "pcm_s8"
        elif self.bit_depth in [16, 24, 32, 64]:
            return f"pcm_s{self.bit_depth}le"
        else:
            _logger.warning(
                f"Unsupported bit depth {self.bit_depth}, falling back to pcm_s16le"
            )
            return "pcm_s16le"

    def _get_filter_str_with_pre_filter(self, current_filter: str) -> str:
        """
        Get a filter string for current_filter, with the pre-filter
        added before. Applies the input label before.

        Args:
            current_filter (str): The current filter.

        Returns:
            str: The filter string.
        """
        input_label = f"[0:{self.stream_id}]"
        filter_chain = []
        if self.media_file.ffmpeg_normalize.pre_filter:
            filter_chain.append(self.media_file.ffmpeg_normalize.pre_filter)
        filter_chain.append(current_filter)
        filter_str = input_label + ",".join(filter_chain)
        return filter_str

    def parse_astats(self) -> Iterator[float]:
        """
        Use ffmpeg with astats filter to get the mean (RMS) and max (peak) volume of the input file.

        Yields:
            float: The progress of the command.
        """
        _logger.info(f"Running first pass astats filter for stream {self.stream_id}")

        filter_str = self._get_filter_str_with_pre_filter(
            "astats=measure_overall=Peak_level+RMS_level:measure_perchannel=0"
        )

        cmd = [
            self.media_file.ffmpeg_normalize.ffmpeg_exe,
            "-hide_banner",
            "-y",
            "-i",
            self.media_file.input_file,
            "-filter_complex",
            filter_str,
            "-vn",
            "-sn",
            "-f",
            "null",
            NUL,
        ]

        cmd_runner = CommandRunner()
        yield from cmd_runner.run_ffmpeg_command(cmd)
        output = cmd_runner.get_output()

        _logger.debug(
            f"astats command output: {CommandRunner.prune_ffmpeg_progress_from_output(output)}"
        )

        mean_volume_matches = re.findall(r"RMS level dB: ([\-\d\.]+)", output)
        if mean_volume_matches:
            if mean_volume_matches[0] == "-":
                self.loudness_statistics["mean"] = float("-inf")
            else:
                self.loudness_statistics["mean"] = float(mean_volume_matches[0])
        else:
            raise FFmpegNormalizeError(
                f"Could not get mean volume for {self.media_file.input_file}"
            )

        max_volume_matches = re.findall(r"Peak level dB: ([\-\d\.]+)", output)
        if max_volume_matches:
            if max_volume_matches[0] == "-":
                self.loudness_statistics["max"] = float("-inf")
            else:
                self.loudness_statistics["max"] = float(max_volume_matches[0])
        else:
            raise FFmpegNormalizeError(
                f"Could not get max volume for {self.media_file.input_file}"
            )

    def parse_loudnorm_stats(self) -> Iterator[float]:
        """
        Run a first pass loudnorm filter to get measured data.

        Yields:
            float: The progress of the command.
        """
        _logger.info(f"Running first pass loudnorm filter for stream {self.stream_id}")

        opts = {
            "i": self.media_file.ffmpeg_normalize.target_level,
            "lra": self.media_file.ffmpeg_normalize.loudness_range_target,
            "tp": self.media_file.ffmpeg_normalize.true_peak,
            "offset": self.media_file.ffmpeg_normalize.offset,
            "print_format": "json",
        }

        if self.media_file.ffmpeg_normalize.dual_mono:
            opts["dual_mono"] = "true"

        filter_str = self._get_filter_str_with_pre_filter(
            "loudnorm=" + dict_to_filter_opts(opts)
        )

        cmd = [
            self.media_file.ffmpeg_normalize.ffmpeg_exe,
            "-hide_banner",
            "-y",
            "-i",
            self.media_file.input_file,
            "-filter_complex",
            filter_str,
            "-vn",
            "-sn",
            "-f",
            "null",
            NUL,
        ]

        cmd_runner = CommandRunner()
        yield from cmd_runner.run_ffmpeg_command(cmd)
        output = cmd_runner.get_output()

        _logger.debug(
            f"Loudnorm first pass command output: {CommandRunner.prune_ffmpeg_progress_from_output(output)}"
        )

        output_lines = [line.strip() for line in output.split("\n")]

        self.loudness_statistics["ebu"] = AudioStream._parse_loudnorm_output(
            output_lines
        )

    @staticmethod
    def _parse_loudnorm_output(output_lines: list[str]) -> EbuLoudnessStatistics:
        """
        Parse the output of a loudnorm filter to get the EBU loudness statistics.

        Args:
            output_lines (list[str]): The output lines of the loudnorm filter.

        Raises:
            FFmpegNormalizeError: When the output could not be parsed.

        Returns:
            EbuLoudnessStatistics: The EBU loudness statistics.
        """
        loudnorm_start = 0
        loudnorm_end = 0
        for index, line in enumerate(output_lines):
            if line.startswith("[Parsed_loudnorm"):
                loudnorm_start = index + 1
                continue
            if loudnorm_start and line.startswith("}"):
                loudnorm_end = index + 1
                break

        if not (loudnorm_start and loudnorm_end):
            raise FFmpegNormalizeError(
                "Could not parse loudnorm stats; no loudnorm-related output found"
            )

        try:
            loudnorm_stats = json.loads(
                "\n".join(output_lines[loudnorm_start:loudnorm_end])
            )

            _logger.debug(f"Loudnorm stats parsed: {json.dumps(loudnorm_stats)}")

            for key in [
                "input_i",
                "input_tp",
                "input_lra",
                "input_thresh",
                "output_i",
                "output_tp",
                "output_lra",
                "output_thresh",
                "target_offset",
            ]:
                # handle infinite values
                if float(loudnorm_stats[key]) == -float("inf"):
                    loudnorm_stats[key] = -99
                elif float(loudnorm_stats[key]) == float("inf"):
                    loudnorm_stats[key] = 0
                else:
                    # convert to floats
                    loudnorm_stats[key] = float(loudnorm_stats[key])

            return cast(EbuLoudnessStatistics, loudnorm_stats)
        except Exception as e:
            raise FFmpegNormalizeError(
                f"Could not parse loudnorm stats; wrong JSON format in string: {e}"
            )

    def get_second_pass_opts_ebu(self) -> str:
        """
        Return second pass loudnorm filter options string for ffmpeg
        """

        if not self.loudness_statistics["ebu"]:
            raise FFmpegNormalizeError(
                "First pass not run, you must call parse_loudnorm_stats first"
            )

        if float(self.loudness_statistics["ebu"]["input_i"]) > 0:
            _logger.warning(
                "Input file had measured input loudness greater than zero "
                f"({self.loudness_statistics['ebu']['input_i']}), capping at 0"
            )
            self.loudness_statistics["ebu"]["input_i"] = 0

        will_use_dynamic_mode = self.media_file.ffmpeg_normalize.dynamic

        if self.media_file.ffmpeg_normalize.keep_loudness_range_target:
            _logger.debug(
                "Keeping target loudness range in second pass loudnorm filter"
            )
            input_lra = self.loudness_statistics["ebu"]["input_lra"]
            if input_lra < 1 or input_lra > 50:
                _logger.warning(
                    "Input file had measured loudness range outside of [1,50] "
                    f"({input_lra}), capping to allowed range"
                )

            self.media_file.ffmpeg_normalize.loudness_range_target = self._constrain(
                self.loudness_statistics["ebu"]["input_lra"], 1, 50
            )

        if self.media_file.ffmpeg_normalize.keep_lra_above_loudness_range_target:
            if (
                self.loudness_statistics["ebu"]["input_lra"]
                <= self.media_file.ffmpeg_normalize.loudness_range_target
            ):
                _logger.debug(
                    "Setting loudness range target in second pass loudnorm filter"
                )
            else:
                self.media_file.ffmpeg_normalize.loudness_range_target = (
                    self.loudness_statistics["ebu"]["input_lra"]
                )
                _logger.debug(
                    "Keeping target loudness range in second pass loudnorm filter"
                )

        if (
            self.media_file.ffmpeg_normalize.loudness_range_target
            < self.loudness_statistics["ebu"]["input_lra"]
            and not will_use_dynamic_mode
        ):
            _logger.warning(
                f"Input file had loudness range of {self.loudness_statistics['ebu']['input_lra']}. "
                f"This is larger than the loudness range target ({self.media_file.ffmpeg_normalize.loudness_range_target}). "
                "Normalization will revert to dynamic mode. Choose a higher target loudness range if you want linear normalization. "
                "Alternatively, use the --keep-loudness-range-target or --keep-lra-above-loudness-range-target option to keep the target loudness range from "
                "the input."
            )
            will_use_dynamic_mode = True

        if will_use_dynamic_mode and not self.ffmpeg_normalize.sample_rate:
            _logger.warning(
                "In dynamic mode, the sample rate will automatically be set to 192 kHz by the loudnorm filter. "
                "Specify -ar/--sample-rate to override it."
            )

        stats = self.loudness_statistics["ebu"]

        opts = {
            "i": self.media_file.ffmpeg_normalize.target_level,
            "lra": self.media_file.ffmpeg_normalize.loudness_range_target,
            "tp": self.media_file.ffmpeg_normalize.true_peak,
            "offset": self._constrain(
                float(stats["target_offset"]), -99, 99, name="target_offset"
            ),
            "measured_i": self._constrain(
                float(stats["input_i"]), -99, 0, name="input_i"
            ),
            "measured_lra": self._constrain(
                float(stats["input_lra"]), 0, 99, name="input_lra"
            ),
            "measured_tp": self._constrain(
                float(stats["input_tp"]), -99, 99, name="input_tp"
            ),
            "measured_thresh": self._constrain(
                float(stats["input_thresh"]), -99, 0, name="input_thresh"
            ),
            "linear": "false" if self.media_file.ffmpeg_normalize.dynamic else "true",
            "print_format": "json",
        }

        if self.media_file.ffmpeg_normalize.dual_mono:
            opts["dual_mono"] = "true"

        return "loudnorm=" + dict_to_filter_opts(opts)

    def get_second_pass_opts_peakrms(self) -> str:
        """
        Set the adjustment gain based on chosen option and mean/max volume,
        return the matching ffmpeg volume filter.

        Returns:
            str: ffmpeg volume filter string
        """
        if (
            self.loudness_statistics["max"] is None
            or self.loudness_statistics["mean"] is None
        ):
            raise FFmpegNormalizeError(
                "First pass not run, no mean/max volume to normalize to"
            )

        normalization_type = self.media_file.ffmpeg_normalize.normalization_type
        target_level = self.media_file.ffmpeg_normalize.target_level

        if normalization_type == "peak":
            adjustment = 0 + target_level - self.loudness_statistics["max"]
        elif normalization_type == "rms":
            adjustment = target_level - self.loudness_statistics["mean"]
        else:
            raise FFmpegNormalizeError(
                "Can only set adjustment for peak and RMS normalization"
            )

        _logger.info(
            f"Adjusting stream {self.stream_id} by {adjustment} dB to reach {target_level}"
        )

        clip_amount = self.loudness_statistics["max"] + adjustment
        if clip_amount > 0:
            _logger.warning(f"Adjusting will lead to clipping of {clip_amount} dB")

        return f"volume={adjustment}dB"
