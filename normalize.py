#!/usr/bin/env python
#
# Audio normalization script, normalizing media files to WAV output
# 
# Requirements: Recent ffmpeg installed on your system (above 2.0 would suffice)
# Author: Werner Robitza

import argparse
import subprocess
import os
import re


args = dict()

def run_command(cmd, raw = False, dry = False):
    cmd = cmd.replace("  ", " ")
    cmd = cmd.replace("  ", " ")
    print_verbose("[command] {0}".format(cmd))

    if dry:
    	return

    if raw:
        output = subprocess.Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.STDOUT, shell = True).communicate()[0]
    else:
        output = subprocess.Popen(cmd.split(" "), stdout = subprocess.PIPE, stderr = subprocess.STDOUT).communicate()[0]
    return output


def ffmpeg_get_mean(input_file):
	cmd = 'ffmpeg -hide_banner -i "' + input_file + '" -filter:a "volumedetect" -vn -sn -f null /dev/null'
	output = run_command(cmd, True)
	mean_volume_matches = re.findall(r"mean_volume: ([\-\d\.]+) dB", output)
	if (mean_volume_matches):
		mean_volume = float(mean_volume_matches[0])
	else:
		print("[error] could not get mean volume for " + input_file)
		raise SystemExit

	max_volume_matches = re.findall(r"max_volume: ([\-\d\.]+) dB", output)
	if (max_volume_matches):
		max_volume = float(max_volume_matches[0])
	else:
		print("[error] could not get max volume for " + input_file)
		raise SystemExit
		
	return mean_volume, max_volume
	

def ffmpeg_adjust_volume(input_file, gain, output):
	global args
	if not args.force and os.path.exists(output):
		print_verbose("[warning] output file " + output + " already exists, skipping. Use -f to force overwriting.")
		return

	cmd = 'ffmpeg -y -i "' + input_file + '" -vn -sn -filter:a "volume=' + str(gain) + 'dB" -c:a pcm_s16le "' + output + '"'
	output = run_command(cmd, True, args.dry_run)
	#print(output)


def print_verbose(message):
	global args
	if args.verbose:
		print(message)

# -------------------------------------------------------------------------------------------------

parser = argparse.ArgumentParser(
	description='This program normalizes audio to a certain dB level.\n It takes any audio or video file as input, and writes the audio part as output WAV file.'
	)
parser.add_argument('-i', '--input', nargs='+', help='Input files to convert', required=True)
parser.add_argument('-f', '--force', default=False, action="store_true",
                    help='Force overwriting existing files')
parser.add_argument('-l', '--level', default=-26, help="dB level to normalize to, default: -26 dB")
parser.add_argument('-p', '--prefix', default="normalized", help="Normalized file prefix, default: normalized")
parser.add_argument('-v', '--verbose', default=False, action="store_true", help="Enable verbose output")
parser.add_argument('-n', '--dry-run', default=False, action="store_true", help="Show what would be done, do not convert")

args = parser.parse_args()

for input_file in args.input:
	if not os.path.exists(input_file):
		print("[error] file " + input_file + " does not exist")
		continue

	print_verbose("[info] reading file " + input_file)

	mean, maximum = ffmpeg_get_mean(input_file)
	print_verbose("[info] mean volume: " + str(mean))
	print_verbose("[info] max volume: " + str(maximum))

	target_level = args.level
	adjustment   = target_level - mean
	print_verbose("[info] file needs " + str(adjustment) + " dB gain to reach " + str(args.level) + " dB")

	if maximum + adjustment > 0:
		print("[warning] adjusting " + input_file + " will lead to clipping of " + str(maximum + adjustment) + "dB")

	path, filename = os.path.split(input_file)
	basename = os.path.splitext(filename)[0]
	
	ffmpeg_adjust_volume(input_file, adjustment, os.path.join(path, args.prefix + "-" + basename + ".wav"))
