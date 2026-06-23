from pydub import AudioSegment
import os

def mix_with_music(voice_path: str, music_path: str, out_path: str, music_level_db: float = -18.0):
    """
    Mix voice (voice_path) with background music (music_path).
    - music_level_db: approximate gain to apply to music (negative values reduce music level)
    Produces out_path (mp3 or wav depending on out_path extension).
    """
    voice = AudioSegment.from_file(voice_path)
    # Normalize voice to around -3 dBFS to help mixing
    try:
        voice = voice.normalize()
    except Exception:
        pass

    music = AudioSegment.from_file(music_path)
    # Apply gain to music (lower it)
    music = music.apply_gain(music_level_db)

    # Loop or trim the music to match voice length
    if len(music) < len(voice):
        # loop music
        repeats = int(len(voice) / len(music)) + 1
        music = music * repeats
    music = music[:len(voice)]

    # Overlay voice onto music; voice on top (no ducking logic here for simplicity)
    mixed = music.overlay(voice)

    ext = os.path.splitext(out_path)[1].lstrip(".").lower()
    # default to mp3
    if ext == "mp3":
        mixed.export(out_path, format="mp3", bitrate="192k")
    else:
        mixed.export(out_path, format=ext or "mp3")
    return out_path
