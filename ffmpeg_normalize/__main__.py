import argparse
import textwrap
import logging
import os
import shlex
import json

try:
    from json.decoder import JSONDecodeError
except ImportError:
    JSONDecodeError = ValueError

from ._version import __version__
from ._ffmpeg_normalize import FFmpegNormalize, NORMALIZATION_TYPES
from ._errors import FFmpegNormalizeError
from ._logger import setup_custom_logger
logger = setup_custom_logger('ffmpeg_normalize')

def create_parser():
    parser = argparse.ArgumentParser(
        prog="ffmpeg-normalize",
        description=textwrap.dedent("""\
            ffmpeg-normalize v{} -- command line tool for normalizing audio files
            """.format(__version__)),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=textwrap.dedent("""\
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
            Homepage / Issues: https://github.com/slhck/ffmpeg-normalize
            """)
    )

    group_io = parser.add_argument_group("File Input/output")
    group_io.add_argument(
        'input',
        nargs='+',
        help="Input media file(s)"
    )
    group_io.add_argument(
        '-o', '--output',
        nargs='+',
        help=textwrap.dedent("""\
        Output file names. Will be applied per input file.

        If no output file name is specified for an input file, the output files
        will be written to the default output folder with the name `<input>.<ext>`,
        where `<ext>` is the output extension (see `-ext` option).
        """)
    )
    group_io.add_argument(
        '-of', '--output-folder',
        type=str,
        help=textwrap.dedent("""\
            Output folder (default: `normalized`)

            This folder will be used for input files that have no explicit output
            name specified.
        """),
        default='normalized'
    )

    group_general = parser.add_argument_group("General Options")
    group_general.add_argument(
        '-f', '--force',
        action='store_true',
        help="Force overwrite existing files"
    )
    group_general.add_argument(
        '-d', '--debug',
        action='store_true',
        help="Print debugging output"
    )
    group_general.add_argument(
        '-v', '--verbose',
        action='store_true',
        help="Print verbose output"
    )
    group_general.add_argument(
        '-n', '--dry-run',
        action='store_true',
        help="Do not run normalization, only print what would be done"
    )
    group_general.add_argument(
        '-pr', '--progress',
        action='store_true',
        help="Show progress bar for files and streams"
    )
    group_general.add_argument(
        '--version',
        action='version',
        version='%(prog)s v{}'.format(__version__),
        help="Print version and exit"
    )

    group_normalization = parser.add_argument_group("Normalization")
    group_normalization.add_argument(
        '-nt', '--normalization-type',
        type=str,
        choices=NORMALIZATION_TYPES,
        help=textwrap.dedent("""\
        Normalization type (default: `ebu`).

        EBU normalization performs two passes and normalizes according to EBU
        R128.

        RMS-based normalization brings the input file to the specified RMS
        level.

        Peak normalization brings the signal to the specified peak level.
        """),
        default='ebu'
    )
    group_normalization.add_argument(
        '-t', '--target-level',
        type=float,
        help=textwrap.dedent("""\
        Normalization target level in dB/LUFS (default: -23).

        For EBU normalization, it corresponds to Integrated Loudness Target
        in LUFS. The range is -70.0 - -5.0.

        Otherwise, the range is -99 to 0.
        """),
        default=-23.0
    )
    group_normalization.add_argument(
        '-p', '--print-stats',
        action='store_true',
        help="Print first pass loudness statistics formatted as JSON to stdout"
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
        '-lrt', '--loudness-range-target',
        type=float,
        help=textwrap.dedent("""\
        EBU Loudness Range Target in LUFS (default: 7.0).
        Range is 1.0 - 20.0.
        """),
        default=7.0,
    )

    group_ebu.add_argument(
        '-tp', '--true-peak',
        type=float,
        help=textwrap.dedent("""\
        EBU Maximum True Peak in dBTP (default: -2.0).
        Range is -9.0 - +0.0.
        """),
        default=-2.0
    )

    group_ebu.add_argument(
        '--offset',
        type=float,
        help=textwrap.dedent("""\
        EBU Offset Gain (default: 0.0).
        The gain is applied before the true-peak limiter.
        Range is -99.0 - +99.0.
        """),
        default=0.0
    )

    group_ebu.add_argument(
        '--dual-mono',
        action='store_true',
        help=textwrap.dedent("""\
        Treat mono input files as "dual-mono".

        If a mono file is intended for playback on a stereo system, its EBU R128
        measurement will be perceptually incorrect. If set, this option will
        compensate for this effect. Multi-channel input files are not affected
        by this option.
        """)
    )

    group_acodec = parser.add_argument_group("Audio Encoding")
    group_acodec.add_argument(
        '-c:a', '--audio-codec',
        type=str,
        help=textwrap.dedent("""\
        Audio codec to use for output files.
        See `ffmpeg -encoders` for a list.

        Will use PCM audio with input stream bit depth by default.
        """)
    )
    group_acodec.add_argument(
        '-b:a', '--audio-bitrate',
        type=str,
        help=textwrap.dedent("""\
        Audio bitrate in bits/s, or with K suffix.

        If not specified, will use codec default.
        """),
    )
    group_acodec.add_argument(
        '-ar', '--sample-rate',
        type=str,
        help=textwrap.dedent("""\
        Audio sample rate to use for output files in Hz.

        Will use input sample rate by default.
        """)
    )
    group_acodec.add_argument(
        '-koa', '--keep-original-audio',
        action='store_true',
        help="Copy original, non-normalized audio streams to output file"
    )

    group_vcodec = parser.add_argument_group("Other Encoding Options")
    group_vcodec.add_argument(
        '-vn', '--video-disable',
        action='store_true',
        help="Do not write video streams to output"
    )
    group_vcodec.add_argument(
        '-c:v', '--video-codec',
        type=str,
        help=textwrap.dedent("""\
        Video codec to use for output files (default: 'copy').
        See `ffmpeg -encoders` for a list.

        Will attempt to copy video codec by default.
        """),
        default='copy'
    )
    group_vcodec.add_argument(
        '-sn', '--subtitle-disable',
        action='store_true',
        help="Do not write subtitle streams to output"
    )
    group_vcodec.add_argument(
        '-mn', '--metadata-disable',
        action='store_true',
        help="Do not write metadata to output"
    )
    group_vcodec.add_argument(
        '-cn', '--chapters-disable',
        action='store_true',
        help="Do not write chapters to output"
    )

    group_format = parser.add_argument_group("Output Format")
    group_format.add_argument(
        '-e', '--extra-output-options',
        type=str,
        help=textwrap.dedent("""\
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
        """)
    )
    group_format.add_argument(
        '-ofmt', '--output-format',
        type=str,
        help=textwrap.dedent("""\
        Media format to use for output file(s).
        See 'ffmpeg -formats' for a list.

        If not specified, the format will be inferred by ffmpeg from the output
        file name. If the output file name is not explicitly specified, the
        extension will govern the format (see '--extension' option).
        """)
    )
    group_format.add_argument(
        '-ext', '--extension',
        type=str,
        help=textwrap.dedent("""\
        Output file extension to use for output files that were not explicitly
        specified. (Default: `mkv`)
        """),
        default='mkv'
    )
    return parser


