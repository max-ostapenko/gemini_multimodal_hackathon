"""One-pager HTML generation service."""

from app.models.schemas import MermaidDiagram, TechnicalGuide
from app.services.gemini import GeminiService
from app.services.mermaid_renderer import MermaidRenderer

HTML_GENERATION_SYSTEM_INSTRUCTION = """You are an expert web designer and technical writer.
Your task is to create beautiful, professional HTML one-pagers that effectively communicate technical concepts.

Design principles:
- Clean, modern design with good typography
- Professional color scheme (prefer blues, grays, with accent colors)
- Mobile-responsive layout
- Clear visual hierarchy
- Good use of whitespace
- Engaging but not overwhelming

Technical requirements:
- Self-contained HTML with inline CSS
- Use modern CSS features (flexbox, grid, CSS variables)
- Include the Mermaid diagram using the mermaid.js library
- Proper semantic HTML structure
- Include Inter font from Google Fonts
- Dark/light sections for visual interest
"""


class OnePagerGenerator:
    """Service for generating HTML one-pagers."""

    def __init__(self, gemini_service: GeminiService | None = None):
        """Initialize the generator."""
        self.gemini = gemini_service or GeminiService()
        self.mermaid_renderer = MermaidRenderer()

    async def generate(
        self,
        guide: TechnicalGuide,
        diagram: MermaidDiagram,
        diagram_svg: str | None = None,
    ) -> str:
        """
        Generate an HTML one-pager from guide and diagram.

        Args:
            guide: Technical guide data
            diagram: Mermaid diagram data
            diagram_svg: Optional pre-rendered SVG of the diagram

        Returns:
            Complete HTML document as string
        """
        # Get mermaid CSS for styling
        mermaid_css = self.mermaid_renderer.get_inline_styles()

        prompt = f"""Create a stunning, professional HTML one-pager for the following technical content.

TECHNICAL GUIDE:
Title: {guide.title}
Subtitle: {guide.subtitle}
Executive Summary: {guide.executive_summary}
Problem Statement: {guide.problem_statement}
Target Audience: {guide.target_audience}

Key Concepts:
{self._format_concepts(guide.key_concepts)}

Sections:
{self._format_sections(guide.sections)}

Technologies: {', '.join(guide.technologies)}
Use Cases: {', '.join(guide.use_cases)}
Next Steps: {', '.join(guide.next_steps)}

MERMAID DIAGRAM:
Type: {diagram.diagram_type}
Title: {diagram.title}
Description: {diagram.description}
Code:
```mermaid
{diagram.mermaid_code}
```

ADDITIONAL STYLING CSS:
{mermaid_css}

REQUIREMENTS:
1. Create a complete, self-contained HTML document
2. Use inline CSS (in <style> tags)
3. Include the Mermaid.js library via CDN to render the diagram
4. Design for a one-page format that could be printed or shared
5. Include all sections from the guide with good visual hierarchy
6. Make the diagram prominent and well-integrated
7. Add a professional header with the title and subtitle
8. Include a footer with "Generated with AI" note
9. Use the Inter font from Google Fonts
10. Make it responsive for different screen sizes

Return ONLY the complete HTML code, no explanations."""

        html = await self.gemini.generate_text(
            prompt=prompt,
            system_instruction=HTML_GENERATION_SYSTEM_INSTRUCTION,
        )

        # Clean up the response (remove markdown code blocks if present)
        html = html.strip()
        if html.startswith("```html"):
            html = html[7:]
        elif html.startswith("```"):
            html = html[3:]
        if html.endswith("```"):
            html = html[:-3]

        return html.strip()

    def _format_concepts(self, concepts) -> str:
        """Format key concepts for the prompt."""
        lines = []
        for c in concepts:
            lines.append(f"- {c.name}: {c.description} (Importance: {c.importance})")
        return "\n".join(lines) if lines else "None specified"

    def _format_sections(self, sections) -> str:
        """Format sections for the prompt."""
        lines = []
        for s in sections:
            lines.append(f"## {s.title}")
            lines.append(s.content)
            if s.key_points:
                lines.append("Key points:")
                for point in s.key_points:
                    lines.append(f"  - {point}")
            lines.append("")
        return "\n".join(lines) if lines else "None specified"

    def generate_fallback_html(
        self,
        guide: TechnicalGuide,
        diagram: MermaidDiagram,
    ) -> str:
        """
        Generate a fallback HTML one-pager using a template.

        This is used if the LLM generation fails.
        """
        mermaid_css = self.mermaid_renderer.get_inline_styles()

        sections_html = ""
        for section in guide.sections:
            key_points_html = ""
            if section.key_points:
                key_points_html = "<ul>" + "".join(f"<li>{p}</li>" for p in section.key_points) + "</ul>"

            sections_html += f"""
            <section class="content-section">
                <h2>{section.title}</h2>
                <div class="section-content">{section.content}</div>
                {key_points_html}
            </section>
            """

        concepts_html = ""
        if guide.key_concepts:
            concepts_html = "<div class='concepts-grid'>"
            for concept in guide.key_concepts:
                concepts_html += f"""
                <div class="concept-card">
                    <h3>{concept.name}</h3>
                    <p>{concept.description}</p>
                    <span class="importance">{concept.importance}</span>
                </div>
                """
            concepts_html += "</div>"

        technologies_html = ""
        if guide.technologies:
            technologies_html = "<div class='tech-tags'>" + "".join(
                f"<span class='tag'>{t}</span>" for t in guide.technologies
            ) + "</div>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{guide.title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        :root {{
            --primary: #1976d2;
            --primary-dark: #1565c0;
            --secondary: #424242;
            --accent: #00acc1;
            --bg: #ffffff;
            --bg-alt: #f5f7fa;
            --text: #333333;
            --text-light: #666666;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            line-height: 1.6;
            color: var(--text);
            background: var(--bg);
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 2rem;
        }}

        header {{
            background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
            color: white;
            padding: 4rem 0;
            text-align: center;
        }}

        header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}

        header .subtitle {{
            font-size: 1.25rem;
            opacity: 0.9;
        }}

        .executive-summary {{
            background: var(--bg-alt);
            padding: 3rem 0;
            text-align: center;
        }}

        .executive-summary p {{
            font-size: 1.25rem;
            max-width: 800px;
            margin: 0 auto;
            color: var(--text-light);
        }}

        .problem-section {{
            padding: 3rem 0;
            border-bottom: 1px solid #eee;
        }}

        .problem-section h2 {{
            color: var(--primary);
            margin-bottom: 1rem;
        }}

        .diagram-section {{
            padding: 3rem 0;
            background: var(--bg-alt);
        }}

        .diagram-section h2 {{
            text-align: center;
            margin-bottom: 1rem;
        }}

        .diagram-description {{
            text-align: center;
            color: var(--text-light);
            margin-bottom: 2rem;
        }}

        {mermaid_css}

        .concepts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.5rem;
            padding: 2rem 0;
        }}

        .concept-card {{
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}

        .concept-card h3 {{
            color: var(--primary);
            margin-bottom: 0.5rem;
        }}

        .concept-card .importance {{
            display: inline-block;
            background: var(--accent);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            margin-top: 0.5rem;
        }}

        .content-section {{
            padding: 2rem 0;
            border-bottom: 1px solid #eee;
        }}

        .content-section h2 {{
            color: var(--secondary);
            margin-bottom: 1rem;
        }}

        .content-section ul {{
            margin-top: 1rem;
            padding-left: 1.5rem;
        }}

        .tech-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            padding: 1rem 0;
        }}

        .tag {{
            background: var(--primary);
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
        }}

        .next-steps {{
            background: var(--primary);
            color: white;
            padding: 3rem 0;
        }}

        .next-steps h2 {{
            margin-bottom: 1.5rem;
        }}

        .next-steps ul {{
            list-style: none;
        }}

        .next-steps li {{
            padding: 0.5rem 0;
            padding-left: 1.5rem;
            position: relative;
        }}

        .next-steps li::before {{
            content: "→";
            position: absolute;
            left: 0;
        }}

        footer {{
            text-align: center;
            padding: 2rem 0;
            color: var(--text-light);
            font-size: 0.9rem;
        }}

        @media (max-width: 768px) {{
            header h1 {{
                font-size: 1.75rem;
            }}

            .container {{
                padding: 0 1rem;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <div class="container">
            <h1>{guide.title}</h1>
            <p class="subtitle">{guide.subtitle}</p>
        </div>
    </header>

    <section class="executive-summary">
        <div class="container">
            <p>{guide.executive_summary}</p>
        </div>
    </section>

    <section class="problem-section">
        <div class="container">
            <h2>The Problem</h2>
            <p>{guide.problem_statement}</p>
        </div>
    </section>

    <section class="diagram-section">
        <div class="container">
            <h2>{diagram.title}</h2>
            <p class="diagram-description">{diagram.description}</p>
            <div class="mermaid">
{diagram.mermaid_code}
            </div>
        </div>
    </section>

    <section class="concepts-section">
        <div class="container">
            <h2>Key Concepts</h2>
            {concepts_html}
        </div>
    </section>

    <main class="container">
        {sections_html}

        <section class="tech-section">
            <h2>Technologies</h2>
            {technologies_html}
        </section>
    </main>

    <section class="next-steps">
        <div class="container">
            <h2>Next Steps</h2>
            <ul>
                {"".join(f"<li>{step}</li>" for step in guide.next_steps)}
            </ul>
        </div>
    </section>

    <footer>
        <p>Target Audience: {guide.target_audience}</p>
        <p>Generated with AI • Technical Notes to One-Pager</p>
    </footer>

    <script>
        mermaid.initialize({{ startOnLoad: true, theme: 'default' }});
    </script>
</body>
</html>"""
