# DevOpsy - Your Virtual DevOps Engineer! 🚀
> Submission for Multimodal Agent Hack Berlin 2025
> **Transform your napkin sketches and whiteboard diagrams into professional technical documentation for engineers!**

[![Hackathon](https://img.shields.io/badge/Multimodal%20Agent%20Hack-Berlin%202025-blue)](https://github.com)
[![Gemini](https://img.shields.io/badge/Powered%20by-Google%20Gemini%202.0-orange)](https://ai.google.dev)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 💡 The Pitch

<table>
<tr>
<td width="60%">

**Ever scribbled a brilliant idea on a napkin during lunch?** We've all been there. That sketch contains a million-dollar idea, but turning it into proper documentation? That's where dreams go to die.

**DevOpsy changes everything.** Snap a photo of your napkin, whiteboard, or back-of-envelope sketch. Our AI doesn't just transcribe—it *thinks like a senior architect*. It adds the load balancers you forgot, suggests the caching layer you need, identifies security gaps, and generates production-ready Mermaid diagrams with proper data flows.

**From napkin to "deployment-docs" in 30 seconds!!!** That's DevOpsy.

</td>
<td width="40%">

<img src="assets/devopsy-meme.png" alt="Will develop system architecture for food" width="300"/>

*Don't be this guy. Use DevOpsy.* 😅

</td>
</tr>
</table>

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🖼️ **Multimodal Input** | Upload napkin sketches, whiteboard photos, or hand-drawn diagrams |
| 🧠 **AI Architect** | Doesn't just copy—enhances your design with production best practices |
| 📊 **Smart Diagrams** | Auto-generates Mermaid flowcharts with proper syntax and data flows |
| 📄 **One-Pager Export** | Beautiful HTML documentation ready to share with your team |
| 🔄 **Self-Healing Diagrams** | Agentic validation fixes syntax errors automatically |

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Your Napkin   │────▶│  Gemini 2.0 AI   │────▶│  Professional   │
│    Sketch 📝    │     │  (Multimodal)    │     │  Documentation  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
              ┌─────▼─────┐        ┌──────▼──────┐
              │ Technical │        │   Mermaid   │
              │   Guide   │        │   Diagram   │
              └───────────┘        └─────────────┘
```

**Tech Stack:**
- **Backend**: FastAPI + Python 3.11+
- **AI Engine**: Google Gemini 2.0 Flash (Multimodal)
- **Diagram Rendering**: Mermaid.js + mermaid-py
- **Agentic Features**: Self-correcting diagram validation with RAG

---

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/max-ostapenko/gemini_multimodal_hackathon.git
cd gemini_multimodal_hackathon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure (add your GOOGLE_API_KEY)
cp .env.example .env

# Run!
python -m app.main
```

Open **http://127.0.0.1:8000** and start transforming sketches!

---

## 🔌 API Reference

### `POST /generate`
Transform image + context into full documentation.

**Request:**
```bash
curl -X POST http://127.0.0.1:8000/generate \
  -F "image=@napkin_sketch.jpg" \
  -F "prompt=This is our new microservices architecture for the food delivery app"
```

**Response:**
```json
{
  "technical_guide": { "title": "...", "sections": [...] },
  "mermaid_diagram": { "mermaid_code": "flowchart TD..." },
  "html_output": "<!DOCTYPE html>...",
  "success": true
}
```

### `GET /health`
Health check endpoint.

---

## 📁 Project Structure

```
app/
├── main.py                    # FastAPI entry point
├── config.py                  # Environment configuration
├── services/
│   ├── gemini.py              # Gemini LLM integration
│   ├── guide_generator.py     # Technical guide AI prompts
│   ├── diagram_generator.py   # Mermaid diagram generation
│   ├── diagram_agent.py       # Agentic validation & fixing
│   ├── mermaid_example.py     # RAG context examples
│   ├── mermaid_renderer.py    # SVG rendering
│   └── onepager_generator.py  # HTML generation
├── models/
│   └── schemas.py             # Pydantic models
└── static/
    └── index.html             # Web UI
```

---

## 🤖 How the AI Works

1. **Vision + Understanding**: Gemini 2.0 analyzes your sketch multimodally
2. **Architect Mode**: AI enhances design with missing components (caches, queues, monitoring)
3. **Diagram Generation**: Creates Mermaid flowchart with proper syntax
4. **Agentic Validation**: Self-correcting agent fixes any syntax errors
5. **Documentation**: Generates comprehensive technical guide + HTML one-pager

---

## 👥 Team

Built with ❤️ at **Multimodal Agent Hack Berlin 2025**

---

## 📜 License

MIT License - Build something amazing!
