"""Pydantic models for structured data."""

from typing import Optional

from pydantic import BaseModel, Field


class KeyConcept(BaseModel):
    """A key concept extracted from the notes."""
    name: str = Field(description="Name of the concept")
    description: str = Field(description="Brief description of the concept")
    importance: str = Field(description="Why this concept is important")


class Section(BaseModel):
    """A section of the technical guide."""
    title: str = Field(description="Section title")
    content: str = Field(description="Detailed content for this section in markdown")
    key_points: list[str] = Field(default_factory=list, description="Bullet points of key takeaways")


class TechnicalGuide(BaseModel):
    """Structured technical guide generated from notes."""
    title: str = Field(description="Title of the technical guide")
    subtitle: str = Field(description="Subtitle or tagline")
    executive_summary: str = Field(description="Brief executive summary (2-3 sentences)")
    problem_statement: str = Field(description="What problem does this solve?")
    key_concepts: list[KeyConcept] = Field(default_factory=list, description="Main concepts covered")
    sections: list[Section] = Field(default_factory=list, description="Detailed sections")
    technologies: list[str] = Field(default_factory=list, description="Technologies/tools mentioned")
    use_cases: list[str] = Field(default_factory=list, description="Potential use cases")
    next_steps: list[str] = Field(default_factory=list, description="Recommended next steps")
    target_audience: str = Field(description="Who this guide is for")


class MermaidDiagram(BaseModel):
    """Mermaid diagram representation."""
    diagram_type: str = Field(description="Type of diagram (flowchart, sequence, class, etc.)")
    title: str = Field(description="Title for the diagram")
    description: str = Field(description="What this diagram represents")
    mermaid_code: str = Field(description="The mermaid diagram code")


class GenerationRequest(BaseModel):
    """Request model for generation endpoint."""
    prompt: str = Field(description="Text description/context about the notes")
    image_base64: Optional[str] = Field(default=None, description="Base64 encoded image")


class GenerationResponse(BaseModel):
    """Response model for generation endpoint."""
    technical_guide: TechnicalGuide
    mermaid_diagram: MermaidDiagram
    html_output: str = Field(description="Generated HTML one-pager")
    diagram_svg: Optional[str] = Field(default=None, description="SVG rendering of the mermaid diagram")
    success: bool = True
    error: Optional[str] = None
