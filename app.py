import streamlit as st
import pdfplumber
import re
import tempfile
from gtts import gTTS
from googletrans import Translator

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Medical Report Explainer", layout="centered")
st.title("🩺 Medical Report Explainer")
st.write("Structured Medical Report | Multilingual Voice Explanation")

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "conversation_log" not in st.session_state:
    st.session_state.conversation_log = []

# -------------------------------------------------
# LANGUAGE SELECTION
# -------------------------------------------------
language_map = {
    "English": "en",
    "Hindi": "hi",
    "Tamil": "ta",
    "Telugu": "te"
}
language = st.selectbox("🌐 Select Language", list(language_map.keys()))
lang_code = language_map[language]
translator = Translator()

# -------------------------------------------------
# PDF UPLOAD
# -------------------------------------------------
st.subheader("📄 Upload Medical Report (PDF)")
pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

def extract_text_from_pdf(pdf):
    text = ""
    with pdfplumber.open(pdf) as pdf_doc:
        for page in pdf_doc.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# -------------------------------------------------
# SECTION DETECTION
# -------------------------------------------------
def detect_report_sections(text):
    sections = {
        "Complete Blood Count": [],
        "Blood Sugar / Diabetes": [],
        "Lipid Profile": [],
        "Thyroid Function": [],
        "Kidney Function": [],
        "Liver Function": [],
        "Vitamins": [],
        "Urine Analysis": [],
        "Infection Screening": [],
        "Others": []
    }

    for line in text.split("\n"):
        l = line.lower()

        if any(k in l for k in ["hemoglobin", "rbc", "wbc", "platelet", "esr"]):
            sections["Complete Blood Count"].append(line)

        elif any(k in l for k in ["fasting", "glucose", "hba1c"]):
            sections["Blood Sugar / Diabetes"].append(line)

        elif any(k in l for k in ["cholesterol", "hdl", "ldl", "triglyceride"]):
            sections["Lipid Profile"].append(line)

        elif any(k in l for k in ["tsh", "t3", "t4"]):
            sections["Thyroid Function"].append(line)

        elif any(k in l for k in ["creatinine", "urea", "bun", "uric"]):
            sections["Kidney Function"].append(line)

        elif any(k in l for k in ["bilirubin", "sgot", "sgpt", "albumin"]):
            sections["Liver Function"].append(line)

        elif any(k in l for k in ["vitamin d", "vitamin b12"]):
            sections["Vitamins"].append(line)

        elif any(k in l for k in ["urine", "microalbumin"]):
            sections["Urine Analysis"].append(line)

        elif any(k in l for k in ["hiv", "hbsag"]):
            sections["Infection Screening"].append(line)

        else:
            sections["Others"].append(line)

    return sections

# -------------------------------------------------
# SECTION EXPLANATION (VOICE-FRIENDLY)
# -------------------------------------------------
def explain_section(section_name, lines):
    if not lines:
        return f"No significant findings in {section_name}."

    explanations = {
        "Complete Blood Count":
            "This section checks your blood levels, including hemoglobin and white blood cells.",
        "Blood Sugar / Diabetes":
            "This section explains your blood sugar levels and diabetes control.",
        "Lipid Profile":
            "This section shows cholesterol and fat levels related to heart health.",
        "Thyroid Function":
            "This section checks whether your thyroid hormones are normal.",
        "Kidney Function":
            "This section evaluates how well your kidneys are working.",
        "Liver Function":
            "This section assesses the health of your liver.",
        "Vitamins":
            "This section checks important vitamins like Vitamin D and Vitamin B12.",
        "Urine Analysis":
            "This section analyzes urine to detect sugar, protein, or infection.",
        "Infection Screening":
            "This section screens for infections such as HIV or Hepatitis."
    }

    return explanations.get(section_name,
                            "This section contains additional medical information.")

# -------------------------------------------------
# TEXT TO SPEECH
# -------------------------------------------------
def speak(text, lang):
    tts = gTTS(text=text, lang=lang)
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    return temp.name

# -------------------------------------------------
# TEXT CHAT (OPTIONAL)
# -------------------------------------------------
st.subheader("💬 Text Chat (Optional)")
user_text = st.text_input("Ask a question about your report")

# -------------------------------------------------
# MAIN LOGIC
# -------------------------------------------------
if pdf_file:
    report_text = extract_text_from_pdf(pdf_file)
    sections = detect_report_sections(report_text)

    st.subheader("📂 Report Sections")
    for sec, lines in sections.items():
        if lines:
            with st.expander(sec):
                for l in lines[:8]:
                    st.write(l)

    # Text-based question handling
    if user_text:
        st.session_state.conversation_log.append(f"User (Text): {user_text}")

    # Button to explain entire report
    st.subheader("🔊 Voice Explanation for All Sections")
    explain_all = st.button("▶️ Explain Entire Report (Voice)")

    if explain_all:
        for section, lines in sections.items():
            if not lines:
                continue

            explanation = explain_section(section, lines)
            translated = translator.translate(explanation, dest=lang_code).text

            st.markdown(f"### 🧩 {section}")
            st.write(translated)

            audio_path = speak(translated, lang_code)
            st.audio(audio_path)

            st.session_state.conversation_log.append(
                f"{section}: {translated}"
            )

# -------------------------------------------------
# DOWNLOAD TRANSCRIPT
# -------------------------------------------------
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
