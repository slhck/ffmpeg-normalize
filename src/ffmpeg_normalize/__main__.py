from __future__ import annotations

import argparse
import json
import logging
import os
import shlex
import sys
import textwrap
from json.decoder import JSONDecodeError
from typing import NoReturn

from ._errors import FFmpegNormalizeError
from ._ffmpeg_normalize import NORMALIZATION_TYPES, FFmpegNormalize
from ._logger import setup_cli_logger
from ._presets import PresetManager

# Import version from package
import importlib.metadata

__version__ = importlib.metadata.version("ffmpeg-normalize")

_logger = logging.getLogger(__name__)


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ffmpeg-normalize",
        description=textwrap.dedent(
            """\
            ffmpeg-normalize v{} -- command line tool for normalizing audio files
            """.format(__version__)
        ),
        # manually overridden because argparse generates the wrong order of arguments, see:
        # https://github.com/slhck/ffmpeg-normalize/issues/132#issuecomment-662516535
        usage="%(prog)s INPUT [INPUT ...] [-o OUTPUT [OUTPUT ...]] [options]",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent(
            """\
            The program additionally respects environment variables:

              - `TMP` / `TEMP` / `TMPDIR`
                    Sets the path to the temporary directory in which files are
                    stored before being moved to the final output directory.
                    Note: You need to use full paths.

              - `FFMPEG_PATH`
                    Sets the full path to an `ffmpeg` executable other than
                    the system default.


            Author: Werner Robitza
            License: MIT
            Website / Issues: https://github.com/slhck/ffmpeg-normalize
            """
        ),
    )

    group_io = parser.add_argument_group("File Input/output")
    group_io.add_argument("input", nargs="*", help="Input media file(s)")
    group_io.add_argument(
        "--input-list",
        type=str,
        help="Path to a text file containing a line-separated list of input files",
    )
    group_io.add_argument(
        "-o",
        "--output",
        nargs="+",
        help=textwrap.dedent(
            """\
        Output file names. Will be applied per input file.

        If no output file name is specified for an input file, the output files
        will be written to the default output folder with the name `<input>.<ext>`,
        where `<ext>` is the output extension (see `-ext` option).

        Example: ffmpeg-normalize 1.wav 2.wav -o 1n.wav 2n.wav
        """
        ),
    )
    group_io.add_argument(
        "-of",
        "--output-folder",
        type=str,
        help=textwrap.dedent(
            """\
            Output folder (default: `normalized`)

            This folder will be used for input files that have no explicit output
            name specified.
        """
        ),
        default=FFmpegNormalize.DEFAULTS["output_folder"],
    )

    group_general = parser.add_argument_group("General Options")
    group_general.add_argument(
        "-f", "--force", action="store_true", help="Force overwrite existing files"
    )
    group_general.add_argument(
        "-d", "--debug", action="store_true", help="Print debugging output"
    )
    group_general.add_argument(
        "-v", "--verbose", action="store_true", help="Print verbose output"
    )
    group_general.add_argument(
        "-q", "--quiet", action="store_true", help="Only print errors in output"
    )
    group_general.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Do not run normalization, only print what would be done",
    )
    group_general.add_argument(
        "-pr",
        "--progress",
        action="store_true",
        help="Show progress bar for files and streams",
    )
    group_general.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s v{__version__}",
        help="Print version and exit",
    )
    group_general.add_argument(
        "--preset",
        type=str,
        help=textwrap.dedent(
            """\
        Load options from a preset file.

        Preset files are JSON files located in the presets directory.
        The directory location depends on your OS:
        - Linux/macOS: ~/.config/ffmpeg-normalize/presets/
        - Windows: %%APPDATA%%/ffmpeg-normalize/presets/

        Use --list-presets to see available presets.
        CLI options specified on the command line take precedence over preset values.
        """
        ),
    )
    group_general.add_argument(
        "--list-presets",
        action="store_true",
        help="List all available presets and exit",
    )

    group_normalization = parser.add_argument_group("Normalization")
    group_normalization.add_argument(
        "-nt",
        "--normalization-type",
        type=str,
        choices=NORMALIZATION_TYPES,
        help=textwrap.dedent(
            """\
        Normalization type (default: `ebu`).

        EBU normalization performs two passes and normalizes according to EBU
        R128.

        RMS-based normalization brings the input file to the specified RMS
        level.

        Peak normalization brings the signal to the specified peak level.
        """
        ),
        default=FFmpegNormalize.DEFAULTS["normalization_type"],
    )
    group_normalization.add_argument(
        "-t",
        "--target-level",
        type=float,
        help=textwrap.dedent(
            f"""\
        Normalization target level in dB/LUFS (default: {FFmpegNormalize.DEFAULTS["target_level"]}).

        For EBU normalization, it corresponds to Integrated Loudness Target
        in LUFS. The range is -70.0 - -5.0.

        Otherwise, the range is -99 to 0.
        """
        ),
        default=FFmpegNormalize.DEFAULTS["target_level"],
    )
    group_normalization.add_argument(
        "-p",
        "--print-stats",
        action="store_true",
        help="Print loudness statistics for both passes formatted as JSON to stdout.",
    )
    group_normalization.add_argument(
        "--replaygain",
        action="store_true",
        help=textwrap.dedent(
            """\
        Write ReplayGain tags to the original file without normalizing.
        This mode will overwrite the input file and ignore other options.
        Only works with EBU normalization, and only with .mp3, .mp4/.m4a, .ogg, .opus for now.
        """
        ),
    )
    group_normalization.add_argument(
        "--batch",
        action="store_true",
        help=textwrap.dedent(
            """\
        Preserve relative loudness between files (album mode).

        When operating on a group of unrelated files, you usually want all of them at the same
        level. However, a group of music files all from the same album is generally meant to be
        listened to at the relative volumes they were recorded at. In batch mode, all the specified
        files are considered to be part of a single album and their relative volumes are preserved.
        This is done by averaging the loudness of all the files, computing a single adjustment from
        that, and applying a relative adjustment to all the files.

        Batch mode works with all normalization types (EBU, RMS, peak).
        """
        ),
    )

    # group_normalization.add_argument(
    #     '--threshold',
    #     type=float,
    #     help=textwrap.dedent("""\
    #     Threshold below which normalization should not be run.

    #     If the stream falls within the threshold, it will simply be copied.
    #     """),
    #     default=0.5
    # )

    group_ebu = parser.add_argument_group("EBU R128 Normalization")
    group_ebu.add_argument(
        "-lrt",
        "--loudness-range-target",
        type=float,
        help=textwrap.dedent(
            f"""\
        EBU Loudness Range Target in LUFS (default: {FFmpegNormalize.DEFAULTS["loudness_range_target"]}).
        Range is 1.0 - 50.0.
        """
        ),
        default=FFmpegNormalize.DEFAULTS["loudness_range_target"],
    )

    group_ebu.add_argument(
        "--keep-loudness-range-target",
        action="store_true",
        help=textwrap.dedent(
            """\
        Keep the input loudness range target to allow for linear normalization.
        """
        ),
    )

    group_ebu.add_argument(
        "--keep-lra-above-loudness-range-target",
        action="store_true",
        help=textwrap.dedent(
            """\
        Keep input loudness range above loudness range target.
        Can be used as an alternative to `--keep-loudness-range-target` to allow for linear normalization.
        """
        ),
    )

    group_ebu.add_argument(
        "-tp",
        "--true-peak",
        type=float,
        help=textwrap.dedent(
            f"""\
        EBU Maximum True Peak in dBTP (default: {FFmpegNormalize.DEFAULTS["true_peak"]}).
        Range is -9.0 - +0.0.
        """
        ),
        default=FFmpegNormalize.DEFAULTS["true_peak"],
    )

    group_ebu.add_argument(
        "--offset",
        type=float,
        help=textwrap.dedent(
            f"""\
        EBU Offset Gain (default: {FFmpegNormalize.DEFAULTS["offset"]}).
        The gain is applied before the true-peak limiter in the first pass only.
        The offset for the second pass will be automatically determined based on the first pass statistics.
        Range is -99.0 - +99.0.
        """
        ),
        default=FFmpegNormalize.DEFAULTS["offset"],
    )

    group_ebu.add_argument(
        "--lower-only",
        action="store_true",
        help=textwrap.dedent(
            """\
        Whether the audio should not increase in loudness.

        If the measured loudness from the first pass is lower than the target
        loudness then normalization will be skipped for the audio source.

        For EBU normalization, this compares input integrated loudness to the target level.
        For peak normalization, this compares the input peak level to the target level.
        For RMS normalization, this compares the input RMS level to the target level.
        """
        ),
    )

    group_ebu.add_argument(
        "--auto-lower-loudness-target",
        action="store_true",
        help=textwrap.dedent(
            """\
        Automatically lower EBU Integrated Loudness Target to prevent falling
        back to dynamic filtering.

        Makes sure target loudness is lower than measured loudness minus peak
        loudness (input_i - input_tp) by a small amount (0.1 LUFS).
        """
        ),
    )

    group_ebu.add_argument(
        "--dual-mono",
        action="store_true",
        help=textwrap.dedent(
            """\
        Treat mono input files as "dual-mono".

        If a mono file is intended for playback on a stereo system, its EBU R128
        measurement will be perceptually incorrect. If set, this option will
        compensate for this effect. Multi-channel input files are not affected
        by this option.
        """
        ),
    )

    group_ebu.add_argument(
        "--dynamic",
        action="store_true",
        help=textwrap.dedent(
            """\
        Force dynamic normalization mode.

        Instead of applying linear EBU R128 normalization, choose a dynamic
        normalization. This is not usually recommended.

        Dynamic mode will automatically change the sample rate to 192 kHz. Use
        -ar/--sample-rate to specify a different output sample rate.
        """
        ),
    )

    group_stream_selection = parser.add_argument_group("Audio Stream Selection")
    group_stream_selection.add_argument(
        "-as",
        "--audio-streams",
        type=str,
        help=textwrap.dedent(
            """\
        Select specific audio streams to normalize by stream index (comma-separated).
        Example: --audio-streams 0,2 will normalize only streams 0 and 2.

        By default, all audio streams are normalized.
        """
        ),
    )
    group_stream_selection.add_argument(
        "--audio-default-only",
        action="store_true",
        help=textwrap.dedent(
            """\
        Only normalize audio streams with the 'default' disposition flag.
        This is useful for files with multiple audio tracks where only the main track
        should be normalized (e.g., keeping commentary tracks unchanged).
        """
        ),
    )
    group_stream_selection.add_argument(
        "--keep-other-audio",
        action="store_true",
        help=textwrap.dedent(
            """\
        Keep non-selected audio streams in the output file (copy without normalization).
        Only applies when --audio-streams or --audio-default-only is used.

        By default, only selected streams are included in the output.
        """
        ),
    )

    group_acodec = parser.add_argument_group("Audio Encoding")
    group_acodec.add_argument(
        "-c:a",
        "--audio-codec",
        type=str,
        help=textwrap.dedent(
            """\
        Audio codec to use for output files.
        See `ffmpeg -encoders` for a list.

        Will use PCM audio with input stream bit depth by default.
        """
        ),
    )
    group_acodec.add_argument(
        "-b:a",
        "--audio-bitrate",
        type=str,
        help=textwrap.dedent(
            """\
        Audio bitrate in bits/s, or with K suffix.

        If not specified, will use codec default.
        """
        ),
    )
    group_acodec.add_argument(
        "-ar",
        "--sample-rate",
        type=str,
        help=textwrap.dedent(
            """\
        Audio sample rate to use for output files in Hz.

        Will use input sample rate by default, except for EBU normalization,
        which will change the input sample rate to 192 kHz.
        """
        ),
    )
    group_acodec.add_argument(
        "-ac",
        "--audio-channels",
        type=int,
        help=textwrap.dedent(
            """\
        Set the number of audio channels.
        If not specified, the input channel layout will be used.
        """
        ),
    )
    group_acodec.add_argument(
        "-koa",
        "--keep-original-audio",
        action="store_true",
        help="Copy original, non-normalized audio streams to output file",
    )
    group_acodec.add_argument(
        "-prf",
        "--pre-filter",
        type=str,
        help=textwrap.dedent(
            """\
        Add an audio filter chain before applying normalization.
        Multiple filters can be specified by comma-separating them.
        """
        ),
    )
    group_acodec.add_argument(
        "-pof",
        "--post-filter",
        type=str,
        help=textwrap.dedent(
            """\
        Add an audio filter chain after applying normalization.
        Multiple filters can be specified by comma-separating them.

        For EBU, the filter will be applied during the second pass.
        """
        ),
    )

    group_vcodec = parser.add_argument_group("Other Encoding Options")
    group_vcodec.add_argument(
        "-vn",
        "--video-disable",
        action="store_true",
        help="Do not write video streams to output",
    )
    group_vcodec.add_argument(
        "-c:v",
        "--video-codec",
        type=str,
        help=textwrap.dedent(
            """\
        Video codec to use for output files (default: 'copy').
        See `ffmpeg -encoders` for a list.

        Will attempt to copy video codec by default.
        """
        ),
        default=FFmpegNormalize.DEFAULTS["video_codec"],
    )
    group_vcodec.add_argument(
        "-sn",
        "--subtitle-disable",
        action="store_true",
        help="Do not write subtitle streams to output",
    )
    group_vcodec.add_argument(
        "-mn",
        "--metadata-disable",
        action="store_true",
        help="Do not write metadata to output",
    )
    group_vcodec.add_argument(
        "-cn",
        "--chapters-disable",
        action="store_true",
        help="Do not write chapters to output",
    )

    group_format = parser.add_argument_group("Input/Output options")
    group_format.add_argument(
        "-ei",
        "--extra-input-options",
        type=str,
        help=textwrap.dedent(
            """\
        Extra input options list.

        A list of extra ffmpeg command line arguments valid for the input,
        applied before ffmpeg's `-i`.

        You can either use a JSON-formatted list (i.e., a list of
        comma-separated, quoted elements within square brackets), or a simple
        string of space-separated arguments.

        If JSON is used, you need to wrap the whole argument in quotes to
        prevent shell expansion and to preserve literal quotes inside the
        string. If a simple string is used, you need to specify the argument
        with `-e=`.

        Examples: `-e '[ "-f", "mpegts" ]'` or `-e="-f mpegts"`
        """
        ),
    )
    group_format.add_argument(
        "-e",
        "--extra-output-options",
        type=str,
        help=textwrap.dedent(
            """\
        Extra output options list.

        A list of extra ffmpeg command line arguments.

        You can either use a JSON-formatted list (i.e., a list of
        comma-separated, quoted elements within square brackets), or a simple
        string of space-separated arguments.

        If JSON is used, you need to wrap the whole argument in quotes to
        prevent shell expansion and to preserve literal quotes inside the
        string. If a simple string is used, you need to specify the argument
        with `-e=`.

        Examples: `-e '[ "-vbr", "3" ]'` or `-e="-vbr 3"`
        """
        ),
    )
    group_format.add_argument(
        "-ofmt",
        "--output-format",
        type=str,
        help=textwrap.dedent(
            """\
        Media format to use for output file(s).
        See 'ffmpeg -formats' for a list.

        If not specified, the format will be inferred by ffmpeg from the output
        file name. If the output file name is not explicitly specified, the
        extension will govern the format (see '--extension' option).
        """
        ),
    )
    group_format.add_argument(
        "-ext",
        "--extension",
        type=str,
        help=textwrap.dedent(
            """\
        Output file extension to use for output files that were not explicitly
        specified. (Default: `mkv`)
        """
        ),
        default=FFmpegNormalize.DEFAULTS["extension"],
    )
    return parser


