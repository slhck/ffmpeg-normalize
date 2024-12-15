# Bash completion for ffmpeg-normalize
_ffmpeg_normalize()
{
    local cur prev opts
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main options
    opts="-o --output \
          -of --output-folder \
          -f --force \
          -d --debug \
          -v --verbose \
          -q --quiet \
          -n --dry-run \
          -pr --progress \
          --version \
          -nt --normalization-type \
          -t --target-level \
          -p --print-stats \
          -lrt --loudness-range-target \
          --keep-loudness-range-target \
          --keep-lra-above-loudness-range-target \
          --auto-lower-loudness-target \
          -tp --true-peak \
          --offset \
          --lower-only \
          --dual-mono \
          --dynamic \
          -c:a --audio-codec \
          -b:a --audio-bitrate \
          -ar --sample-rate \
          -ac --audio-channels \
          -koa --keep-original-audio \
          -prf --pre-filter \
          -pof --post-filter \
          -vn --video-disable \
          -c:v --video-codec \
          -sn --subtitle-disable \
          -mn --metadata-disable \
          -cn --chapters-disable \
          -ei --extra-input-options \
          -e --extra-output-options \
          -ofmt --output-format \
          -ext --extension"

    # Handle special completion cases
    case "${prev}" in
        -nt|--normalization-type)
            COMPREPLY=( $(compgen -W "ebu rms peak" -- ${cur}) )
            return 0
            ;;
        -o|--output|-of|--output-folder)
            # File/directory completion
            COMPREPLY=( $(compgen -f -- ${cur}) )
            return 0
            ;;
    esac

    # Complete options if current word starts with -
    if [[ ${cur} == -* ]] ; then
        COMPREPLY=( $(compgen -W "${opts}" -- ${cur}) )
        return 0
    fi

    # Complete with files by default
    COMPREPLY=( $(compgen -f -- ${cur}) )
    return 0
}

complete -F _ffmpeg_normalize ffmpeg-normalize
