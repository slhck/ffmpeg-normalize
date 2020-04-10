#!/bin/bash
#
# Bump the version, create changelog, and push to Git
#
# Requirements:
# - `pip3 install wheel twine pypandoc gitchangelog pystache`
set -e

# define the file containing the version here
VERSION_FILE="ffmpeg_normalize/_version.py"

# run checks
for package in pypandoc twine wheel gitchangelog pystache; do
    python -c "import ${package}" || { echo >&2 "${package} is not installed. Install via pip!"; exit 1; }
done

[[ -z $(git status -s) ]] || { echo >&2 "repo is not clean, commit everything first!"; exit 1; }

LATEST_HASH="$(git log --pretty=format:'%h' -n 1)"

BASE_STRING=$(grep -Eo '[0-9]+\.[0-9]+\.[0-9]+' "$VERSION_FILE")
BASE_LIST=(`echo $BASE_STRING | tr '.' ' '`)
V_MAJOR=${BASE_LIST[0]}
V_MINOR=${BASE_LIST[1]}
V_PATCH=${BASE_LIST[2]}
echo -e "Current version: $BASE_STRING"
echo -e " Latest commit hash: $LATEST_HASH"
V_MINOR=$((V_MINOR + 1))
V_PATCH=0
SUGGESTED_VERSION="$V_MAJOR.$V_MINOR.$V_PATCH"
echo -ne "Enter a version number [$SUGGESTED_VERSION]: "
read INPUT_STRING
if [ "$INPUT_STRING" = "" ]; then
    INPUT_STRING="$SUGGESTED_VERSION"
fi
echo -e "Will set new version to be $INPUT_STRING"

# replace the version
perl -pi -e "s/\Q$BASE_STRING\E/$INPUT_STRING/" "$VERSION_FILE"

git add "$VERSION_FILE"

# bump initially but to not push yet
git commit -m "Bump version to ${INPUT_STRING}."
git tag -a -m "Tag version ${INPUT_STRING}." "v$INPUT_STRING"

# generate the changelog
gitchangelog > CHANGELOG.md

# add the changelog and amend it to the previous commit and tag
git add CHANGELOG.md
git commit --amend --no-edit
git tag -a -f -m "Tag version ${INPUT_STRING}." "v$INPUT_STRING"

# push to remote
echo "Pushing new version to origin..."
git push && git push --tags

# upload to PyPi
rm -rf dist/* build
python3 setup.py sdist bdist_wheel
python3 -m twine upload dist/*
