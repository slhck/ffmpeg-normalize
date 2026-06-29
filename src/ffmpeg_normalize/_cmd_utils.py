from __future__ import annotations

import contextvars
import logging
import os
import re
import shlex
import subprocess
from contextlib import contextmanager
from shutil import which
from typing import Any, Iterator

from ffmpeg_progress_yield import FfmpegProgress

from ._errors import FFmpegNormalizeError

_logger = logging.getLogger(__name__)

_ffmpeg_env_var: contextvars.ContextVar[dict[str, str] | None] = contextvars.ContextVar(
    "ffmpeg_env", default=None
)


@contextmanager
def ffmpeg_env(env: dict[str, str] | None) -> Iterator[None]:
    """
    Temporarily set the environment for subprocess.Popen.

    Args:
        env: Environment dict to pass to subprocess.Popen.
    """
    token = _ffmpeg_env_var.set(env)
    try:
        yield
    finally:
        _ffmpeg_env_var.reset(token)


def _get_ffmpeg_env() -> dict[str, str] | None:
    return _ffmpeg_env_var.get()


DUR_REGEX = re.compile(
    r"Duration: (?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})\.(?P<ms>\d{2})"
)

# Containers that cannot store raw PCM audio. For these, the bit-depth-aware PCM
# default cannot be used, so a real audio codec has to be chosen (either via the
# -c:a option or by falling back to ffmpeg's own default for the container, see
# get_muxer_default_audio_encoder()). PCM_INCOMPATIBLE_FORMATS is matched against
# the -f/--output-format value, PCM_INCOMPATIBLE_EXTS against the output file
# extension (which additionally lists m4a).
PCM_INCOMPATIBLE_FORMATS = {"flac", "mp3", "mp4", "ogg", "oga", "opus", "webm"}
PCM_INCOMPATIBLE_EXTS = {"flac", "mp3", "mp4", "m4a", "ogg", "oga", "opus", "webm"}

# Output extensions whose ffmpeg muxer is registered under a different name.
# ffmpeg's av_guess_format() resolves these internally; for the "-h muxer="
# query in get_muxer_default_audio_encoder() we need the muxer's own name.
_MUXER_NAME_FOR_EXT = {
    "m4a": "ipod",
    "m4b": "ipod",
    "m4v": "ipod",
    "aac": "adts",
    "mka": "matroska",
    "mkv": "matroska",
}


class CommandRunner:
    """
    Wrapper for running ffmpeg commands
    """

    def __init__(self, dry: bool = False):
        """Create a CommandRunner object

        Args:
            cmd: Command to run as a list of strings
            dry: Dry run mode. Defaults to False.
        """
        self.dry = dry
        self.output: str | None = None

    @staticmethod
    def prune_ffmpeg_progress_from_output(output: str) -> str:
        """
        Prune ffmpeg progress lines from output

        Args:
            output (str): Output from ffmpeg

        Returns:
            str: Output with progress lines removed
        """
        return "\n".join(
            [
                line
                for line in output.splitlines()
                if not any(
                    key in line
                    for key in [
                        "bitrate=",
                        "total_size=",
                        "out_time_us=",
                        "out_time_ms=",
                        "out_time=",
                        "dup_frames=",
                        "drop_frames=",
                        "speed=",
                        "progress=",
                    ]
                )
            ]
        )

    def run_ffmpeg_command(self, cmd: list[str]) -> Iterator[float]:
        """
        Run an ffmpeg command

        Yields:
            float: Progress percentage
        """
        # wrapper for 'ffmpeg-progress-yield'
        _logger.debug(f"Running command: {shlex.join(cmd)}")
        with FfmpegProgress(cmd, dry_run=self.dry) as ff:
            yield from ff.run_command_with_progress(
                popen_kwargs={"env": _get_ffmpeg_env()}
            )

            self.output = ff.stderr

        if _logger.getEffectiveLevel() == logging.DEBUG and self.output is not None:
            _logger.debug(
                f"ffmpeg output: {CommandRunner.prune_ffmpeg_progress_from_output(self.output)}"
            )

    def run_command(self, cmd: list[str]) -> CommandRunner:
        """
        Run a command with subprocess

        Returns:
            CommandRunner: itself

        Raises:
            RuntimeError: If command returns non-zero exit code
        """
        _logger.debug(f"Running command: {shlex.join(cmd)}")

        if self.dry:
            _logger.debug("Dry mode specified, not actually running command")
            return self

        p = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,  # Apply stdin isolation by creating separate pipe.
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=False,
            env=_get_ffmpeg_env(),
        )

        stdout_bytes, stderr_bytes = p.communicate()

        stdout = stdout_bytes.decode("utf8", errors="replace")
        stderr = stderr_bytes.decode("utf8", errors="replace")

        if p.returncode != 0:
            raise RuntimeError(f"Error running command {shlex.join(cmd)}: {stderr}")

        self.output = stdout + stderr
        return self

    def get_output(self) -> str:
        if self.output is None:
            raise FFmpegNormalizeError("Command has not been run yet")
        return self.output


