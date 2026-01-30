from models import TTSOptions
from pathlib import Path
import os
import sys
import argparse
import re
from timescale import speed_up_clip 

from moviepy import AudioFileClip, CompositeAudioClip,VideoFileClip,afx, vfx



base_params = TTSOptions(
	model_name="tts_models/multilingual/multi-dataset/xtts_v2",
	speaker_wav=[
		"samples/derekjacobi_illidad3.wav"
	],
	language_idx="en",
	title=""
)


def init_tts():
	print("Init TTS")
	print("Starting imports")
	from TTS.api import TTS
	import torch
	print("Get device")
	device = "cuda" if torch.cuda.is_available() else "cpu"
	print("Attaching model to device")

	return TTS(base_params["model_name"]).to(device)

def srt_time_to_sec(timing_str):
	start_str, end_str = timing_str.split(" --> ")
	def parse_time(s):
		h, m, sec_ms = s.split(":")
		s, ms = sec_ms.split(",")
		return int(h)*3600 + int(m)*60 + int(s) + int(ms)/1000
	return parse_time(start_str), parse_time(end_str)





def srt_to_dict(srt_text):
	blocks = srt_text.strip().split("\n\n")
	parsed = []

	for block in blocks:
		lines = block.splitlines()
		if len(lines) < 3:
			continue
		index = re.sub(r"\D", "", lines[0])
		

		timing = lines[1]
		text = "\n".join(lines[2:])

		parsed.append({
			"index": index,
			"timing": timing,
			"text": text
		})

	return parsed


def dict_to_srt(parsed_srt):
	lines = []
	for block in parsed_srt:
		index = block.get("index", "")
		timing = block.get("timing", "")
		text = block.get("text", "")
		lines.append(f"{index}\n{timing}\n{text}")
	return "\n\n".join(lines)


