# 🩺 Medical Report Explainer with Real-Time Voice & Multilingual Support

## 📌 Project Overview
This project is a **Streamlit-based web application** that allows users to upload medical reports
(such as blood test reports) and interact with them using **real-time voice input** and **text chat**.  
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
- 💬 Optional text-based chat interface  
- 🔊 Voice-based medical explanations in multiple languages  
- 🌐 Multilingual support: English, Hindi, Tamil, Telugu  
- 📥 Automatic conversation transcription  
- ⬇ Downloadable transcript file  
- 🖥️ Web-based interface using Streamlit  

---

## 🧱 System Architecture
1. User uploads a medical report (PDF)  
2. Text is extracted using **pdfplumber**  
3. Medical values are identified using **regular expressions**  
4. Values are compared with standard medical ranges  
5. User asks questions via **real-time voice input** or text  
6. Explanation is translated using **googletrans** to selected language  
7. Explanation is converted to **speech** using **gTTS**  
8. Audio response is played in the browser  
9. Entire conversation is stored and available for **download as transcript**

---

## 🛠️ Technologies Used
- Python  
- Streamlit  
- streamlit-webrtc  
- pdfplumber  
- SpeechRecognition  
- Google Text-to-Speech (gTTS)  
- googletrans  
- WebRTC  
- Regular Expressions (basic NLP)  

---

## 🚀 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/rath1108s/medical-report-explainer.git
cd medical-report-explainer

**Create Conda Environment**
conda create -n medical python=3.9
conda activate medical

**Install Dependencies**
pip install -r requirements.txt


**Run the Application**
streamlit run app.py

