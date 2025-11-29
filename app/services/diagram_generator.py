"""Mermaid diagram generation service."""

from app.models.schemas import MermaidDiagram
from app.services.gemini import GeminiService
from app.services.mermaid_renderer import MermaidRenderer
from app.services.diagram_agent import DiagramFixerAgent, MermaidSyntaxChecker
from app.services.mermaid_example import WORKING_EXAMPLE, SYNTAX_RULES_SUMMARY

DIAGRAM_SYSTEM_INSTRUCTION = f"""You are a senior software architect who creates professional system design diagrams.

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

=== CRITICAL MERMAID SYNTAX RULES ===

FLOWCHART EDGE LABELS (VERY IMPORTANT):
- CORRECT: A -->|label text| B
- WRONG: A --> B: label text  (THIS WILL BREAK!)
- The colon syntax is ONLY for sequenceDiagram, NOT flowcharts!

NODE IDs:
- CORRECT: API_Gateway, User_Service, Redis_Cache
- WRONG: API Gateway, User Service (NO SPACES!)

NODE LABELS WITH SPECIAL CHARACTERS (CRITICAL!):
- If label contains parentheses (), use DOUBLE QUOTES inside brackets
- CORRECT: MyNode["Label with (parentheses)"]
- WRONG: MyNode[Label with (parentheses)]  <-- THIS BREAKS!
- CORRECT: DB["PostgreSQL (Primary)"]
- CORRECT: Cache["Redis (Cluster)"]
- CORRECT: User["User Device (Web/Mobile)"]

NODE SHAPES:
- Rectangle: [Label] or ["Label with special chars"]
- Rounded: (Label)
- Stadium: ([Label])
- Database: [(Label)] or [("Label with special")]
- Circle: ((Label))
- Diamond: {Label}

SUBGRAPHS:
- Must have matching 'end' for each 'subgraph'
- Format: subgraph Title\\n  content\\nend

ARROWS:
- --> : solid arrow
- --- : solid line
- -.-> : dotted arrow
- ==> : thick arrow

=== FULL WORKING EXAMPLE (STUDY THIS CAREFULLY!) ===
{WORKING_EXAMPLE}
=== END EXAMPLE ===

{SYNTAX_RULES_SUMMARY}

IMPORTANT: Your output MUST follow the exact same syntax patterns as the working example above!
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

2. **Clear Data Flow**: Label every arrow using CORRECT syntax:
   - FLOWCHART: A -->|protocol/data type| B
   - NOT: A --> B: label (this is WRONG for flowcharts!)

3. **Logical Grouping**: Use subgraphs for:
   - Client Layer (web, mobile, API consumers)
   - API Gateway / Load Balancer
   - Application Services
   - Data Layer (databases, caches, queues)
   - External Services (auth providers, payment, analytics)

4. **Production Reality**: Show what a real deployment looks like, not a toy example.

REMINDER - CORRECT EDGE LABEL SYNTAX FOR FLOWCHARTS:
✓ User -->|HTTP/HTTPS| LoadBalancer
✗ User --> LoadBalancer: HTTP/HTTPS  (WRONG!)

Make this diagram something a DevOps engineer could actually use to understand the system.
Be specific with technology choices in labels (e.g., "PostgreSQL" not just "DB")."""


class DiagramGenerator:
    """Service for generating Mermaid diagrams from multimodal input."""

    def __init__(self, gemini_service: GeminiService | None = None):
        """Initialize the diagram generator."""
        self.gemini = gemini_service or GeminiService()
        self.renderer = MermaidRenderer()
        self.syntax_checker = MermaidSyntaxChecker()
        self.fixer_agent = DiagramFixerAgent(self.gemini)

    async def generate(
        self,
        prompt: str,
        image_base64: str | None = None,
    ) -> MermaidDiagram:
        """
        Generate a Mermaid diagram from notes/diagram with agentic validation.

        Flow:
        1. Generate initial diagram from LLM
        2. Validate with MermaidSyntaxChecker
        3. If invalid, delegate to DiagramFixerAgent for iterative fixing
        4. Return the final diagram

        Args:
            prompt: User's description/context about the notes
            image_base64: Base64 encoded image of the notes/diagram

        Returns:
            Structured MermaidDiagram object
        """
        full_prompt = DIAGRAM_PROMPT_TEMPLATE.format(user_prompt=prompt)

        # Step 1: Generate initial diagram
        print("DiagramGenerator: Generating initial diagram...")
        diagram = await self.gemini.generate_structured_output(
            prompt=full_prompt,
            response_schema=MermaidDiagram,
            image_base64=image_base64,
            system_instruction=DIAGRAM_SYSTEM_INSTRUCTION,
        )

        # Step 2: Validate with our syntax checker first
        validation = self.syntax_checker.validate(diagram.mermaid_code)
        
        if validation.is_valid:
            print("DiagramGenerator: Initial diagram passed validation")
            # Also verify with renderer for complete validation
            is_valid, error_msg = self.renderer.validate_syntax(diagram.mermaid_code)
            if is_valid:
                return diagram
            # If renderer found issues our checker missed, proceed to fix
            validation.is_valid = False
            validation.error_message = error_msg

        # Step 3: Diagram has errors - delegate to fixer agent
        print(f"DiagramGenerator: Validation failed - {validation.error_message}")
        print("DiagramGenerator: Delegating to DiagramFixerAgent...")
        
        fixed_code, is_fixed, iterations = await self.fixer_agent.fix(
            broken_code=diagram.mermaid_code,
            error_message=validation.error_message or "Unknown syntax error",
            original_error_type=validation.error_type,
        )

        # Step 4: Update diagram with fixed code
        if is_fixed:
            print(f"DiagramGenerator: Diagram fixed successfully in {iterations} iteration(s)")
            diagram.mermaid_code = fixed_code
        else:
            print(f"DiagramGenerator: Warning - returning diagram with potential errors after {iterations} fix attempts")
            diagram.mermaid_code = fixed_code  # Use best effort

        return diagram
