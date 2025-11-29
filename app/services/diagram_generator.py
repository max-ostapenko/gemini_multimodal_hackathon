"""Mermaid diagram generation service."""

from app.models.schemas import MermaidDiagram
from app.services.gemini import GeminiService
from app.services.mermaid_renderer import MermaidRenderer

MAX_RETRIES = 3

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
        self.renderer = MermaidRenderer()

    async def generate(
        self,
        prompt: str,
        image_base64: str | None = None,
    ) -> MermaidDiagram:
        """
        Generate a Mermaid diagram from notes/diagram with retry logic.

        If the generated diagram has syntax errors, the LLM will be asked
        to fix it up to MAX_RETRIES times.

        Args:
            prompt: User's description/context about the notes
            image_base64: Base64 encoded image of the notes/diagram

        Returns:
            Structured MermaidDiagram object
        """
        full_prompt = DIAGRAM_PROMPT_TEMPLATE.format(user_prompt=prompt)
        last_error = None
        last_diagram = None

        for attempt in range(MAX_RETRIES + 1):
            # On retry, add error context to the prompt
            if attempt > 0 and last_error and last_diagram:
                retry_prompt = self._build_retry_prompt(
                    original_prompt=full_prompt,
                    failed_code=last_diagram.mermaid_code,
                    error_message=last_error,
                    attempt=attempt,
                )
                current_prompt = retry_prompt
            else:
                current_prompt = full_prompt

            # Generate diagram
            diagram = await self.gemini.generate_structured_output(
                prompt=current_prompt,
                response_schema=MermaidDiagram,
                image_base64=image_base64,
                system_instruction=DIAGRAM_SYSTEM_INSTRUCTION,
            )

            # Validate the generated mermaid code
            is_valid, error_msg = self.renderer.validate_syntax(diagram.mermaid_code)

            if is_valid:
                if attempt > 0:
                    print(f"Mermaid diagram fixed after {attempt} retry(ies)")
                return diagram

            # Store for retry
            last_error = error_msg
            last_diagram = diagram
            print(f"Mermaid syntax error (attempt {attempt + 1}/{MAX_RETRIES + 1}): {error_msg}")

        # After all retries, return the last diagram anyway
        print(f"Warning: Returning diagram with potential syntax errors after {MAX_RETRIES} retries")
        return last_diagram or diagram

    def _build_retry_prompt(
        self,
        original_prompt: str,
        failed_code: str,
        error_message: str,
        attempt: int,
    ) -> str:
        """Build a prompt for retrying diagram generation with error context."""
        return f"""{original_prompt}

---
IMPORTANT: Your previous attempt (attempt {attempt}) produced invalid Mermaid syntax.

The code you generated:
```mermaid
{failed_code}
```

Error message:
{error_message}

Please fix the syntax error and generate a VALID Mermaid diagram. Common issues to check:
- Ensure proper diagram type declaration (e.g., 'flowchart TD', 'sequenceDiagram')
- Check for balanced brackets and quotes
- Avoid special characters in node labels (use quotes if needed)
- Make sure arrow syntax is correct (-->, --->, -.->, etc.)
- For flowcharts, ensure node IDs don't contain spaces

Generate a corrected, syntactically valid Mermaid diagram.
"""
