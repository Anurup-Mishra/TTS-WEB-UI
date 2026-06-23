import os
import tempfile
import uuid
from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from gtts import gTTS
from supabase import create_client, Client

# Import your TTS engine manager
from tts.synth import SynthesisManager

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")

# --- SUPABASE INIT ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ALLOWED_MUSIC_EXT = {"mp3", "wav", "ogg", "m4a"}
tts_manager = SynthesisManager()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_MUSIC_EXT

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/synthesize", methods=["POST"])
def synthesize():
    text = request.form.get("text", "").strip()
    engine = request.form.get("engine", "auto")
    rate = request.form.get("rate", type=int, default=150)
    target_lang = request.form.get("language", "en")
    
    if not text:
        flash("Please provide text to synthesize.", "error")
        return redirect(url_for("index"))

    # Background Music
    music_path = None
    music_file = request.files.get("music")
    if music_file and music_file.filename and allowed_file(music_file.filename):
        tmp_music = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(music_file.filename)[1])
        music_file.save(tmp_music.name)
        music_path = tmp_music.name

    # Voice Reference
    speaker_wav = None
    preset = request.form.get("preset_voice")
    if preset and preset != "none":
        speaker_wav = os.path.join(os.getcwd(), preset)
    
    voice_ref_file = request.files.get("voice_ref")
    if voice_ref_file and voice_ref_file.filename:
        tmp_voice_ref = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        voice_ref_file.save(tmp_voice_ref.name)
        speaker_wav = tmp_voice_ref.name

    try:
        if target_lang != "en":
            translated_text = GoogleTranslator(source='auto', target=target_lang).translate(text)
            tts = gTTS(text=translated_text, lang=target_lang)
            tmp_voice = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp_voice.close()
            tts.save(tmp_voice.name)
            out_path = tmp_voice.name
        else:
            out_path = tts_manager.synthesize_to_mp3(
                text=text, engine=engine, rate=rate, music_path=music_path, speaker_wav=speaker_wav
            )

        # --- SUPABASE UPLOAD & DB INSERT ---
        if supabase:
            # 1. Create a unique file name
            file_name = f"speech_{uuid.uuid4().hex[:8]}_{target_lang}.mp3"
            
            # 2. Read the generated file and upload to Storage
            with open(out_path, 'rb') as f:
                supabase.storage.from_('audio_files').upload(
                    file_name,
                    f.read(),
                    {"content-type": "audio/mpeg"}
                )
            
            # 3. Get the public URL for the newly uploaded file
            public_url = supabase.storage.from_('audio_files').get_public_url(file_name)
            
            # 4. Insert the record into the Database
            supabase.table('history').insert({
                "text": text,
                "language": target_lang,
                "audio_url": public_url
            }).execute()

    except Exception as e:
        import traceback
        traceback.print_exc()
        flash(f"Synthesis failed: {e}", "error")
        if music_path and os.path.exists(music_path): os.remove(music_path)
        return redirect(url_for("index"))

    finally:
        if music_path and os.path.exists(music_path):
            os.remove(music_path)

    return send_file(out_path, as_attachment=True, download_name=f"speech_{target_lang}.mp3")

if __name__ == "__main__":
    app.run(debug=True)