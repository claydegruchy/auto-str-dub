from moviepy import AudioFileClip
from moviepy.audio.AudioClip import AudioArrayClip
import librosa
import numpy as np

def speed_up_clip(clip, speed):
    """
    Speeds up an AudioClip without changing pitch.
    clip: any AudioClip
    speed: >1.0 speeds up, <1.0 slows down
    """
    samples = clip.to_soundarray(fps=clip.fps)
    sr = clip.fps

    # handle mono/stereo
    if samples.ndim == 2:
        left = librosa.effects.time_stretch(samples[:, 0], rate=speed)
        right = librosa.effects.time_stretch(samples[:, 1], rate=speed)
        stretched = np.stack([left, right], axis=1)
    else:
        stretched = librosa.effects.time_stretch(samples, rate=speed)

    # wrap in AudioArrayClip
    return AudioArrayClip(stretched, fps=sr)
