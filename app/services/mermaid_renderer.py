"""Mermaid diagram rendering service."""

import os
import subprocess
import tempfile
from pathlib import Path


class MermaidRenderer:
    """Service for rendering Mermaid diagrams to SVG/PNG/CSS."""

    def __init__(self):
        """Initialize the renderer."""
        self._check_mermaid_cli()

    def _check_mermaid_cli(self) -> bool:
        """Check if mermaid-cli (mmdc) is available."""
        try:
            result = subprocess.run(
                ["mmdc", "--version"],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def render_to_svg(self, mermaid_code: str) -> str | None:
        """
        Render Mermaid diagram to SVG string.

        Args:
            mermaid_code: Mermaid diagram code

        Returns:
            SVG string or None if rendering fails
        """
        try:
            # Try using mermaid-py first (Python native)
            from mermaid import Mermaid
            from mermaid.graph import Graph

            graph = Graph("diagram", mermaid_code)
            mermaid = Mermaid(graph)
            return mermaid.svg
        except ImportError:
            pass
        except Exception:
            pass

        # Fallback to mermaid-cli if available
        if not self._check_mermaid_cli():
            return None

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                input_file = Path(tmpdir) / "diagram.mmd"
                output_file = Path(tmpdir) / "diagram.svg"

                input_file.write_text(mermaid_code)

                result = subprocess.run(
                    ["mmdc", "-i", str(input_file), "-o", str(output_file), "-b", "transparent"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0 and output_file.exists():
                    return output_file.read_text()
        except Exception:
            pass

        return None

    def render_to_png_base64(self, mermaid_code: str) -> str | None:
        """
        Render Mermaid diagram to base64 encoded PNG.

        Args:
            mermaid_code: Mermaid diagram code

        Returns:
            Base64 encoded PNG or None if rendering fails
        """
        import base64

        if not self._check_mermaid_cli():
            return None

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                input_file = Path(tmpdir) / "diagram.mmd"
                output_file = Path(tmpdir) / "diagram.png"

                input_file.write_text(mermaid_code)

                result = subprocess.run(
                    ["mmdc", "-i", str(input_file), "-o", str(output_file), "-b", "white"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0 and output_file.exists():
                    png_bytes = output_file.read_bytes()
                    return base64.b64encode(png_bytes).decode("utf-8")
        except Exception:
            pass

        return None

    def get_inline_styles(self) -> str:
        """
        Get CSS styles for inline Mermaid rendering in HTML.

        Returns:
            CSS styles for Mermaid diagrams
        """
        return """
        /* Mermaid diagram styling */
        .mermaid {
            display: flex;
            justify-content: center;
            margin: 2rem 0;
        }

        .mermaid svg {
            max-width: 100%;
            height: auto;
        }

        /* Custom styling for mermaid elements */
        .mermaid .node rect,
        .mermaid .node circle,
        .mermaid .node ellipse,
        .mermaid .node polygon,
        .mermaid .node path {
            fill: #e3f2fd;
            stroke: #1976d2;
            stroke-width: 2px;
        }

        .mermaid .label {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 14px;
            color: #333;
        }

        .mermaid .edgePath path {
            stroke: #90a4ae;
            stroke-width: 2px;
        }

        .mermaid .arrowheadPath {
            fill: #90a4ae;
        }
        """
