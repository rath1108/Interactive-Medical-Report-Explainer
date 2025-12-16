# 🩺 Medical Report Explainer with Real-Time Voice Interaction

## 📌 Project Overview
This project is a **Streamlit-based web application** that allows users to upload medical reports
(such as blood test reports) and interact with them using **real-time voice input**.
The system extracts key medical values, detects abnormalities, and explains the results
using **multilingual voice output**.

This application is designed to help patients and caregivers understand medical reports
in a simple and interactive way.

---

## 🎯 Features
- 📄 Upload medical reports in PDF format
- 🔍 Automatic extraction of key medical values
- ⚠️ Detection of abnormal values using standard medical ranges
- 🎤 Real-time microphone input using WebRTC
- 🔊 Voice-based medical explanations
- 🌐 Multilingual support (English, Hindi, Tamil)
- 🖥️ Web-based interface using Streamlit

---

## 🧱 System Architecture
1. User uploads a medical report (PDF)
2. Text is extracted using **pdfplumber**
3. Medical values are identified using **regular expressions**
4. Values are compared with standard medical ranges
5. User asks questions via **real-time voice input**
6. Explanation is generated and converted to speech
7. Audio response is played in the browser

---

## 🛠️ Technologies Used
- Python
- Streamlit
- streamlit-webrtc
- pdfplumber
- SpeechRecognition
- Google Text-to-Speech (gTTS)
- WebRTC
- Regular Expressions (NLP basics)

---

## 🚀 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/medical-report-explainer.git
cd medical-report-explainer