def main() -> None:
    cli_args = create_parser().parse_args()
    setup_cli_logger(arguments=cli_args)

    def error(message: object) -> NoReturn:
        if _logger.getEffectiveLevel() == logging.DEBUG:
            _logger.error(f"FFmpegNormalizeError: {message}")
        else:
            _logger.error(message)
        sys.exit(1)

    # Handle --list-presets
    preset_manager = PresetManager()
    if cli_args.list_presets:
        presets = preset_manager.get_available_presets()
        if presets:
            print("Available presets:")
            for preset in presets:
                print(f"  - {preset}")
        else:
            print(f"No presets found in {preset_manager.presets_dir}")
        sys.exit(0)

    # Load and apply preset if specified
    if cli_args.preset:
        try:
            preset_data = preset_manager.load_preset(cli_args.preset)
            _logger.debug(f"Loaded preset '{cli_args.preset}': {preset_data}")
            preset_manager.merge_preset_with_args(preset_data, cli_args)
            _logger.info(f"Applied preset '{cli_args.preset}'")
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            error(str(e))

    def _split_options(opts: str) -> list[str]:
        """
        Parse extra options (input or output) into a list.

        Args:
            opts: String of options

        Returns:
            list: List of options
        """
        if not opts:
            return []
        try:
            if opts.startswith("["):
                try:
                    ret = [str(s) for s in json.loads(opts)]
                except JSONDecodeError:
                    ret = shlex.split(opts)
            else:
                ret = shlex.split(opts)
        except Exception as e:
            error(f"Could not parse extra_options: {e}")
        return ret

    # parse extra options
    extra_input_options = _split_options(cli_args.extra_input_options)
    extra_output_options = _split_options(cli_args.extra_output_options)

    # parse audio streams selection
    audio_streams = None
    if cli_args.audio_streams:
        try:
            audio_streams = [int(s.strip()) for s in cli_args.audio_streams.split(",")]
        except ValueError:
            error("Invalid audio stream indices. Must be comma-separated integers.")

    # validate stream selection options
    if cli_args.audio_default_only and cli_args.audio_streams:
        error("Cannot use both --audio-default-only and --audio-streams together.")

    ffmpeg_normalize = FFmpegNormalize(
        normalization_type=cli_args.normalization_type,
        target_level=cli_args.target_level,
        print_stats=cli_args.print_stats,
        loudness_range_target=cli_args.loudness_range_target,
        # threshold=cli_args.threshold,
        keep_loudness_range_target=cli_args.keep_loudness_range_target,
        keep_lra_above_loudness_range_target=cli_args.keep_lra_above_loudness_range_target,
        true_peak=cli_args.true_peak,
        offset=cli_args.offset,
        lower_only=cli_args.lower_only,
        auto_lower_loudness_target=cli_args.auto_lower_loudness_target,
        dual_mono=cli_args.dual_mono,
        dynamic=cli_args.dynamic,
        audio_codec=cli_args.audio_codec,
        audio_bitrate=cli_args.audio_bitrate,
        sample_rate=cli_args.sample_rate,
        audio_channels=cli_args.audio_channels,
        keep_original_audio=cli_args.keep_original_audio,
        pre_filter=cli_args.pre_filter,
        post_filter=cli_args.post_filter,
        video_codec=cli_args.video_codec,
        video_disable=cli_args.video_disable,
        subtitle_disable=cli_args.subtitle_disable,
        metadata_disable=cli_args.metadata_disable,
        chapters_disable=cli_args.chapters_disable,
        extra_input_options=extra_input_options,
        extra_output_options=extra_output_options,
        output_format=cli_args.output_format,
        extension=cli_args.extension,
        dry_run=cli_args.dry_run,
        progress=cli_args.progress,
        replaygain=cli_args.replaygain,
        batch=cli_args.batch,
        audio_streams=audio_streams,
        audio_default_only=cli_args.audio_default_only,
        keep_other_audio=cli_args.keep_other_audio,
    )

    if cli_args.output and len(cli_args.input) > len(cli_args.output):
        _logger.warning(
            "There are more input files than output file names given. "
            "Please specify one output file name per input file using -o <output1> <output2> ... "
            "Will apply default file naming for the remaining ones."
        )

    # Collect input files from positional args and --input-list
    input_files = list(cli_args.input) if cli_args.input else []
    if cli_args.input_list:
        if not os.path.exists(cli_args.input_list):
            error(f"Input list file '{cli_args.input_list}' does not exist")
        with open(cli_args.input_list, "r") as f:
            input_files.extend([line.strip() for line in f if line.strip()])

    if not input_files:
        error("No input files specified. Use positional arguments or --input-list.")

    # Validate all input files upfront before processing
    _logger.debug("Validating all input files before processing...")
    validation_errors = FFmpegNormalize.validate_input_files(input_files)
    if validation_errors:
        _logger.error("Validation failed for the following files:")
        for err in validation_errors:
            _logger.error(f"  - {err}")
        error(
            f"Validation failed for {len(validation_errors)} file(s). "
            "Please fix the issues above and try again."
        )

    for index, input_file in enumerate(input_files):
        if cli_args.output is not None and index < len(cli_args.output):
            if cli_args.output_folder and cli_args.output_folder != "normalized":
                _logger.warning(
                    f"Output folder {cli_args.output_folder} is ignored for "
                    f"input file {input_file}"
                )
            output_file = cli_args.output[index]
            output_dir = os.path.dirname(output_file)
            if output_dir != "" and not os.path.isdir(output_dir):
                error(f"Output file path {output_dir} does not exist")
        else:
            output_file = os.path.join(
                cli_args.output_folder,
                os.path.splitext(os.path.basename(input_file))[0]
                + "."
                + cli_args.extension,
            )
            if not os.path.isdir(cli_args.output_folder) and not cli_args.dry_run:
                _logger.warning(
                    f"Output directory '{cli_args.output_folder}' does not exist, will create"
                )
                os.makedirs(cli_args.output_folder, exist_ok=True)

        if (
            os.path.exists(output_file)
            and not cli_args.force
            and not cli_args.replaygain
        ):
            _logger.warning(
                f"Output file '{output_file}' already exists, skipping. Use -f to force overwriting."
            )
            continue

        if not os.path.exists(input_file):
            _logger.warning(f"Input file '{input_file}' does not exist, skipping")
            continue

        if not os.path.isfile(input_file):
            _logger.warning(f"Input file '{input_file}' is not a file, skipping")
            continue

        try:
            ffmpeg_normalize.add_media_file(input_file, output_file)
        except FFmpegNormalizeError as e:
            error(e)

    try:
        ffmpeg_normalize.run_normalization()
    except FFmpegNormalizeError as e:
        error(e)


if __name__ == "__main__":
    main()
