import argparse
from pathlib import Path
import sys
from models import TTSOptions

base_params = TTSOptions(
    model_name="tts_models/multilingual/multi-dataset/xtts_v2",
    speaker_wav=[
        "samples/derekjacobi_illidad3.wav"
    ],
    language_idx="en",
    title=""

)


tts_base = None


def init_tts():
    print("Init TTS")
    print("Checking samples")

    # Ensure all base speaker_wav samples exist
    missing = [p for p in base_params["speaker_wav"] if not Path(p).exists()]
    if missing:
        print("Missing speaker wavs:", file=sys.stderr)
        for p in missing:
            print(p, file=sys.stderr)
        sys.exit(1)

    print("Starting imports")
    from TTS.api import TTS
    import torch
    print("Get device")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print("Attaching model to device")

    return TTS(base_params["model_name"]).to(device)


tts_base = None


def xtts(text, file_path, speed=1):
    global tts_base 

    if tts_base == None:
        tts_base = init_tts()
    tts_base.tts_to_file(
        text=text,
        file_path=file_path,
        speaker_wav=base_params["speaker_wav"],
        language=base_params["language_idx"],
        speed=speed
    )


def main():
    parser = argparse.ArgumentParser(description="Run XTTS")
    parser.add_argument("text", help="Text to speak")
    parser.add_argument("out", help="Output file")
    parser.add_argument("--speed", 	type=int, default=1, help="Speed modifier")

    args = parser.parse_args()
    xtts(args.text, args.out, args.speed)


if __name__ == "__main__":
    main()
