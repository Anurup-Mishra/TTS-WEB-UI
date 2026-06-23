import os
import tempfile
from typing import Optional
from pydub import AudioSegment

try:
    from TTS.api import TTS
    COQUI_AVAILABLE = True
except Exception:
    COQUI_AVAILABLE = False

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except Exception:
    PYTTSX3_AVAILABLE = False

from .audio_utils import mix_with_music

# Defaulting to the XTTS model so voice cloning works automatically
DEFAULT_COQUI_MODEL = os.environ.get("COQUI_MODEL_NAME", "tts_models/multilingual/multi-dataset/xtts_v2")

class SynthesisManager:
    def __init__(self):
        self.coqui_model_name = DEFAULT_COQUI_MODEL
        self.coqui_tts = None  
        self.pytt_engine = None  

    def _ensure_coqui(self):
        if not COQUI_AVAILABLE:
            raise RuntimeError("Coqui TTS (TTS package) not installed.")
        if self.coqui_tts is None:
            self.coqui_tts = TTS(model_name=self.coqui_model_name, progress_bar=False, gpu=False)

    def _ensure_pyttsx3(self):
        if not PYTTSX3_AVAILABLE:
            raise RuntimeError("pyttsx3 not installed.")
        if self.pytt_engine is None:
            self.pytt_engine = pyttsx3.init()

    def synthesize_to_mp3(self, text: str, engine: str = "auto", rate: int = 150, music_path: Optional[str] = None, speaker_wav: Optional[str] = None) -> str:
        engine_choice = engine
        if engine == "auto":
            if COQUI_AVAILABLE:
                engine_choice = "coqui"
            elif PYTTSX3_AVAILABLE:
                engine_choice = "pyttsx3"
            else:
                raise RuntimeError("No TTS engine available. Install TTS or pyttsx3.")

        tmp_voice = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        tmp_voice.close()
        try:
            if engine_choice == "coqui":
                self._ensure_coqui()
           # If a custom voice file is provided, clone it
                if speaker_wav and os.path.exists(speaker_wav):
                    self.coqui_tts.tts_to_file(text=text, file_path=tmp_voice.name, speaker_wav=speaker_wav, language="en")
                
                # Otherwise, use the base/default AI voice
                else:
                    # Multi-speaker models like XTTS require a specific speaker name if not cloning
                    if self.coqui_tts.is_multi_speaker:
                        # Grab the very first built-in voice (e.g., "Claribel Dervla")
                        speaker_manager = self.coqui_tts.synthesizer.tts_model.speaker_manager
                        default_speaker = list(speaker_manager.name_to_id)[0]
                        self.coqui_tts.tts_to_file(text=text, file_path=tmp_voice.name, speaker=default_speaker, language="en")
                    else:
                        # For simpler single-speaker models
                        self.coqui_tts.tts_to_file(text=text, file_path=tmp_voice.name)
            
            elif engine_choice == "pyttsx3":
                self._ensure_pyttsx3()
                self.pytt_engine.setProperty("rate", rate)
                self.pytt_engine.save_to_file(text, tmp_voice.name)
                self.pytt_engine.runAndWait()
            else:
                raise ValueError(f"Unknown engine: {engine_choice}")

            if music_path:
                tmp_mixed = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tmp_mixed.close()
                mix_with_music(voice_path=tmp_voice.name, music_path=music_path, out_path=tmp_mixed.name)
                return tmp_mixed.name

            audio = AudioSegment.from_file(tmp_voice.name, format="wav")
            tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp_out.close()
            audio.export(tmp_out.name, format="mp3", bitrate="192k")
            return tmp_out.name
        finally:
            if os.path.exists(tmp_voice.name):
                os.remove(tmp_voice.name)