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
st.write("Robust Patient Details | Natural Language | Real-Time Multilingual Voice")

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
# CLINICAL NORMAL RANGES (CORE SET)
# =================================================
NORMAL_RANGES = {
    # CBC
    "Hemoglobin": {"male": (13.5, 17.5), "female": (12.0, 15.5), "unit": "g/dL"},
    "Total WBC Count": {"range": (4000, 11000), "unit": "cells/µL"},
    "Platelet Count": {"range": (150000, 450000), "unit": "/µL"},

    # Diabetes
    "Fasting Blood Sugar": {"range": (70, 99), "unit": "mg/dL"},
    "HbA1c": {"range": (0, 5.7), "unit": "%"},

    # Lipid
    "Total Cholesterol": {"range": (0, 200), "unit": "mg/dL"},
    "LDL": {"range": (0, 100), "unit": "mg/dL"},
    "HDL": {"male": (40, 1000), "female": (50, 1000), "unit": "mg/dL"},
    "Triglycerides": {"range": (0, 150), "unit": "mg/dL"},

    # Liver
    "SGPT": {"range": (7, 56), "unit": "U/L"},
    "SGOT": {"range": (10, 40), "unit": "U/L"},

    # Kidney
    "Serum Creatinine": {"male": (0.7, 1.3), "female": (0.6, 1.1), "unit": "mg/dL"},

    # Vitamins
    "Vitamin D": {"range": (30, 100), "unit": "ng/mL"},
}

# =================================================
# QUERY → PARAMETER MAP (FOR FILTERING)
# =================================================
QUERY_TO_PARAMS = {
    "sugar": ["Fasting Blood Sugar", "HbA1c"],
    "diabetes": ["Fasting Blood Sugar", "HbA1c"],
    "cholesterol": ["Total Cholesterol", "LDL", "HDL", "Triglycerides"],
    "vitamin": ["Vitamin D"],
    "cbc": ["Hemoglobin", "Total WBC Count", "Platelet Count"],
    "kidney": ["Serum Creatinine"],
    "liver": ["SGPT", "SGOT"],
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
# ROBUST PATIENT DETAILS EXTRACTION (HEURISTIC)
# =================================================
def extract_patient_details(text):
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    joined = " ".join(lines)

    details = {"Name": "Not Found", "Age": "Not Found", "Gender": "Not Found"}

    # -----------------------------
    # AGE detection
    # -----------------------------
    age_match = re.search(r'(\d{1,3})\s*(Y|Years|Yr|yrs)', joined, re.I)
    if age_match:
        details["Age"] = age_match.group(1)

    # -----------------------------
    # GENDER detection
    # -----------------------------
    if re.search(r'\bMale\b|\bM\b', joined, re.I):
        details["Gender"] = "Male"
    elif re.search(r'\bFemale\b|\bF\b', joined, re.I):
        details["Gender"] = "Female"

    # -----------------------------
    # NAME detection (ROBUST + TITLE HANDLING)
    # -----------------------------
    title_pattern = r'(Mr|Mr\.|Ms|Ms\.|Mrs|Mrs\.|Miss|Dr|Dr\.)\s*'

   for line in lines[:10]:
        name_match = re.search(r'Name\s*[:\-]\s*([A-Za-z\s]+)', line)
        if name_match:
            details["Name"] = name_match.group(1).strip()
            return details  # strongest signal → stop here
    # 2️⃣ Standalone name lines (with or without title)
    for line in lines[:8]:
        clean_line = re.sub(title_pattern, '', line, flags=re.I)

        if (
            2 <= len(clean_line.split()) <= 4
            and re.match(r'^[A-Za-z][A-Za-z\s]+$', clean_line)
            and not re.search(
                r'PATIENT|REPORT|LAB|HOSPITAL|PATHOLOGY|INFORMATION|REF|DATE',
                clean_line,
                re.I
            )
        ):
            details["Name"] = clean_line.strip().title()
            return details

    return details

    return details

# =================================================
# PARAMETER EXTRACTION (SAFE)
# =================================================
def extract_present_parameters(text):
    found = {}
    for param in NORMAL_RANGES:
        match = re.search(rf"{param}.*?([0-9]+(?:\.[0-9]+)?)", text, re.I)
        if match:
            try:
                found[param] = float(match.group(1))
            except ValueError:
                continue
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
# TEXT TO SPEECH (WITH TRANSLATION)
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
st.subheader("📄 Upload Medical Report")
pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

if pdf_file:
    report_text = extract_text(pdf_file)
    patient = extract_patient_details(report_text)

    gender = patient["Gender"].lower() if patient["Gender"] != "Not Found" else "male"

    st.subheader("👤 Patient Information")
    st.table(patient)
    st.caption("ℹ️ Patient details are auto-detected and may vary with report format.")

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




