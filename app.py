import streamlit as st
import pdfplumber
import re
import tempfile
from gtts import gTTS
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Medical Report Explainer", layout="centered")
st.title("🩺 Medical Report Explainer")
st.write("Voice + Text | Multilingual | PDF Medical Reports")

# ---------------- GLOBAL STORAGE ----------------
if "conversation_log" not in st.session_state:
    st.session_state.conversation_log = []

# ---------------- LANGUAGE SELECTION ----------------
language_map = {
    "English": "en",
    "Hindi": "hi",
    "Tamil": "ta"
}

st.subheader("🌐 Select Language")
language = st.selectbox("Language", list(language_map.keys()))
lang_code = language_map[language]

# ---------------- MEDICAL RANGES ----------------
MEDICAL_RANGES = {
    "Fasting Sugar": (70, 100),
    "Total Cholesterol": (0, 200),
}

# ---------------- PDF UPLOAD ----------------
st.subheader("📄 Upload Medical Report (PDF)")
pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

def extract_text_from_pdf(pdf):
    text = ""
    with pdfplumber.open(pdf) as pdf_doc:
        for page in pdf_doc.pages:
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

# ---------------- TEXT CHAT ----------------
st.subheader("💬 Text Chat (Optional)")
user_text = st.text_input("Type your question here")

# ---------------- REAL-TIME VOICE INPUT ----------------
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.audio_frames = []

    def recv(self, frame: av.AudioFrame):
        self.audio_frames.append(frame)
        return frame

st.subheader("🎤 Real-Time Voice Input")
webrtc_ctx = webrtc_streamer(
    key="voice",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

recognized_text = ""

if webrtc_ctx and webrtc_ctx.state.playing:
    st.info("🎙 Speak now...")

# ---------------- MAIN LOGIC ----------------
if pdf_file:
    report_text = extract_text_from_pdf(pdf_file)
    medical_values = extract_medical_values(report_text)
    explanation = analyze(medical_values)

    st.subheader("📊 Extracted Medical Values")
    st.json(medical_values)

    # Decide input source
    final_query = ""

    if user_text:
        final_query = user_text
        st.session_state.conversation_log.append(f"User (Text): {user_text}")

    elif recognized_text:
        final_query = recognized_text
        st.session_state.conversation_log.append(f"User (Voice): {recognized_text}")

    if explanation:
        st.subheader("🧠 Medical Explanation")
        st.write(explanation)

        st.session_state.conversation_log.append(f"System: {explanation}")

        audio_path = speak(explanation, lang_code)
        st.audio(audio_path)

# ---------------- DOWNLOAD TRANSCRIPT ----------------
st.markdown("---")
st.subheader("📥 Download Conversation Transcript")

if st.session_state.conversation_log:
    transcript = "\n".join(st.session_state.conversation_log)
    st.download_button(
        label="⬇️ Download Transcript (.txt)",
        data=transcript,
        file_name="medical_conversation_transcript.txt",
        mime="text/plain"
    )

st.caption("⚠️ Educational use only. Not a medical diagnosis.")
