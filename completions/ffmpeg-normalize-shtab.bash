# AUTOMATICALLY GENERATED by `shtab`



_shtab_ffmpeg_normalize_option_strings=('-h' '--help' '-o' '--output' '-of' '--output-folder' '-f' '--force' '-d' '--debug' '-v' '--verbose' '-q' '--quiet' '-n' '--dry-run' '-pr' '--progress' '--version' '-nt' '--normalization-type' '-t' '--target-level' '-p' '--print-stats' '-lrt' '--loudness-range-target' '--keep-loudness-range-target' '--keep-lra-above-loudness-range-target' '-tp' '--true-peak' '--offset' '--lower-only' '--auto-lower-loudness-target' '--dual-mono' '--dynamic' '-c:a' '--audio-codec' '-b:a' '--audio-bitrate' '-ar' '--sample-rate' '-ac' '--audio-channels' '-koa' '--keep-original-audio' '-prf' '--pre-filter' '-pof' '--post-filter' '-vn' '--video-disable' '-c:v' '--video-codec' '-sn' '--subtitle-disable' '-mn' '--metadata-disable' '-cn' '--chapters-disable' '-ei' '--extra-input-options' '-e' '--extra-output-options' '-ofmt' '--output-format' '-ext' '--extension')



_shtab_ffmpeg_normalize__nt_choices=('ebu' 'rms' 'peak')
_shtab_ffmpeg_normalize___normalization_type_choices=('ebu' 'rms' 'peak')

_shtab_ffmpeg_normalize_pos_0_nargs=+
_shtab_ffmpeg_normalize__h_nargs=0
_shtab_ffmpeg_normalize___help_nargs=0
_shtab_ffmpeg_normalize__o_nargs=+
_shtab_ffmpeg_normalize___output_nargs=+
_shtab_ffmpeg_normalize__f_nargs=0
_shtab_ffmpeg_normalize___force_nargs=0
_shtab_ffmpeg_normalize__d_nargs=0
_shtab_ffmpeg_normalize___debug_nargs=0
_shtab_ffmpeg_normalize__v_nargs=0
_shtab_ffmpeg_normalize___verbose_nargs=0
_shtab_ffmpeg_normalize__q_nargs=0
_shtab_ffmpeg_normalize___quiet_nargs=0
_shtab_ffmpeg_normalize__n_nargs=0
_shtab_ffmpeg_normalize___dry_run_nargs=0
_shtab_ffmpeg_normalize__pr_nargs=0
_shtab_ffmpeg_normalize___progress_nargs=0
_shtab_ffmpeg_normalize___version_nargs=0
_shtab_ffmpeg_normalize__p_nargs=0
_shtab_ffmpeg_normalize___print_stats_nargs=0
_shtab_ffmpeg_normalize___keep_loudness_range_target_nargs=0
_shtab_ffmpeg_normalize___keep_lra_above_loudness_range_target_nargs=0
_shtab_ffmpeg_normalize___lower_only_nargs=0
_shtab_ffmpeg_normalize___auto_lower_loudness_target_nargs=0
_shtab_ffmpeg_normalize___dual_mono_nargs=0
_shtab_ffmpeg_normalize___dynamic_nargs=0
_shtab_ffmpeg_normalize__koa_nargs=0
_shtab_ffmpeg_normalize___keep_original_audio_nargs=0
_shtab_ffmpeg_normalize__vn_nargs=0
_shtab_ffmpeg_normalize___video_disable_nargs=0
_shtab_ffmpeg_normalize__sn_nargs=0
_shtab_ffmpeg_normalize___subtitle_disable_nargs=0
_shtab_ffmpeg_normalize__mn_nargs=0
_shtab_ffmpeg_normalize___metadata_disable_nargs=0
_shtab_ffmpeg_normalize__cn_nargs=0
_shtab_ffmpeg_normalize___chapters_disable_nargs=0


# $1=COMP_WORDS[1]
_shtab_compgen_files() {
  compgen -f -- $1  # files
}

# $1=COMP_WORDS[1]
_shtab_compgen_dirs() {
  compgen -d -- $1  # recurse into subdirs
}

