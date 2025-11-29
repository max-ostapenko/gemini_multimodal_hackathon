"""Mermaid diagram generation service."""

from app.models.schemas import MermaidDiagram
from app.services.gemini import GeminiService

DIAGRAM_SYSTEM_INSTRUCTION = """You are an expert at creating clear, informative Mermaid diagrams.
Your task is to analyze technical notes and diagrams and create a Mermaid diagram that represents
the core architecture, flow, or concepts.

Guidelines for Mermaid diagrams:
- Choose the most appropriate diagram type (flowchart, sequence, class, state, etc.)
- Keep diagrams clean and readable
- Use meaningful node names and labels
- Show relationships and data flow clearly
- Include key components and their interactions
- Avoid overly complex diagrams - aim for clarity

Common diagram types to consider:
- flowchart TD/LR: For process flows, architectures, decision trees
- sequenceDiagram: For interaction sequences between components
- classDiagram: For object relationships and class structures
- stateDiagram-v2: For state machines and transitions
- erDiagram: For data models and entity relationships
- graph TD/LR: For simple directed graphs

IMPORTANT: Generate valid Mermaid syntax only. Test your diagram mentally to ensure it will render correctly.
"""

DIAGRAM_PROMPT_TEMPLATE = """Analyze the provided technical notes/diagram and create a Mermaid diagram
that captures the core architecture or key concepts.

Additional context from the user: {user_prompt}

Create a Mermaid diagram that:
1. Represents the main components/entities shown
2. Shows relationships and data flow
3. Is clear and easy to understand
4. Uses appropriate diagram type for the content
5. Includes meaningful labels and descriptions

The diagram should serve as a visual summary of the technical concepts."""


class DiagramGenerator:
    """Service for generating Mermaid diagrams from multimodal input."""

    def __init__(self, gemini_service: GeminiService | None = None):
        """Initialize the diagram generator."""
        self.gemini = gemini_service or GeminiService()

    async def generate(
        self,
        prompt: str,
        image_base64: str | None = None,
    ) -> MermaidDiagram:
        """
        Generate a Mermaid diagram from notes/diagram.

        Args:
            prompt: User's description/context about the notes
            image_base64: Base64 encoded image of the notes/diagram

        Returns:
            Structured MermaidDiagram object
        """
        full_prompt = DIAGRAM_PROMPT_TEMPLATE.format(user_prompt=prompt)

        diagram = await self.gemini.generate_structured_output(
            prompt=full_prompt,
            response_schema=MermaidDiagram,
            image_base64=image_base64,
            system_instruction=DIAGRAM_SYSTEM_INSTRUCTION,
        )

        return diagram
