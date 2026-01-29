from models import TTSOptions
from pathlib import Path
import os
import sys
import argparse

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


def srt_to_dict(srt_text):
	blocks = srt_text.strip().split("\n\n")
	parsed = []

	for block in blocks:
		lines = block.splitlines()
		if len(lines) < 3:
			continue

		index = lines[0]
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
	parser.add_argument("text_file", help="Path to input text or SRT file")
	parser.add_argument("-o", "--out", default="output.wav", help="Output wav path")

	args = parser.parse_args()

	text_path = Path(args.text_file)
	if not text_path.exists():
		print("Text/SRT file not found", file=sys.stderr)
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
	print(done_files)
	# exit()
	# tts = init_tts()
	str_json=srt_to_dict(text)
	i=0
	print("Parsed file", len(str_json), "blocks to complete")
	for block in str_json:
		print("starting block", i,"out of" ,len(str_json))
		if i>3:
			print("limit reached")
			break
		i+=1
		filename = block["index"] + ".wav"
		if filename in done_files:
			print(filename, "done, skipping")
			continue

		path = work_dir/filename
		

		print("making audio",block["text"],path)

		# # Run TTS to file
		# tts.tts_to_file(
		# 	text=block["text"],
		# 	file_path=path,
		# 	speaker_wav=base_params["speaker_wav"],
		# 	language=base_params["language_idx"]
		# )
		

	print("done")

		
	exit()
	



	print(f"Output written to {args.out}")
	print(f"Working directory: {work_dir}")


if __name__ == "__main__":
	main()