def main():
	parser = argparse.ArgumentParser(description="Run XTTS from text/SRT file")
	parser.add_argument("srt", help="Path to input text or SRT file")
	parser.add_argument("video", help="Video for this SRT file")
	parser.add_argument("--dryrun", action="store_true", help="Dryrun mode")
	parser.add_argument("--limit", 	type=int, default=None, help="Limits the number of lines, usually shortening the video")
	parser.add_argument("--nonalign", 	action="store_true",help="Dont try to shink audio files that are too long")

	args = parser.parse_args()

	
	text_path = Path(args.srt)
	if not text_path.exists():
		print("Text/SRT file not found", file=sys.stderr)
		sys.exit(1)
	
	video_path = Path(args.video)
	if not video_path.exists():
		print("Video file not found", file=sys.stderr)
		sys.exit(1)
	

	# Ensure all base speaker_wav samples exist
	missing = [p for p in base_params["speaker_wav"] if not Path(p).exists()]
	if missing:
		print("Missing speaker wavs:", file=sys.stderr)
		for p in missing:
			print(p, file=sys.stderr)
		sys.exit(1)

	# Create a working folder per input file (SRT or text)
	work_dir = Path("work") / text_path.stem
	try:
		work_dir.mkdir(parents=True, exist_ok=True)
	except Exception as e:
		print(f"Failed to create work dir: {work_dir}", file=sys.stderr)
		print(e, file=sys.stderr)
		sys.exit(1)

	# Read text content
	text = text_path.read_text(encoding="utf-8")
	if not text:
		print("Text/SRT file is empty", file=sys.stderr)
		sys.exit(1)


	if text_path.suffix != ".srt":
		print("str only", file=sys.stderr)
		sys.exit(1)

	done_files = [x.name for x in list(work_dir.glob("*.wav"))]
	print("starting", text_path.name, len(done_files), "files already completed")
	# exit()
	tts=None
	
	str_json=srt_to_dict(text)
	i=0
	print("Parsed file", len(str_json), "blocks to complete")
	for block, next_block in zip(str_json, str_json[1:]+ [None]):

		print("starting block", i,"out of" ,len(str_json))

		start, end = srt_time_to_sec(block["timing"])
		block_duration = end-start
		print("normal duration", block_duration)
		if next_block:
			next_start, next_end = srt_time_to_sec(next_block["timing"])
			if next_start-start-.2>block_duration:
				block_duration =next_start-start-.2
				print("extra duration", block_duration)

		
		if args.limit is not None and i>args.limit:
			print("limit reached")
			break
		i+=1
		filename ="_"+ block["index"] + ".wav"
		print(block)


		if filename in done_files:
			print(filename, "done, skipping")
			continue

		path = work_dir/filename
		
		# handle speed
		speed_factor=1
		avg_speaking_speed=2.33 #average words per m
		words = re.findall(r'\b\w+\b', block["text"])
		s = len(words)/(block_duration *avg_speaking_speed) 
		if s>1:
			print("this block should contain", block_duration *avg_speaking_speed, "words but contains",len(words))
			print("speeding up speech for this block by", s)
			speed_factor=s*1.5

		print("making audio",block["text"],path)

	


		# # Run TTS to file
		if not tts and not args.dryrun:
			tts = init_tts()
		if tts:
			while True:
				tts.tts_to_file(
					text=block["text"],
					file_path=path,
					speaker_wav=base_params["speaker_wav"],
					language=base_params["language_idx"],
					speed=speed_factor
				)
				clip = AudioFileClip(str(path))
				clip_duration = clip.duration
				
				if clip_duration>block_duration:
					speed_factor*=1.5
					print(f"generated clip too long ({clip_duration} vs {block_duration}), retrying with higher speed factor ({speed_factor})", )
					continue
				print(f"audio complete {clip_duration} vs {block_duration}")
				break
	print("tts done")
	print("making combined audio file")
	
	# for file in [x for x in list(work_dir.glob("*.wav"))]:
	i=0
	clips=[]
	for block in str_json:
		

		if args.limit is not None and i>args.limit:
			print("limit reached")
			break
		i+=1

		index=block["index"]
		wav_file = work_dir / f"_{index}.wav"
		if not wav_file.exists():
			print(f"Warning: {wav_file} not found, aborting")
			sys.exit(1)

		start, end = srt_time_to_sec(block["timing"])

		block_duration = end-start

		clip = AudioFileClip(str(wav_file))
		clip_duration = clip.duration

		speed_factor = clip_duration/block_duration 
		if speed_factor>1:
			print("this clip is too slow and will overlap its peer", block["index"])
			# clip = speed_up_clip(clip,speed_factor)

		clip=clip.with_start(start)
		# print(block_duration , clip_duration)
		# print(clip_duration, speed_factor)
		# exit()
		clips.append(clip)



		print(wav_file,start,end)
	combined_path = work_dir/"combined.wav"
	combined = CompositeAudioClip(clips)
	combined.write_audiofile(str(combined_path))

	print("updating video with new audio")
	if args.dryrun:
		print("skipping file creation")
		exit()


	video_output_path = video_path.parent / f"dubbed {video_path.name}"

	video = VideoFileClip(video_path)

	# Load audio
	new_audio = AudioFileClip(str(combined_path))

	# Truncate audio slightly to avoid MoviePy overshoot
	truncated_audio = new_audio.subclipped(0, new_audio.duration - 0.05)  # 50ms shorter

	# Clip video to match truncated audio
	video = video.subclipped(0, truncated_audio.duration)

	# Replace audio
	video = video.with_audio(truncated_audio)

	# Export
	video.write_videofile(
		video_output_path,
		codec="libx264",
		audio_codec="aac",
		temp_audiofile="temp-audio.m4a",
		remove_temp=True
	)


	print("finished", "wrote video to", video_output_path)



		
	exit()
	



	print(f"Output written to {args.out}")
	print(f"Working directory: {work_dir}")


if __name__ == "__main__":
	main()
