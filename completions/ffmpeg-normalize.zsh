#compdef ffmpeg-normalize

_ffmpeg_normalize() {
  local -a args
  local context state line
  typeset -A opt_args

  args=(
    # File Input/Output
    '(-o --output)'{-o,--output}'[Output file names]:output file:_files'
    '(-of --output-folder)'{-of,--output-folder}'[Output folder (default: normalized)]:directory:_files -/'

    # General Options
    '(-f --force)'{-f,--force}'[Force overwrite existing files]'
    '(-d --debug)'{-d,--debug}'[Print debugging output]'
    '(-v --verbose)'{-v,--verbose}'[Print verbose output]'
    '(-q --quiet)'{-q,--quiet}'[Only print errors]'
    '(-n --dry-run)'{-n,--dry-run}'[Do not run normalization, only print what would be done]'
    '(-pr --progress)'{-pr,--progress}'[Show progress bar for files and streams]'
    '--version[Print version and exit]'

    # Normalization
    '(-nt --normalization-type)'{-nt,--normalization-type}'[Normalization type]:type:(ebu rms peak)'
    '(-t --target-level)'{-t,--target-level}'[Target level in dB/LUFS]:level:'
    '(-p --print-stats)'{-p,--print-stats}'[Print loudness statistics as JSON]'

    # EBU Options
    '(-lrt --loudness-range-target)'{-lrt,--loudness-range-target}'[EBU Loudness Range Target in LUFS]:range:'
    '--keep-loudness-range-target[Keep input loudness range target]'
    '--keep-lra-above-loudness-range-target[Keep input loudness range above target]'
    '--auto-lower-loudness-target[Automatically lower EBU Integrated Loudness Target]'
    '(-tp --true-peak)'{-tp,--true-peak}'[EBU Maximum True Peak in dBTP]:peak:'
    '--offset[EBU Offset Gain]:offset:'
    '--lower-only[Do not increase loudness]'
    '--dual-mono[Treat mono input as dual-mono]'
    '--dynamic[Force dynamic normalization mode]'

    # Audio Encoding
    '(-c:a --audio-codec)'{-c:a,--audio-codec}'[Audio codec]:codec:'
    '(-b:a --audio-bitrate)'{-b:a,--audio-bitrate}'[Audio bitrate]:bitrate:'
    '(-ar --sample-rate)'{-ar,--sample-rate}'[Audio sample rate]:sample rate:'
    '(-ac --audio-channels)'{-ac,--audio-channels}'[Number of audio channels]:channels:'
    '(-koa --keep-original-audio)'{-koa,--keep-original-audio}'[Keep original audio streams]'
    '(-prf --pre-filter)'{-prf,--pre-filter}'[Pre-normalization audio filter]:filter:'
    '(-pof --post-filter)'{-pof,--post-filter}'[Post-normalization audio filter]:filter:'

    # Video/Other Options
    '(-vn --video-disable)'{-vn,--video-disable}'[Disable video]'
    '(-c:v --video-codec)'{-c:v,--video-codec}'[Video codec]:codec:'
    '(-sn --subtitle-disable)'{-sn,--subtitle-disable}'[Disable subtitles]'
    '(-mn --metadata-disable)'{-mn,--metadata-disable}'[Disable metadata]'
    '(-cn --chapters-disable)'{-cn,--chapters-disable}'[Disable chapters]'

    # Format Options
    '(-ei --extra-input-options)'{-ei,--extra-input-options}'[Extra input options]:options:'
    '(-e --extra-output-options)'{-e,--extra-output-options}'[Extra output options]:options:'
    '(-ofmt --output-format)'{-ofmt,--output-format}'[Output format]:format:'
    '(-ext --extension)'{-ext,--extension}'[Output extension]:extension:'

    '*:input file:_files'
  )

  _arguments -s -S $args
}

_ffmpeg_normalize "$@"