def dict_to_filter_opts(opts: dict[str, Any]) -> str:
    """
    Convert a dictionary to a ffmpeg filter option string

    Args:
        opts (dict[str, Any]): Dictionary of options

    Returns:
        str: Filter option string
    """
    filter_opts = []
    for k, v in opts.items():
        filter_opts.append(f"{k}={v}")
    return ":".join(filter_opts)


def get_ffmpeg_exe() -> str:
    """
    Return path to ffmpeg executable

    Returns:
        str: Path to ffmpeg executable

    Raises:
        FFmpegNormalizeError: If ffmpeg is not found
    """
    if ff_path := os.getenv("FFMPEG_PATH"):
        if os.sep in ff_path:
            if not os.path.isfile(ff_path):
                raise FFmpegNormalizeError(f"No file exists at {ff_path}")

            return ff_path

        ff_exe = which(ff_path)
        if not ff_exe:
            raise FFmpegNormalizeError(f"Could not find '{ff_path}' in your $PATH.")

        return ff_exe

    ff_path = which("ffmpeg")
    if not ff_path:
        raise FFmpegNormalizeError(
            "Could not find ffmpeg in your $PATH or $FFMPEG_PATH. "
            "Please install ffmpeg from http://ffmpeg.org"
        )

    return ff_path


_encoder_sample_formats_cache: dict[str, list[str]] = {}


def get_encoder_sample_formats(encoder: str) -> list[str]:
    """
    Return the list of sample formats supported by an ffmpeg audio encoder.

    The result is parsed from ``ffmpeg -h encoder=<encoder>`` and cached per
    encoder for the lifetime of the process.

    Args:
        encoder: Name of the ffmpeg audio encoder (e.g. "flac").

    Returns:
        list[str]: Supported sample formats (e.g. ["s16", "s32"]), or an empty
            list if they could not be determined.
    """
    if encoder in _encoder_sample_formats_cache:
        return _encoder_sample_formats_cache[encoder]

    formats: list[str] = []
    try:
        output = (
            CommandRunner()
            .run_command([get_ffmpeg_exe(), "-hide_banner", "-h", f"encoder={encoder}"])
            .get_output()
        )
        if match := re.search(r"Supported sample formats:\s*(.+)", output):
            formats = match.group(1).split()
    except (RuntimeError, FFmpegNormalizeError) as e:
        _logger.debug(
            f"Could not determine sample formats for encoder '{encoder}': {e}"
        )

    _encoder_sample_formats_cache[encoder] = formats
    return formats


_codec_encoders_cache: dict[str, list[str]] | None = None
_muxer_default_encoder_cache: dict[str, str | None] = {}


def _get_codec_encoders() -> dict[str, list[str]]:
    """
    Map each ffmpeg codec name to its available encoders.

    Parsed once from ``ffmpeg -codecs`` and cached for the process lifetime. A
    codec with no explicit ``(encoders: ...)`` list uses an encoder of the same
    name, so it maps to an empty list here.

    Returns:
        dict[str, list[str]]: Mapping of codec name to encoder names.
    """
    global _codec_encoders_cache
    if _codec_encoders_cache is not None:
        return _codec_encoders_cache

    encoders: dict[str, list[str]] = {}
    try:
        output = (
            CommandRunner()
            .run_command([get_ffmpeg_exe(), "-hide_banner", "-codecs"])
            .get_output()
        )
        for line in output.splitlines():
            # Rows look like: " DEAIL. opus  Opus ... (encoders: opus libopus)"
            match = re.match(r"\s*[D.][E.][AVS.][I.][L.][S.]\s+([A-Za-z0-9_]+)", line)
            if not match:
                continue
            enc_match = re.search(r"\(encoders:([^)]*)\)", line)
            encoders[match.group(1)] = enc_match.group(1).split() if enc_match else []
    except (RuntimeError, FFmpegNormalizeError) as e:
        _logger.debug(f"Could not list ffmpeg codecs: {e}")

    _codec_encoders_cache = encoders
    return encoders


