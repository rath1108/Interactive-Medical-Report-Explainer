import streamlit as st
import pdfplumber
import re
import tempfile
from gtts import gTTS
from deep_translator import GoogleTranslator

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Medical Report Explainer", layout="centered")
st.title("🩺 Medical Report Explainer")
st.write("Section-wise Condition | Multilingual Voice Explanation")

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

# -------------------------------------------------
# MEDICAL REFERENCE RANGES
# -------------------------------------------------
RANGES = {
    "Fasting Sugar": (70, 100),
    "HbA1c": (0, 5.6),
    "Total Cholesterol": (0, 200),
    "Vitamin D": (30, 100),
    "Vitamin B12": (200, 900)
}

# -------------------------------------------------
# PDF UPLOAD
# -------------------------------------------------
st.subheader("📄 Upload Medical Report (PDF)")
pdf_file = st.file_uploader("Upload PDF", type=["pdf"])

def extract_text_from_pdf(pdf):
    text = ""
    with pdfplumber.open(pdf) as pdf_doc:
        for page in pdf_doc.pages:
            if page.extract_text():
                text += page.extract_text() + "\n"
    return text

# -------------------------------------------------
# SECTION DETECTION
# -------------------------------------------------
def detect_report_sections(text):
    sections = {
        "Complete Blood Count": [],
        "Blood Sugar / Diabetes": [],
        "Lipid Profile": [],
        "Vitamins": [],
        "Thyroid Function": [],
        "Kidney Function": [],
        "Liver Function": [],
        "Urine Analysis": [],
        "Infection Screening": [],
        "Others": []
    }

    for line in text.split("\n"):
        l = line.lower()

        if any(k in l for k in ["hemoglobin", "rbc", "wbc", "platelet"]):
            sections["Complete Blood Count"].append(line)
        elif any(k in l for k in ["fasting", "glucose", "hba1c"]):
            sections["Blood Sugar / Diabetes"].append(line)
        elif any(k in l for k in ["cholesterol", "hdl", "ldl"]):
            sections["Lipid Profile"].append(line)
        elif any(k in l for k in ["vitamin d", "vitamin b12"]):
            sections["Vitamins"].append(line)
        elif any(k in l for k in ["tsh", "t3", "t4"]):
            sections["Thyroid Function"].append(line)
        elif any(k in l for k in ["creatinine", "urea"]):
            sections["Kidney Function"].append(line)
        elif any(k in l for k in ["bilirubin", "sgot", "sgpt"]):
            sections["Liver Function"].append(line)
        elif "urine" in l:
            sections["Urine Analysis"].append(line)
        elif any(k in l for k in ["hiv", "hbsag"]):
            sections["Infection Screening"].append(line)
        else:
            sections["Others"].append(line)

    return sections

