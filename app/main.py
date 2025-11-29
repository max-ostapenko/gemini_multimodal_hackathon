"""Main FastAPI application entry point."""

import base64
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.models.schemas import (
    GenerationRequest,
    GenerationResponse,
    MermaidDiagram,
    TechnicalGuide,
)
from app.services.diagram_generator import DiagramGenerator
from app.services.gemini import GeminiService
from app.services.guide_generator import GuideGenerator
from app.services.mermaid_renderer import MermaidRenderer
from app.services.onepager_generator import OnePagerGenerator

# Global service instances
gemini_service: Optional[GeminiService] = None
guide_generator: Optional[GuideGenerator] = None
diagram_generator: Optional[DiagramGenerator] = None
onepager_generator: Optional[OnePagerGenerator] = None
mermaid_renderer: Optional[MermaidRenderer] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    global gemini_service, guide_generator, diagram_generator, onepager_generator, mermaid_renderer

    # Initialize services
    gemini_service = GeminiService()
    guide_generator = GuideGenerator(gemini_service)
    diagram_generator = DiagramGenerator(gemini_service)
    onepager_generator = OnePagerGenerator(gemini_service)
    mermaid_renderer = MermaidRenderer()

    yield

    # Cleanup (if needed)


app = FastAPI(
    title="DevOpsy - Your Virtual DevOps Engineer",
    description="Transform napkin sketches and whiteboard diagrams into professional technical documentation for engineers!",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "technical-notes-to-onepager"}


@app.get("/")
async def root():
    """Serve the web UI."""
    static_dir = Path(__file__).parent / "static"
    index_file = static_dir / "index.html"
    return HTMLResponse(content=index_file.read_text(encoding="utf-8"))


@app.post("/generate", response_model=GenerationResponse)
async def generate_onepager(
    prompt: str = Form(..., description="Text description/context about the notes"),
    image: Optional[UploadFile] = File(None, description="Image file of notes/diagram"),
):
    """
    Generate a technical one-pager from image + text input.

    This endpoint:
    1. Takes an image of technical notes/diagrams and a text prompt
    2. Generates a detailed technical guide (multimodal → structured JSON)
    3. Generates a Mermaid diagram (multimodal → structured JSON)
    4. Creates a beautiful HTML one-pager combining both

    Returns the complete generation result including the HTML output.
    """
    try:
        # Process image if provided
        image_base64 = None
        if image:
            image_content = await image.read()
            image_base64 = base64.b64encode(image_content).decode("utf-8")

            # Add data URL prefix based on content type
            content_type = image.content_type or "image/jpeg"
            image_base64 = f"data:{content_type};base64,{image_base64}"

        # Step 1: Generate technical guide
        guide = await guide_generator.generate(
            prompt=prompt,
            image_base64=image_base64,
        )

        # Step 2: Generate Mermaid diagram (separate LLM call)
        diagram = await diagram_generator.generate(
            prompt=prompt,
            image_base64=image_base64,
        )

        # Step 3: Render Mermaid to SVG (optional)
        diagram_svg = mermaid_renderer.render_to_svg(diagram.mermaid_code)

        # Step 4: Generate HTML one-pager
        try:
            html_output = await onepager_generator.generate(
                guide=guide,
                diagram=diagram,
                diagram_svg=diagram_svg,
            )
        except Exception as e:
            # Fallback to template-based generation
            print(f"LLM HTML generation failed, using fallback: {e}")
            html_output = onepager_generator.generate_fallback_html(guide, diagram)

        return GenerationResponse(
            technical_guide=guide,
            mermaid_diagram=diagram,
            html_output=html_output,
            diagram_svg=diagram_svg,
            success=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )


@app.post("/generate/json", response_model=GenerationResponse)
async def generate_onepager_json(request: GenerationRequest):
    """
    Generate a technical one-pager from JSON request body.

    Alternative endpoint that accepts JSON body with base64 encoded image.
    """
    try:
        # Step 1: Generate technical guide
        guide = await guide_generator.generate(
            prompt=request.prompt,
            image_base64=request.image_base64,
        )

        # Step 2: Generate Mermaid diagram
        diagram = await diagram_generator.generate(
            prompt=request.prompt,
            image_base64=request.image_base64,
        )

        # Step 3: Render Mermaid to SVG
        diagram_svg = mermaid_renderer.render_to_svg(diagram.mermaid_code)

        # Step 4: Generate HTML one-pager
        try:
            html_output = await onepager_generator.generate(
                guide=guide,
                diagram=diagram,
                diagram_svg=diagram_svg,
            )
        except Exception:
            html_output = onepager_generator.generate_fallback_html(guide, diagram)

        return GenerationResponse(
            technical_guide=guide,
            mermaid_diagram=diagram,
            html_output=html_output,
            diagram_svg=diagram_svg,
            success=True,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )


@app.post("/generate/guide")
async def generate_guide_only(
    prompt: str = Form(...),
    image: Optional[UploadFile] = File(None),
) -> TechnicalGuide:
    """Generate only the technical guide (without diagram or HTML)."""
    image_base64 = None
    if image:
        image_content = await image.read()
        content_type = image.content_type or "image/jpeg"
        image_base64 = f"data:{content_type};base64,{base64.b64encode(image_content).decode('utf-8')}"

    return await guide_generator.generate(prompt=prompt, image_base64=image_base64)


@app.post("/generate/diagram")
async def generate_diagram_only(
    prompt: str = Form(...),
    image: Optional[UploadFile] = File(None),
) -> MermaidDiagram:
    """Generate only the Mermaid diagram (without guide or HTML)."""
    image_base64 = None
    if image:
        image_content = await image.read()
        content_type = image.content_type or "image/jpeg"
        image_base64 = f"data:{content_type};base64,{base64.b64encode(image_content).decode('utf-8')}"

    return await diagram_generator.generate(prompt=prompt, image_base64=image_base64)


@app.get("/preview/{html_content:path}", response_class=HTMLResponse)
async def preview_html(html_content: str):
    """Preview generated HTML (for development/testing)."""
    # This is a simple endpoint to preview HTML
    # In production, you'd serve from Firebase Storage
    return HTMLResponse(content=html_content)


@app.post("/export/docx")
async def export_to_docx(data: dict):
    """
    Export the generated content to a DOCX file.
    
    Generates the DOCX on-demand and returns it as a direct download.
    Works just like the HTML download - saves to user's Downloads folder.
    """
    try:
        # Lazy import to avoid startup issues
        from app.services.docx_exporter import generate_docx
        
        guide = data.get('guide', {})
        diagram = data.get('diagram', {})
        
        # Generate DOCX bytes
        docx_bytes = generate_docx(guide, diagram)
        
        # Return as downloadable file
        filename = f"DevOpsy-{guide.get('title', 'Documentation')[:30]}.docx"
        # Clean filename
        filename = "".join(c if c.isalnum() or c in " -_." else "" for c in filename)
        
        return Response(
            content=docx_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail="DOCX export not available. Please install python-docx: pip install python-docx"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"DOCX export failed: {str(e)}"
        )


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
