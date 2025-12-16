import streamlit as st
import pdfplumber
import re
import tempfile
import numpy as np
from gtts import gTTS
from deep_translator import GoogleTranslator
import speech_recognition as sr
from streamlit_webrtc import webrtc_streamer, AudioProcessorBase
import av
import soundfile as sf

# =================================================
# PAGE CONFIG
# =================================================
st.set_page_config(page_title="Medical Report Explainer", layout="centered")
st.title("🩺 Medical Report Explainer")
st.write("Patient Details | Natural Language | Real-Time Multilingual Voice")

# =================================================
# SESSION STATE
# =================================================
if "conversation_log" not in st.session_state:
    st.session_state.conversation_log = []

if "voice_query" not in st.session_state:
    st.session_state.voice_query = ""

# =================================================
# LANGUAGE SELECTION (OUTPUT)
# =================================================
language_map = {
    "English": "en",
    "Hindi": "hi",
    "Tamil": "ta",
    "Telugu": "te"
}
language = st.selectbox("🌐 Select Output Language", list(language_map.keys()))
lang_code = language_map[language]

# =================================================
# CLINICAL NORMAL RANGES (SAFE STRUCTURE)
# =================================================
NORMAL_RANGES = {
    "Hemoglobin": {"male": (13.5, 17.5), "female": (12.0, 15.5), "unit": "g/dL"},
    "Total WBC Count": {"range": (4000, 11000), "unit": "cells/µL"},
    "Platelet Count": {"range": (150000, 450000), "unit": "/µL"},
    "Fasting Blood Sugar": {"range": (70, 99), "unit": "mg/dL"},
    "HbA1c": {"range": (0, 5.7), "unit": "%"},
    "Total Cholesterol": {"range": (0, 200), "unit": "mg/dL"},
    "LDL": {"range": (0, 100), "unit": "mg/dL"},
    "HDL": {"male": (40, 1000), "female": (50, 1000), "unit": "mg/dL"},
    "Triglycerides": {"range": (0, 150), "unit": "mg/dL"},
    "SGPT": {"range": (7, 56), "unit": "U/L"},
    "SGOT": {"range": (10, 40), "unit": "U/L"},
    "Serum Creatinine": {"male": (0.7, 1.3), "female": (0.6, 1.1), "unit": "mg/dL"},
    "Vitamin D": {"range": (30, 100), "unit": "ng/mL"},
}

QUERY_TO_PARAMS = {
    "sugar": ["Fasting Blood Sugar", "HbA1c"],
    "diabetes": ["Fasting Blood Sugar", "HbA1c"],
    "cholesterol": ["Total Cholesterol", "LDL", "HDL", "Triglycerides"],
    "vitamin": ["Vitamin D"],
    "cbc": ["Hemoglobin", "Total WBC Count", "Platelet Count"],
    "kidney": ["Serum Creatinine"],
    "liver": ["SGPT", "SGOT"]
}

# =================================================
# PDF TEXT EXTRACTION
# =================================================
def extract_text(pdf):
    text = ""
    with pdfplumber.open(pdf) as p:
        for page in p.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text

# =================================================
# PATIENT DETAILS EXTRACTION
# =================================================
def extract_patient_details(text):
    details = {"Name": "Not Found", "Age": "Not Found", "Gender": "Male"}

    if m := re.search(r'Patient\s*Name\s*[:\-]\s*(.*)', text, re.I):
        details["Name"] = m.group(1).strip()
    if m := re.search(r'Age\s*[:\-]\s*(\d+)', text, re.I):
        details["Age"] = m.group(1)
    if m := re.search(r'(Male|Female)', text, re.I):
        details["Gender"] = m.group(1)

    return details

# =================================================
# PARAMETER EXTRACTION (SAFE)
# =================================================
def extract_present_parameters(text):
    found = {}
    for param in NORMAL_RANGES:
        match = re.search(rf"{param}.*?([0-9]+(?:\.[0-9]+)?)", text, re.I)
        if match:
            found[param] = float(match.group(1))
    return found

