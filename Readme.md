# 🧠 AskScribe — AI-Powered Document Intelligence System

**AskScribe** is an intelligent document analysis tool built with **Flask**, combining **Google Gemini AI** and **FAISS vector search** to help users ask questions about uploaded documents in natural language. Whether you're scanning PDFs, DOCX, or TXT files — AskScribe extracts, indexes, and intelligently answers with structured, professional responses.

<p align="center">
  <img src="https://img.shields.io/badge/Backend-Flask-blue?logo=flask" alt="Flask" /><img src="https://img.shields.io/badge/AI-Google%20Gemini-FF6B00?logo=google" alt="Gemini" /><img src="https://img.shields.io/badge/Vector%20Search-FAISS-9cf" alt="FAISS" /><img src="https://img.shields.io/badge/OCR-Tesseract-orange?logo=tesseract" alt="Tesseract" /><img src="https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite" alt="SQLite" /><img src="https://img.shields.io/badge/UI-Bootstrap-darkblue?logo=bootstrap" alt="Bootstrap" />
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT License" /><img src="https://img.shields.io/badge/Python-3.11+-green?logo=python" alt="Python" />
</p>

---

## 🚀 Features

- 📂 Upload PDFs, DOCX, and TXT files  
- 🧠 Ask questions and get structured, **context-aware** answers  
- 🧾 Supports **multi-session** chat history  
- 🔍 Custom **TF-IDF + FAISS** vector search engine  
- 🖼️ **OCR support** for scanned documents  
- 💬 Gemini-powered LLM responses with Markdown formatting  
- 🔐 Secure **user authentication and session handling**  
- 📁 Embedded file management, chunking, and vector indexing

---

## 📁 Project Structure

```
DocumentIntelligence/
│
├── templates/              # HTML (Jinja2)
├── static/                 # CSS/JS/Assets
├── uploads/                # Uploaded documents
├── vectors/                # Stored vector index (JSON)
│
├── main.py                 # Entry point
├── routes.py               # App routes
├── gemini_client.py        # Gemini integration
├── rag_engine.py           # Vector search & RAG engine
├── models.py               # SQLAlchemy models
├── utils/                  # OCR, chunking, preprocessing
├── requirements.txt        # Dependencies
└── README.md
```

---

## ⚙️ Getting Started

### 1️⃣ Clone & Setup

```bash
git clone https://github.com/yourusername/askscribe.git
cd askscribe
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2️⃣ Environment Variables

Create a `.env` file and add:

```env
GEMINI_API_KEY=your_google_gemini_key
SESSION_SECRET=your_flask_secret
```

### 3️⃣ Run the App

```bash
python main.py
```

Visit `http://localhost:5000` in your browser.

---

## 🧠 How It Works

1. **Document Upload**  
   Users upload files → Extract content → Chunk → Generate TF-IDF embeddings → Store with FAISS

2. **Question Answering**  
   User asks question → Retrieve top relevant chunks → Construct prompt → Gemini generates answer

3. **Chat Interface**  
   Real-time Q&A → History stored per session → View or continue previous chats

---

## 🛠️ Tech Stack

| Layer       | Tools / Libraries                    |
|-------------|--------------------------------------|
| 🧠 AI Model  | Google Gemini 2.5 Flash              |
| 🔍 Search    | FAISS + TF-IDF (custom implementation) |
| 🧾 OCR       | Tesseract + Pillow                   |
| 🧰 Backend   | Flask, SQLAlchemy, SQLite            |
| 🎨 Frontend  | HTML, Bootstrap 5.3, JS              |
| 🔐 Auth      | Flask-Login                          |

---

## 🧪 Sample Gemini Prompt

```markdown
**Question**: What is the policy on leave?
**Context**: [Relevant chunks retrieved]
**Instructions**: Answer with headings, bullet points, and highlight **key terms**.
```

---

## 🔐 Security Features

- ✅ Secure file storage with size/type checks  
- ✅ CSRF protection & secure sessions  
- ✅ Environment-based secrets (no hardcoding)  
- ✅ Auto OCR fallback for scanned documents  

---

## 🔮 Future Upgrades

### 📤 Chat Export
Export session as PDF, Markdown, or TXT for offline sharing.

### ☁️ Cloud Uploads
Switch to Amazon S3 or Google Cloud Storage for large files.

### 📈 Analytics Dashboard
Track document types, most asked queries, usage trends.

### 🔔 Real-Time Notifications
Get alerts for OCR status, Gemini API limits, and timeouts.

---

## 📄 License

This project is licensed under the **MIT License**. See the [LICENSE](./LICENSE) file for more info.

---

## 👨‍💻 Author

Made with ❤️ by **Md Meraj Alam**  
_Your feedback is always welcome!_
