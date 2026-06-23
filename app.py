from flask import Flask, render_template, request, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import tempfile
from tts.synth import SynthesisManager
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret")  # only for demo

ALLOWED_MUSIC_EXT = {"mp3", "wav", "ogg", "m4a"}

tts_manager = SynthesisManager()  # lazy loads models as needed

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

    if not text:
        flash("Please provide text to synthesize.", "error")
        return redirect(url_for("index"))

    music_path = None
    music_file = request.files.get("music")
    if music_file and music_file.filename:
        if not allowed_file(music_file.filename):
            flash("Unsupported music file type.", "error")
            return redirect(url_for("index"))
        tmp_music = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(secure_filename(music_file.filename))[1])
        music_file.save(tmp_music.name)
        music_path = tmp_music.name

    try:
        out_path = tts_manager.synthesize_to_mp3(
            text=text,
            engine=engine,
            rate=rate,
            music_path=music_path
        )
    except Exception as e:
        # In production, log exception with stack trace
        flash(f"Synthesis failed: {e}", "error")
        # cleanup uploaded music
        if music_path and os.path.exists(music_path):
            os.remove(music_path)
        return redirect(url_for("index"))

    # cleanup uploaded music
    if music_path and os.path.exists(music_path):
        os.remove(music_path)

    return send_file(out_path, as_attachment=True, download_name="speech.mp3")

if __name__ == "__main__":
    app.run(debug=True)