def _resolve_encoder_for_codec(codec_id: str) -> str:
    """
    Return the encoder ffmpeg uses by default for a codec id.

    This mirrors ffmpeg's own selection when no encoder is given on the command
    line: the external library wrapper (e.g. ``libopus``) is preferred over an
    experimental native encoder of the same name (``opus``). Codecs without an
    explicit encoder list use an encoder named like the codec itself.

    Args:
        codec_id: The codec id as reported by ffmpeg (e.g. "opus", "flac").

    Returns:
        str: The encoder name to pass to ``-c:a``.
    """
    encoders = _get_codec_encoders().get(codec_id, [])
    lib_variant = f"lib{codec_id}"
    if lib_variant in encoders:
        return lib_variant
    if encoders:
        return encoders[0]
    return codec_id


def get_muxer_default_audio_encoder(container: str) -> str | None:
    """
    Return the audio encoder ffmpeg would use by default for a container.

    This replicates ffmpeg's own per-container choice when no ``-c:a`` is given,
    rather than hardcoding a table, so it tracks whatever the installed ffmpeg
    does (e.g. ``.ogg`` may default to flac on some builds). The container's
    default audio codec is read from ``ffmpeg -h muxer=<name>`` and then mapped
    to a concrete, non-experimental encoder via _resolve_encoder_for_codec().

    Results are cached per container for the process lifetime, so batch runs only
    query ffmpeg once per container.

    Args:
        container: Output file extension or ffmpeg format name without a leading
            dot (e.g. "flac", "m4a", "ipod").

    Returns:
        str | None: The encoder name (e.g. "flac", "libopus"), or None if it
            could not be determined.
    """
    container = container.lower()
    if container in _muxer_default_encoder_cache:
        return _muxer_default_encoder_cache[container]

    muxer = _MUXER_NAME_FOR_EXT.get(container, container)
    encoder: str | None = None
    try:
        output = (
            CommandRunner()
            .run_command([get_ffmpeg_exe(), "-hide_banner", "-h", f"muxer={muxer}"])
            .get_output()
        )
        if match := re.search(r"Default audio codec:\s*([A-Za-z0-9_]+)", output):
            encoder = _resolve_encoder_for_codec(match.group(1))
    except (RuntimeError, FFmpegNormalizeError) as e:
        _logger.debug(
            f"Could not determine default audio codec for container '{container}': {e}"
        )

    _muxer_default_encoder_cache[container] = encoder
    return encoder


def ffmpeg_has_loudnorm() -> bool:
    """
    Run feature detection on ffmpeg to see if it supports the loudnorm filter.

    Returns:
        bool: True if loudnorm is supported, False otherwise
    """
    output = CommandRunner().run_command([get_ffmpeg_exe(), "-filters"]).get_output()
    supports_loudnorm = "loudnorm" in output
    if not supports_loudnorm:
        _logger.error(
            "Your ffmpeg does not support the 'loudnorm' filter. "
            "Please make sure you are running ffmpeg v4.2 or above."
        )
    return supports_loudnorm


def validate_input_file(input_file: str) -> tuple[bool, str | None]:
    """
    Validate that an input file exists, is readable, and contains audio streams.

    This function performs a lightweight probe of the file using ffmpeg to check
    if it can be read and contains at least one audio stream.

    Args:
        input_file: Path to the input file to validate

    Returns:
        tuple: (is_valid, error_message)
            - is_valid: True if the file is valid, False otherwise
            - error_message: None if valid, otherwise a descriptive error message
    """
    # Check if file exists
    if not os.path.exists(input_file):
        return False, f"File does not exist: {input_file}"

    # Check if it's actually a file (not a directory)
    if not os.path.isfile(input_file):
        return False, f"Path is not a file: {input_file}"

    # Check if file is readable
    if not os.access(input_file, os.R_OK):
        return False, f"File is not readable (permission denied): {input_file}"

    # Check if file has audio streams using ffmpeg probe
    ffmpeg_exe = get_ffmpeg_exe()
    cmd = [
        ffmpeg_exe,
        "-i",
        input_file,
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

    try:
        output = CommandRunner().run_command(cmd).get_output()
    except RuntimeError as e:
        error_str = str(e)
        # Extract a cleaner error message from ffmpeg output
        if "Invalid data found" in error_str:
            return False, f"Invalid or corrupted media file: {input_file}"
        if "No such file or directory" in error_str:
            return False, f"File not found or cannot be opened: {input_file}"
        if "Permission denied" in error_str:
            return False, f"Permission denied when reading file: {input_file}"
        if "does not contain any stream" in error_str:
            return False, f"File contains no media streams: {input_file}"
        # Generic error for other ffmpeg failures
        return False, f"Cannot read media file: {input_file}"

    # Check for audio streams in the output
    has_audio = False
    for line in output.split("\n"):
        if line.strip().startswith("Stream") and "Audio" in line:
            has_audio = True
            break

    if not has_audio:
        return False, f"File does not contain any audio streams: {input_file}"

    return True, None
