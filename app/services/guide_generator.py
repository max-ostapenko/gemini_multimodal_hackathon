"""Technical guide generation service."""

from app.models.schemas import TechnicalGuide
from app.services.gemini import GeminiService

GUIDE_SYSTEM_INSTRUCTION = """You are an expert technical writer and architect.
Your task is to analyze technical notes, diagrams, and sketches (often from napkins or whiteboards)
and transform them into comprehensive, well-structured technical guides.

Guidelines:
- Be thorough but concise
- Use clear, professional language
- Extract all relevant technical concepts from the image
- Organize information logically
- Identify technologies, patterns, and best practices
- Make the content accessible to the target audience
- Include practical next steps
- Format content sections using markdown for rich formatting
"""

GUIDE_PROMPT_TEMPLATE = """Analyze the provided technical notes/diagram and create a comprehensive technical guide.

Additional context from the user: {user_prompt}

Create a detailed technical guide that:
1. Clearly identifies the main topic/system being described
2. Extracts and explains all key concepts
3. Organizes the information into logical sections
4. Identifies technologies and tools mentioned or implied
5. Suggests practical use cases
6. Provides actionable next steps

Focus on making this guide useful for someone who wants to understand and implement the concepts shown."""


class GuideGenerator:
    """Service for generating technical guides from multimodal input."""

    def __init__(self, gemini_service: GeminiService | None = None):
        """Initialize the guide generator."""
        self.gemini = gemini_service or GeminiService()

    async def generate(
        self,
        prompt: str,
        image_base64: str | None = None,
    ) -> TechnicalGuide:
        """
        Generate a technical guide from notes/diagram.

        Args:
            prompt: User's description/context about the notes
            image_base64: Base64 encoded image of the notes/diagram

        Returns:
            Structured TechnicalGuide object
        """
        full_prompt = GUIDE_PROMPT_TEMPLATE.format(user_prompt=prompt)

        guide = await self.gemini.generate_structured_output(
            prompt=full_prompt,
            response_schema=TechnicalGuide,
            image_base64=image_base64,
            system_instruction=GUIDE_SYSTEM_INSTRUCTION,
        )

        return guide
