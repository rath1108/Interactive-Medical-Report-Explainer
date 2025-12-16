import streamlit as st
import pdfplumber
import re
from gtts import gTTS
import tempfile
import os
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import speech_recognition as sr
import av

st.set_page_config(page_title="Medical Report Explainer", layout="centered")
st.title("🩺 Medical Report Explainer (Real-Time Voice)")

# ---------------- Medical Ranges ----------------
MEDICAL_RANGES = {
    "Fasting Sugar": (70, 100),
    "Total Cholesterol": (0, 200),
}

# ---------------- Language Selection ----------------
language_map = {
    "English": "en",
    "Hindi": "hi",
    "Tamil": "ta"
}

language = st.selectbox("🌐 Select Language", list(language_map.keys()))
lang_code = language_map[language]

# ---------------- Upload PDF ----------------
pdf_file = st.file_uploader("📄 Upload Medical Report (PDF)", type=["pdf"])

def extract_text_from_pdf(pdf):
    text = ""
    with pdfplumber.open(pdf) as pdf:
        for page in pdf.pages:
            text += page.extract_text()
    return text

def extract_medical_values(text):
    patterns = {
        "Fasting Sugar": r'Fasting.*?(\d+)',
        "Total Cholesterol": r'Cholesterol.*?(\d+)'
    }
    data = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        data[key] = match.group(1) if match else "Not found"
    return data

def analyze(values):
    results = []
    for test, value in values.items():
        if value == "Not found":
            continue
        value = int(value)
        low, high = MEDICAL_RANGES[test]
        if value < low:
            results.append(f"{test} is LOW")
        elif value > high:
            results.append(f"{test} is HIGH")
        else:
            results.append(f"{test} is NORMAL")
    return ". ".join(results)

def speak(text, lang):
    tts = gTTS(text=text, lang=lang)
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    return temp.name

# ---------------- Real-Time Voice Processor ----------------
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.audio_data = []

    def recv(self, frame: av.AudioFrame):
        audio = frame.to_ndarray()
        self.audio_data.extend(audio.flatten())
        return frame

st.subheader("🎤 Speak your question (Real-Time)")

webrtc_ctx = webrtc_streamer(
    key="voice",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

# ---------------- Main Logic ----------------
if pdf_file:
    report_text = extract_text_from_pdf(pdf_file)
    medical_values = extract_medical_values(report_text)
    explanation = analyze(medical_values)

    st.subheader("📊 Extracted Values")
    st.json(medical_values)

    if explanation:
        st.subheader("🧠 Explanation")
        st.write(explanation)

        audio_path = speak(explanation, lang_code)
        st.audio(audio_path)

st.markdown("---")
st.caption("⚠️ Educational purpose only")
