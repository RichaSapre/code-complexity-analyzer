# 🧠 Code Complexity Analyzer (v1.0)

A premium developer tool for analyzing algorithmic depth and providing AI-driven optimizations.

## 🚀 Deployment Guide

### Local Development
1. **Clone & Setup**:
   ```bash
   pip install -r backend/requirements.txt
   ```
2. **Setup Keys**: Create a `.env` file in the root:
   ```env
   GEMINI_API_KEY=your_key
   GROQ_API_KEY=your_key
   ```
3. **Run**:
   ```bash
   python backend/app.py
   ```

### ☁️ Cloud Deployment (Render / Heroku)
- **Start Command**: `gunicorn --chdir backend app:app` (This is why we added Gunicorn!)
- **Environment Variables**: Add `GEMINI_API_KEY` and `GROQ_API_KEY` in your provider's dashboard.
- **Root Directory**: The structure is already optimized for monorepos.

## 🏗️ Technical Stack
- **Backend**: Flask + Gemini 2.0 / Groq Llama-3.3 Fallback Chain.
- **Frontend**: Vanilla JS + CSS Grain Texture + Syne & JetBrains Mono typography.
- **CI/CD**: GitHub Actions architecture validation.

---
**Author**: Richa Nitin Sapre // 2026
