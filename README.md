# Technical Notes to One-Pager Generator

> Submission for Multimodal Agent Hack Berlin 2025

Transform your napkin sketches and whiteboard diagrams into professional technical documentation with AI.

## Features

- 📝 **Multimodal Input**: Upload images of technical notes/diagrams + add text descriptions
- 📖 **Technical Guide Generation**: AI generates detailed, structured technical guides
- 📊 **Mermaid Diagrams**: Automatically creates architecture/concept diagrams
- 🎨 **One-Pager Output**: Beautiful HTML one-pager combining guide and visuals

## Architecture

- **Backend**: Python with FastAPI (local)
- **AI/LLM**: Google Gemini 2.0 Flash (GCP API)
- **Diagram Rendering**: mermaid-py for SVG generation

## Setup

1. Clone the repository

2. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure environment:

```bash
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY
```

5. Run the application:

```bash
python -m app.main
# or
uvicorn app.main:app --reload --host 127.0.0.1
```

6. Open http://127.0.0.1:8000 in your browser

## API Endpoints

### POST /generate
Generate a technical one-pager from image + text input.

**Request:**
- `image`: Image file (napkin sketch, whiteboard photo)
- `prompt`: Text description/context about the notes

**Response:**
```json
{
  "technical_guide": { ... },
  "mermaid_diagram": "...",
  "html_output": "...",
  "diagram_svg": "..."
}
```

### GET /health
Health check endpoint.

## Project Structure

```text
app/
├── main.py              # FastAPI application entry point
├── config.py            # Configuration management
├── cli.py               # Command-line interface
├── services/
│   ├── gemini.py             # Gemini LLM service
│   ├── guide_generator.py    # Technical guide generation
│   ├── diagram_generator.py  # Mermaid diagram generation
│   ├── onepager_generator.py # HTML one-pager generation
│   └── mermaid_renderer.py   # Mermaid to SVG/CSS
└── models/
    └── schemas.py       # Pydantic models
```

## License

MIT