def evaluate(param, value, gender):
    ref = NORMAL_RANGES[param]

    if gender in ref:
        low, high = ref[gender]
    elif "range" in ref:
        low, high = ref["range"]
    else:
        return "UNKNOWN"

    if value < low:
        return "LOW"
    elif value > high:
        return "HIGH"
    else:
        return "NORMAL"

def natural_sentence(param, value, unit, condition):
    if condition == "NORMAL":
        return f"Your {param} is {value} {unit}, which is within the normal range."
    elif condition == "LOW":
        return f"Your {param} is {value} {unit}, which is lower than normal."
    else:
        return f"Your {param} is {value} {unit}, which is higher than normal."

# =================================================
# TEXT TO SPEECH
# =================================================
def speak(text):
    translated = GoogleTranslator(source="auto", target=lang_code).translate(text)
    tts = gTTS(translated, lang=lang_code)
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    return translated, temp.name

# =================================================
# REAL-TIME VOICE INPUT (WEBRTC)
# =================================================
class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.frames = []

    def recv(self, frame: av.AudioFrame):
        audio = frame.to_ndarray().flatten()
        self.frames.extend(audio)
        return frame

st.subheader("🎤 Speak Your Question (Real-Time)")
webrtc_ctx = webrtc_streamer(
    key="mic",
    audio_processor_factory=AudioProcessor,
    media_stream_constraints={"audio": True, "video": False},
)

if webrtc_ctx and webrtc_ctx.audio_processor:
    if st.button("🧠 Process Voice"):
        audio_np = np.array(webrtc_ctx.audio_processor.frames, dtype=np.float32)
        if len(audio_np) > 0:
            sf.write("temp.wav", audio_np, 16000)
            r = sr.Recognizer()
            with sr.AudioFile("temp.wav") as src:
                audio_data = r.record(src)
            try:
                st.session_state.voice_query = r.recognize_google(audio_data)
                st.success(f"🗣 You said: {st.session_state.voice_query}")
            except:
                st.error("Could not recognize voice input")

# =================================================
# TEXT INPUT
# =================================================
st.subheader("💬 Or Type Your Question")
text_query = st.text_input("Example: Is my fasting sugar normal?")

# =================================================
# MAIN LOGIC
# =================================================
pdf_file = st.file_uploader("📄 Upload Medical Report (PDF)", type=["pdf"])

if pdf_file:
    report_text = extract_text(pdf_file)
    patient = extract_patient_details(report_text)
    gender = patient["Gender"].lower()

    st.subheader("👤 Patient Information")
    st.table(patient)

    found = extract_present_parameters(report_text)

    query = (st.session_state.voice_query or text_query).lower()

    st.subheader("🧠 Medical Explanation")

    if query:
        requested = []
        for key, params in QUERY_TO_PARAMS.items():
            if key in query:
                requested.extend(params)

        shown = False
        for param in requested:
            if param in found:
                value = found[param]
                cond = evaluate(param, value, gender)
                unit = NORMAL_RANGES[param]["unit"]
                sentence = natural_sentence(param, value, unit, cond)

                st.write("•", sentence)
                translated, audio = speak(sentence)
                st.audio(audio)

                st.session_state.conversation_log.append(translated)
                shown = True

        if not shown:
            msg = "No data available for the requested test in this report."
            st.info(msg)
            _, audio = speak(msg)
            st.audio(audio)

    else:
        for param, value in found.items():
            cond = evaluate(param, value, gender)
            unit = NORMAL_RANGES[param]["unit"]
            sentence = natural_sentence(param, value, unit, cond)

            st.write("•", sentence)
            translated, audio = speak(sentence)
            st.audio(audio)

            st.session_state.conversation_log.append(translated)

# =================================================
# TRANSCRIPT DOWNLOAD
# =================================================
st.markdown("---")
if st.session_state.conversation_log:
    st.download_button(
        "⬇️ Download Conversation Transcript",
        "\n".join(st.session_state.conversation_log),
        file_name="medical_conversation.txt"
    )

st.caption("⚠️ Educational use only. Not a medical diagnosis.")
