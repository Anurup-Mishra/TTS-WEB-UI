# Multilingual Audiobook / TTS Pipeline — Web UI (Flask)

Minimal demo: Flask web UI that synthesizes text to speech using Coqui TTS (neural) with pyttsx3 fallback, and optional background music mixing via pydub/ffmpeg.

Features
- Paste or upload text to synthesize.
- Choose engine: Coqui TTS (high-quality) or pyttsx3 (offline fallback).
- Set speaking rate (words per minute).
- Optionally upload background music (MP3/WAV) to mix with the voice output.
- Download MP3 output.

Requirements
- Python 3.9+
- ffmpeg installed and in PATH (required by pydub)
- Recommended: GPU if using large Coqui models (optional)

Quick start
1. Copy files into a project folder preserving the structure.
2. Create and activate a virtual environment:
   python -m venv .venv
   source .venv/bin/activate   # macOS / Linux
   .venv\Scripts\activate      # Windows (PowerShell/cmd)
3. Install dependencies:
   pip install -r requirements.txt
4. Run the app:
   export FLASK_APP=app.py
   flask run
   Open http://127.0.0.1:5000 in your browser.

Notes
- Coqui model choice: the scaffold defaults to "tts_models/en/ljspeech/tacotron2-DDC". Change in `tts/synth.py` if you need another language/voice.
- Coqui TTS models can be large; for CPU-only testing use a small model or expect slower synth times.
- For production use, run synthesis tasks in a background worker since model load and inference can be heavy.

If you want, I can:
- Add a Dockerfile and docker-compose
- Create a GitHub repo and push these files (provide owner/repo)
- Add a simple background worker (RQ/Celery) for async synth