# $1=COMP_WORDS[1]
_shtab_replace_nonword() {
  echo "${1//[^[:word:]]/_}"
}

# set default values (called for the initial parser & any subparsers)
_set_parser_defaults() {
  local subparsers_var="${prefix}_subparsers[@]"
  sub_parsers=${!subparsers_var-}

  local current_option_strings_var="${prefix}_option_strings[@]"
  current_option_strings=${!current_option_strings_var}

  completed_positional_actions=0

  _set_new_action "pos_${completed_positional_actions}" true
}

# $1=action identifier
# $2=positional action (bool)
# set all identifiers for an action's parameters
_set_new_action() {
  current_action="${prefix}_$(_shtab_replace_nonword $1)"

  local current_action_compgen_var=${current_action}_COMPGEN
  current_action_compgen="${!current_action_compgen_var-}"

  local current_action_choices_var="${current_action}_choices[@]"
  current_action_choices="${!current_action_choices_var-}"

  local current_action_nargs_var="${current_action}_nargs"
  if [ -n "${!current_action_nargs_var-}" ]; then
    current_action_nargs="${!current_action_nargs_var}"
  else
    current_action_nargs=1
  fi

  current_action_args_start_index=$(( $word_index + 1 - $pos_only ))

  current_action_is_positional=$2
}

# Notes:
# `COMPREPLY`: what will be rendered after completion is triggered
# `completing_word`: currently typed word to generate completions for
# `${!var}`: evaluates the content of `var` and expand its content as a variable
#     hello="world"
#     x="hello"
#     ${!x} -> ${hello} -> "world"
_shtab_ffmpeg_normalize() {
  local completing_word="${COMP_WORDS[COMP_CWORD]}"
  local completed_positional_actions
  local current_action
  local current_action_args_start_index
  local current_action_choices
  local current_action_compgen
  local current_action_is_positional
  local current_action_nargs
  local current_option_strings
  local sub_parsers
  COMPREPLY=()

  local prefix=_shtab_ffmpeg_normalize
  local word_index=0
  local pos_only=0 # "--" delimeter not encountered yet
  _set_parser_defaults
  word_index=1

  # determine what arguments are appropriate for the current state
  # of the arg parser
  while [ $word_index -ne $COMP_CWORD ]; do
    local this_word="${COMP_WORDS[$word_index]}"

    if [[ $pos_only = 1 || " $this_word " != " -- " ]]; then
      if [[ -n $sub_parsers && " ${sub_parsers[@]} " == *" ${this_word} "* ]]; then
        # valid subcommand: add it to the prefix & reset the current action
        prefix="${prefix}_$(_shtab_replace_nonword $this_word)"
        _set_parser_defaults
      fi

      if [[ " ${current_option_strings[@]} " == *" ${this_word} "* ]]; then
        # a new action should be acquired (due to recognised option string or
        # no more input expected from current action);
        # the next positional action can fill in here
        _set_new_action $this_word false
      fi

      if [[ "$current_action_nargs" != "*" ]] && \
         [[ "$current_action_nargs" != "+" ]] && \
         [[ "$current_action_nargs" != *"..." ]] && \
         (( $word_index + 1 - $current_action_args_start_index - $pos_only >= \
            $current_action_nargs )); then
        $current_action_is_positional && let "completed_positional_actions += 1"
        _set_new_action "pos_${completed_positional_actions}" true
      fi
    else
      pos_only=1 # "--" delimeter encountered
    fi

    let "word_index+=1"
  done

  # Generate the completions

  if [[ $pos_only = 0 && "${completing_word}" == -* ]]; then
    # optional argument started: use option strings
    COMPREPLY=( $(compgen -W "${current_option_strings[*]}" -- "${completing_word}") )
  else
    # use choices & compgen
    local IFS=$'\n' # items may contain spaces, so delimit using newline
    COMPREPLY=( $([ -n "${current_action_compgen}" ] \
                  && "${current_action_compgen}" "${completing_word}") )
    unset IFS
    COMPREPLY+=( $(compgen -W "${current_action_choices[*]}" -- "${completing_word}") )
  fi

  return 0
}

complete -o filenames -F _shtab_ffmpeg_normalize ffmpeg-normalize
