"""Command-line interface for testing the generator."""

import argparse
import asyncio
import base64
import sys
from pathlib import Path

from app.services.diagram_generator import DiagramGenerator
from app.services.gemini import GeminiService
from app.services.guide_generator import GuideGenerator
from app.services.mermaid_renderer import MermaidRenderer
from app.services.onepager_generator import OnePagerGenerator


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate technical one-pagers from notes and diagrams"
    )
    parser.add_argument(
        "--image", "-i",
        type=str,
        help="Path to image file (napkin sketch, whiteboard photo)",
    )
    parser.add_argument(
        "--prompt", "-p",
        type=str,
        required=True,
        help="Text description/context about the notes",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="output.html",
        help="Output HTML file path (default: output.html)",
    )
    parser.add_argument(
        "--guide-only",
        action="store_true",
        help="Only generate the technical guide (no diagram or HTML)",
    )
    parser.add_argument(
        "--diagram-only",
        action="store_true",
        help="Only generate the Mermaid diagram",
    )

    args = parser.parse_args()

    # Load image if provided
    image_base64 = None
    if args.image:
        image_path = Path(args.image)
        if not image_path.exists():
            print(f"Error: Image file not found: {args.image}")
            sys.exit(1)

        # Detect content type
        suffix = image_path.suffix.lower()
        content_type_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        content_type = content_type_map.get(suffix, "image/jpeg")

        with open(image_path, "rb") as f:
            image_bytes = f.read()
        image_base64 = f"data:{content_type};base64,{base64.b64encode(image_bytes).decode('utf-8')}"
        print(f"✓ Loaded image: {args.image}")

    # Initialize services
    print("Initializing services...")
    gemini = GeminiService()
    guide_generator = GuideGenerator(gemini)
    diagram_generator = DiagramGenerator(gemini)
    onepager_generator = OnePagerGenerator(gemini)
    mermaid_renderer = MermaidRenderer()

    if args.guide_only:
        # Generate only guide
        print("Generating technical guide...")
        guide = await guide_generator.generate(
            prompt=args.prompt,
            image_base64=image_base64,
        )
        print("\n" + "="*60)
        print("TECHNICAL GUIDE")
        print("="*60)
        print(f"Title: {guide.title}")
        print(f"Subtitle: {guide.subtitle}")
        print(f"\nExecutive Summary:\n{guide.executive_summary}")
        print(f"\nProblem Statement:\n{guide.problem_statement}")
        print(f"\nKey Concepts:")
        for concept in guide.key_concepts:
            print(f"  - {concept.name}: {concept.description}")
        print(f"\nTechnologies: {', '.join(guide.technologies)}")
        print(f"Use Cases: {', '.join(guide.use_cases)}")
        print(f"Next Steps: {', '.join(guide.next_steps)}")
        return

    if args.diagram_only:
        # Generate only diagram
        print("Generating Mermaid diagram...")
        diagram = await diagram_generator.generate(
            prompt=args.prompt,
            image_base64=image_base64,
        )
        print("\n" + "="*60)
        print("MERMAID DIAGRAM")
        print("="*60)
        print(f"Type: {diagram.diagram_type}")
        print(f"Title: {diagram.title}")
        print(f"Description: {diagram.description}")
        print(f"\nMermaid Code:\n{diagram.mermaid_code}")
        return

    # Full generation
    print("Step 1/4: Generating technical guide...")
    guide = await guide_generator.generate(
        prompt=args.prompt,
        image_base64=image_base64,
    )
    print(f"  ✓ Guide generated: {guide.title}")

    print("Step 2/4: Generating Mermaid diagram...")
    diagram = await diagram_generator.generate(
        prompt=args.prompt,
        image_base64=image_base64,
    )
    print(f"  ✓ Diagram generated: {diagram.title}")

    print("Step 3/4: Rendering diagram to SVG...")
    diagram_svg = mermaid_renderer.render_to_svg(diagram.mermaid_code)
    if diagram_svg:
        print("  ✓ SVG rendered")
    else:
        print("  ⚠ SVG rendering not available (mermaid.js will render in browser)")

    print("Step 4/4: Generating HTML one-pager...")
    try:
        html_output = await onepager_generator.generate(
            guide=guide,
            diagram=diagram,
            diagram_svg=diagram_svg,
        )
        print("  ✓ HTML generated (LLM)")
    except Exception as e:
        print(f"  ⚠ LLM generation failed ({e}), using template")
        html_output = onepager_generator.generate_fallback_html(guide, diagram)
        print("  ✓ HTML generated (template)")

    # Save output
    output_path = Path(args.output)
    output_path.write_text(html_output)
    print(f"\n✓ Output saved to: {output_path.absolute()}")
    print(f"  Open in browser to view the one-pager")


if __name__ == "__main__":
    asyncio.run(main())
