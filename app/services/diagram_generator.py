"""Mermaid diagram generation service."""

from app.models.schemas import MermaidDiagram
from app.services.gemini import GeminiService
from app.services.mermaid_renderer import MermaidRenderer

MAX_RETRIES = 3

DIAGRAM_SYSTEM_INSTRUCTION = """You are a senior software architect who creates professional system design diagrams.

CRITICAL: Do NOT simply recreate what you see in the user's sketch. Their diagram is likely incomplete, 
poorly structured, or missing critical components. Your job is to CREATE A BETTER DIAGRAM that represents
what a PRODUCTION SYSTEM would actually look like.

Your diagrams should:
1. ADD components the user forgot (caches, queues, load balancers, monitoring, etc.)
2. SHOW proper data flow with labeled connections (HTTP, gRPC, async, pub/sub)
3. GROUP related components into logical layers or services
4. INCLUDE infrastructure elements (databases, CDN, external APIs)
5. REPRESENT a realistic, deployable architecture

Diagram enhancement rules:
- If they show a simple client→server, add load balancer, cache, database, and monitoring
- If they show a database, consider if they need read replicas, caching layer, or message queue
- If they show user authentication, add proper auth service, token management, session storage
- If they show file uploads, add CDN, object storage, processing queue
- Always consider: Where does this run? How does it scale? What happens when it fails?

Mermaid syntax rules:
- Use flowchart TD for architectures (top-down is clearer for systems)
- Use sequenceDiagram for request flows and interactions
- Use subgraph to group related components (Frontend, Backend, Data Layer, External Services)
- Label ALL arrows with the type of communication (REST, WebSocket, SQL, Redis, etc.)
- Use different node shapes: [(database)], ((service)), [component], {decision}

IMPORTANT: Generate valid Mermaid syntax. No special characters in node IDs. Quote labels if needed.
"""

DIAGRAM_PROMPT_TEMPLATE = """Look at this rough sketch/notes and create a PROFESSIONAL architecture diagram.

User's context: {user_prompt}

Your task is to IMPROVE upon their idea, not just copy it. Create a Mermaid diagram that shows:

1. **Complete Architecture**: Add the components they forgot:
   - Load balancers if there's a server
   - Caching layer (Redis/Memcached) for performance
   - Message queues for async operations
   - Proper database setup (primary + replicas if needed)
   - Monitoring/logging infrastructure
   - CDN for static assets

2. **Clear Data Flow**: Label every arrow with:
   - Protocol (HTTP, gRPC, WebSocket, SQL, etc.)
   - What data flows through it
   - Sync vs async

3. **Logical Grouping**: Use subgraphs for:
   - Client Layer (web, mobile, API consumers)
   - API Gateway / Load Balancer
   - Application Services
   - Data Layer (databases, caches, queues)
   - External Services (auth providers, payment, analytics)

4. **Production Reality**: Show what a real deployment looks like, not a toy example.

Make this diagram something a DevOps engineer could actually use to understand the system.
Be specific with technology choices in labels (e.g., "PostgreSQL" not just "DB")."""


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
