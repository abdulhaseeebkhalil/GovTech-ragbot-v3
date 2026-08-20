# 🏛️ Unified GovTech - AI-Powered Government Services Platform

A comprehensive AI-powered platform combining a beautiful modern chat interface with advanced legal document analysis capabilities using Google Gemini AI.

## 🎯 Features

### ✨ Modern Chat Interface
- Beautiful React UI with Framer Motion animations
- Siri-style Avatar with dynamic animations
- Chat History with session management
- Responsive Design with Tailwind CSS + Shadcn UI

### 🤖 AI-Powered Chat (Google Gemini 2.0)
- General Q&A using Google Gemini
- Conversation Context awareness
- Real-time Responses with typing indicators

### ⚖️ Legal Document Analysis
- Multi-Agent RAG System for legal analysis
- PDF Processing of legal documents
- Vector Search with Qdrant
- Court Document Generation
- Named Entity Recognition (NER)

## 🚀 Quick Start Guide

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+

### Step 1: Verify Configuration
Your .env file has been copied from GovTech with existing credentials.

### Step 2: Setup Backend
```bash
Double-click: setup-backend.bat
```

### Step 3: Setup Frontend
```bash
Double-click: setup-frontend.bat
```

## 🎮 Running the Application

### Terminal 1 - Start Backend
```bash
Double-click: start-backend.bat
```
Backend: http://localhost:8000

### Terminal 2 - Start Frontend
```bash
Double-click: start-frontend.bat
```
Frontend: http://localhost:5173

## 📊 API Endpoints

- `POST /chat` - General chatbot with Gemini
- `POST /legal/qa` - Q&A about KPK Local Government Act
- `POST /legal/analyze` - Multi-agent legal analysis
- `GET /health` - Health check
- `GET /docs` - API documentation

## 🤖 AI Provider

**Google Gemini 2.0 ONLY** - No OpenAI required!

Your existing Gemini API key and Qdrant credentials are already configured.

## 🐛 Quick Troubleshooting

**Backend won't start?**
- Check Python 3.9+: `python --version`
- Run `setup-backend.bat` again
- Verify .env has GEMINI_API_KEY

**Frontend shows error?**
- Ensure backend is running
- Check: http://localhost:8000/health

## 📞 Support

- API Docs: http://localhost:8000/docs
- Read: RUN_COMMANDS.md for detailed help
- Check: START_HERE.txt for quick start

**Happy Coding! 🚀**