def main():
    cli_args = create_parser().parse_args()

    if cli_args.debug:
        logger.setLevel(logging.DEBUG)
    elif cli_args.verbose:
        logger.setLevel(logging.INFO)

    # parse extra options
    extra_output_options = []
    if cli_args.extra_output_options:
        try:
            if cli_args.extra_output_options.startswith('['):
                try:
                    extra_output_options = [str(s) for s in json.loads(cli_args.extra_output_options)]
                except JSONDecodeError as e:
                    extra_output_options = shlex.split(cli_args.extra_output_options)
            else:
                extra_output_options = shlex.split(cli_args.extra_output_options)
        except Exception as e:
            raise FFmpegNormalizeError(
                "Could not parse extra_options: {}".format(e)
            )

    ffmpeg_normalize = FFmpegNormalize(
        normalization_type=cli_args.normalization_type,
        target_level=cli_args.target_level,
        print_stats=cli_args.print_stats,
        loudness_range_target=cli_args.loudness_range_target,
        # threshold=cli_args.threshold,
        true_peak=cli_args.true_peak,
        offset=cli_args.offset,
        dual_mono=cli_args.dual_mono,
        audio_codec=cli_args.audio_codec,
        audio_bitrate=cli_args.audio_bitrate,
        sample_rate=cli_args.sample_rate,
        keep_original_audio=cli_args.keep_original_audio,
        video_codec=cli_args.video_codec,
        video_disable=cli_args.video_disable,
        subtitle_disable=cli_args.subtitle_disable,
        metadata_disable=cli_args.metadata_disable,
        chapters_disable=cli_args.chapters_disable,
        extra_output_options=extra_output_options,
        output_format=cli_args.output_format,
        dry_run=cli_args.dry_run,
        progress=cli_args.progress,
    )

    for index, input_file in enumerate(cli_args.input):
        if cli_args.output is not None and index < len(cli_args.output):
            output_file = cli_args.output[index]
        else:
            output_file = os.path.join(
                cli_args.output_folder,
                os.path.splitext(os.path.basename(input_file))[0] +
                '.' + cli_args.extension,
            )
            if not os.path.isdir(cli_args.output_folder) and not cli_args.dry_run:
                logger.warning(
                    "Output directory '{}' does not exist, will create"
                    .format(cli_args.output_folder)
                )
                os.makedirs(cli_args.output_folder)

        if os.path.exists(output_file) and not cli_args.force:
            logger.warning(
                "Output file {} already exists, skipping. Use -f to force overwriting.".format(output_file)
            )
        else:
            ffmpeg_normalize.add_media_file(input_file, output_file)

    ffmpeg_normalize.run_normalization()


if __name__ == '__main__':
    main()