# -------------------------------------------------
# VALUE EXTRACTION
# -------------------------------------------------
def extract_values(text):
    values = {}

    patterns = {
        "Fasting Sugar": r'Fasting.*?(\d+)',
        "HbA1c": r'HbA1c.*?([\d.]+)',
        "Total Cholesterol": r'Cholesterol.*?(\d+)',
        "Vitamin D": r'Vitamin D.*?([\d.]+)',
        "Vitamin B12": r'Vitamin B12.*?(\d+)'
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            values[key] = float(match.group(1))

    return values

# -------------------------------------------------
# CONDITION ANALYSIS
# -------------------------------------------------
def get_condition(test, value):
    low, high = RANGES[test]
    if value < low:
        return "LOW"
    elif value > high:
        return "HIGH"
    else:
        return "NORMAL"

def section_condition(section, values):
    conditions = []

    for test in values:
        if section == "Blood Sugar / Diabetes" and test in ["Fasting Sugar", "HbA1c"]:
            conditions.append(f"{test} is {get_condition(test, values[test])}")

        if section == "Lipid Profile" and test == "Total Cholesterol":
            conditions.append(f"{test} is {get_condition(test, values[test])}")

        if section == "Vitamins" and test in ["Vitamin D", "Vitamin B12"]:
            conditions.append(f"{test} is {get_condition(test, values[test])}")

    if not conditions:
        return "Values are mostly within normal range."

    return "; ".join(conditions)

# -------------------------------------------------
# SECTION EXPLANATION + CONDITION
# -------------------------------------------------
def explain_section(section, values):
    base_explanation = {
        "Complete Blood Count": "This section evaluates blood cells and immunity.",
        "Blood Sugar / Diabetes": "This section shows blood sugar control and diabetes status.",
        "Lipid Profile": "This section evaluates cholesterol related to heart health.",
        "Vitamins": "This section checks vitamin deficiency levels.",
        "Thyroid Function": "This section evaluates thyroid hormone balance.",
        "Kidney Function": "This section checks kidney performance.",
        "Liver Function": "This section assesses liver health.",
        "Urine Analysis": "This section analyzes urine parameters.",
        "Infection Screening": "This section screens for infections."
    }

    condition = section_condition(section, values)
    return f"{base_explanation.get(section,'Medical information section')} Condition: {condition}."

# -------------------------------------------------
# TEXT TO SPEECH
# -------------------------------------------------
def speak(text, lang):
    tts = gTTS(text=text, lang=lang)
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    tts.save(temp.name)
    return temp.name

# -------------------------------------------------
# TEXT INPUT
# -------------------------------------------------
st.subheader("💬 Ask a Question")
user_text = st.text_input("Example: Explain my blood sugar condition")

# -------------------------------------------------
# QUERY TO SECTION
# -------------------------------------------------
def map_query_to_section(q):
    q = q.lower()
    if "sugar" in q or "diabetes" in q:
        return "Blood Sugar / Diabetes"
    if "cholesterol" in q:
        return "Lipid Profile"
    if "vitamin" in q:
        return "Vitamins"
    if "thyroid" in q:
        return "Thyroid Function"
    if "kidney" in q:
        return "Kidney Function"
    if "liver" in q:
        return "Liver Function"
    if "urine" in q:
        return "Urine Analysis"
    if "infection" in q:
        return "Infection Screening"
    if "blood" in q or "cbc" in q:
        return "Complete Blood Count"
    return None

# -------------------------------------------------
# MAIN LOGIC
# -------------------------------------------------
if pdf_file:
    report_text = extract_text_from_pdf(pdf_file)
    sections = detect_report_sections(report_text)
    values = extract_values(report_text)

    st.subheader("📂 Detected Sections")
    for s, lines in sections.items():
        if lines:
            with st.expander(s):
                for l in lines[:6]:
                    st.write(l)

    # ---- USER QUERY MODE ----
    if user_text:
        st.session_state.conversation_log.append(f"User: {user_text}")
        section = map_query_to_section(user_text)

        if section:
            explanation = explain_section(section, values)

            translated = GoogleTranslator(
                source="auto",
                target=lang_code
            ).translate(explanation)

            st.subheader(f"🧠 {section}")
            st.write(translated)

            audio = speak(translated, lang_code)
            st.audio(audio)

            st.session_state.conversation_log.append(f"{section}: {translated}")
        else:
            st.warning("Could not understand the question.")

    # ---- FULL REPORT MODE ----
    else:
        st.subheader("🔊 Explain Entire Report")
        if st.button("▶️ Explain All Sections"):
            for section in sections:
                explanation = explain_section(section, values)

                translated = GoogleTranslator(
                    source="auto",
                    target=lang_code
                ).translate(explanation)

                st.markdown(f"### 🧩 {section}")
                st.write(translated)

                audio = speak(translated, lang_code)
                st.audio(audio)

                st.session_state.conversation_log.append(f"{section}: {translated}")

# -------------------------------------------------
# TRANSCRIPT DOWNLOAD
# -------------------------------------------------
st.markdown("---")
st.subheader("📥 Download Transcript")

if st.session_state.conversation_log:
    transcript = "\n".join(st.session_state.conversation_log)
    st.download_button(
        "⬇️ Download Transcript",
        transcript,
        file_name="medical_report_transcript.txt"
    )

st.caption("⚠️ Educational use only. Not medical advice.")
