# Installation

## Python Package

For Python 3 and pip:

```bash
pip3 install ffmpeg-normalize
```

Or download this repository, then run `pip3 install .`.

To later upgrade to the latest version, run `pip3 install --upgrade ffmpeg-normalize`.

## Shell Completions

This tool provides shell completions for bash and zsh. To install them:

### Bash

If you have [`bash-completion`](https://github.com/scop/bash-completion) installed, you can just copy your new completion script to the `/usr/local/etc/bash_completion.d` directory.

```bash
curl -L https://raw.githubusercontent.com/slhck/ffmpeg-normalize/master/completions/ffmpeg-normalize-completion.bash \
  -o /usr/local/etc/bash_completion.d/ffmpeg-normalize
```

Without bash-completion, you can manually install the completion script:

```bash
# create completions directory if it doesn't exist
mkdir -p ~/.bash_completions.d

# download and install completion script
curl -L https://raw.githubusercontent.com/slhck/ffmpeg-normalize/master/completions/ffmpeg-normalize-completion.bash \
  -o ~/.bash_completions.d/ffmpeg-normalize

# source it in your ~/.bashrc
echo 'source ~/.bash_completions.d/ffmpeg-normalize' >> ~/.bashrc
```

### Zsh

Download the completion script and place it in the default `site-functions` directory:

```bash
curl -L https://raw.githubusercontent.com/slhck/ffmpeg-normalize/master/completions/ffmpeg-normalize.zsh \
  -o /usr/local/share/zsh/site-functions/
```

You may choose any other directory that is in your `$FPATH` variable.
Make sure your `.zshrc` file contains `autoload -Uz compinit && compinit`.
