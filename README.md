# auto-str-dub
This is a python script that uses a local xtts model to automatically dub a video based on a supplied subtitle (.srt) file.

Works offline as long as you have the model already. Supports resuming translations.


# running

needs `uv` and a is built to run on mac, probably works on other systems but not tested

- `git clone https://github.com/claydegruchy/auto-str-dub.git`
- `uv venv` + activate
- `uv sync`
- `uv run main.py {srt} {video}`

# how
it takes a srt file and a video file 

1. creates a folder named after the srt file
2. split the srt up into blocks of text based on their index
3. for index each block:
   1. get the text for that block and run it through xtts
   2. save the resulting .wav to work/{folder}/{index}.wac
4. then once they're all done, sew them all together based on the timestamp for each block
5. save a copy of the supplied video with the cut together dub audio replacing the audio file to the same folder as the original

# why
i'm doing my hunting course and theres a lot of stuff in there in swedish. i already translated the subtitles (using [auto-str-translation-ai](https://github.com/claydegruchy/auto-str-translation-ai) which i also made) but i want to be able to watch without reading

also too many other things out there are too wonky for me