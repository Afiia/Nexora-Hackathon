import flask
from flask import Flask, render_template, request, jsonify
import whisper
import tempfile
import os
import imageio_ffmpeg
import subprocess

app = Flask(__name__)

# Force local ffmpeg path
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

def run(cmd, *args, **kwargs):
    if cmd and "ffmpeg" in cmd[0]:
        cmd[0] = FFMPEG_PATH
    return subprocess.run(cmd, *args, **kwargs)

import whisper.audio
whisper.audio.run = run

# Load model
model = whisper.load_model("base")


def classify(text):
    text = (text or "").lower()
    if any(x in text for x in ["otp", "cvv", "pin", "share otp"]):
        return "🚨 FRAUD"
    if any(x in text for x in ["bank", "kyc", "urgent", "account blocked"]):
        return "⚠️ SUSPICIOUS"
    return "✅ SAFE"


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/process_audio", methods=["POST"])
def process_audio():
    path = None
    try:
        audio = request.files["audio"]

        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            audio.save(tmp.name)
            path = tmp.name

        result = model.transcribe(path, fp16=False)
        text = result.get("text", "")

        return jsonify({
            "risk": classify(text),
            "text": text
        })

    except Exception as e:
        return jsonify({
            "risk": "⚠️ ERROR",
            "text": str(e)
        }), 500

    finally:
        try:
            if path and os.path.exists(path):
                os.remove(path)
        except Exception:
            pass


if __name__ == "__main__":
    print("Running at http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)
