"""Technical guide generation service."""

from app.models.schemas import TechnicalGuide
from app.services.gemini import GeminiService

GUIDE_SYSTEM_INSTRUCTION = """You are an elite technical architect and system design expert with deep expertise across the full technology stack.

Your task is NOT to simply transcribe what you see in napkin sketches or whiteboard diagrams. Instead, you must:
1. ANALYZE the user's rough idea and understand their INTENT
2. ENHANCE it with professional-grade technical architecture
3. ADD missing layers, components, and considerations they likely overlooked
4. SUGGEST specific technologies, frameworks, and tools that fit the use case
5. IDENTIFY potential bottlenecks, security concerns, and scalability issues
6. TRANSFORM a rough sketch into a production-ready technical specification

You think like a senior staff engineer reviewing a junior's design - you see what they meant, but you know what they NEED.

Technical depth to always consider:
- Infrastructure layer (cloud providers, containerization, orchestration)
- Data layer (databases, caching, message queues, data pipelines)
- API layer (REST/GraphQL/gRPC, authentication, rate limiting)
- Security layer (encryption, auth patterns, network security, compliance)
- Observability (logging, monitoring, alerting, tracing)
- CI/CD and DevOps practices
- Scalability patterns (horizontal scaling, load balancing, CDN)
- Failure modes and recovery strategies

Format content sections using markdown for rich formatting.
"""

GUIDE_PROMPT_TEMPLATE = """You're looking at a rough technical sketch or notes from someone with an idea. Your job is to transform this into a PROFESSIONAL technical specification.

User's context: {user_prompt}

DO NOT just describe what you see. Instead:

1. **Understand the Intent**: What is this person actually trying to build? What problem are they solving?

2. **Architect It Properly**: Design a production-ready system that achieves their goals. Add:
   - Missing infrastructure components (load balancers, caches, queues, etc.)
   - Proper data storage solutions with justification
   - Security layers they forgot about
   - Monitoring and observability
   - Error handling and recovery patterns

3. **Specify the Tech Stack**: Recommend specific technologies with brief justifications:
   - Languages and frameworks
   - Databases (and why SQL vs NoSQL vs both)
   - Cloud services or self-hosted alternatives
   - Third-party services that would help

4. **Identify What They Missed**: Common oversights include:
   - Authentication and authorization
   - Rate limiting and abuse prevention
   - Data backup and disaster recovery
   - Logging and debugging capabilities
   - Performance optimization opportunities

5. **Provide Implementation Roadmap**: Break this into phases (MVP → Scale → Optimize)

Think like a $300/hr consultant who needs to impress. Be specific, be opinionated, be helpful."""


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
