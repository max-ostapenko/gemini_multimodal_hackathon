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

    def validate_syntax(self, mermaid_code: str) -> tuple[bool, str | None]:
        """
        Validate Mermaid diagram syntax.

        Args:
            mermaid_code: Mermaid diagram code to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Try mermaid-py first (with multiple API attempts for different versions)
        try:
            from mermaid import Mermaid
            from mermaid.graph import Graph

            graph = Graph("validation", mermaid_code)
            mermaid = Mermaid(graph)
            
            # Try different API methods depending on mermaid-py version
            if hasattr(mermaid, 'svg'):
                _ = mermaid.svg
            elif hasattr(mermaid, 'to_svg'):
                _ = mermaid.to_svg()
            elif hasattr(mermaid, '_repr_html_'):
                _ = mermaid._repr_html_()
            # If none of the above, just check if object was created successfully
            return True, None
        except ImportError:
            pass
        except Exception as e:
            # Don't fail on mermaid-py issues - we have frontend rendering
            # Only return error if it's clearly a syntax error
            error_str = str(e)
            if 'parse' in error_str.lower() or 'syntax' in error_str.lower():
                return False, error_str
            # Otherwise, assume it's a library issue, not syntax
            pass

        # Fallback to mermaid-cli validation
        if self._check_mermaid_cli():
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    input_file = Path(tmpdir) / "diagram.mmd"
                    output_file = Path(tmpdir) / "diagram.svg"

                    input_file.write_text(mermaid_code)

                    result = subprocess.run(
                        ["mmdc", "-i", str(input_file), "-o", str(output_file)],
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )

                    if result.returncode == 0:
                        return True, None
                    else:
                        error_msg = result.stderr or result.stdout or "Unknown mermaid syntax error"
                        return False, error_msg
            except Exception as e:
                return False, str(e)

        # If no validation tool available, do basic syntax check
        return self._basic_syntax_check(mermaid_code)

    def _basic_syntax_check(self, mermaid_code: str) -> tuple[bool, str | None]:
        """Basic syntax validation when no mermaid tools available."""
        code = mermaid_code.strip()

        # Check for common diagram type declarations
        valid_starts = [
            "graph ", "graph\n",
            "flowchart ", "flowchart\n",
            "sequenceDiagram",
            "classDiagram",
            "stateDiagram",
            "erDiagram",
            "journey",
            "gantt",
            "pie",
            "gitGraph",
            "mindmap",
            "timeline",
        ]

        has_valid_start = any(code.startswith(start) for start in valid_starts)
        if not has_valid_start:
            return False, f"Diagram must start with a valid type declaration (e.g., 'flowchart TD', 'sequenceDiagram', etc.). Got: {code[:50]}..."

        # Check for balanced brackets
        brackets = {'[': ']', '{': '}', '(': ')'}
        stack = []
        for char in code:
            if char in brackets:
                stack.append(brackets[char])
            elif char in brackets.values():
                if not stack or stack.pop() != char:
                    return False, f"Unbalanced brackets in diagram"

        if stack:
            return False, f"Unclosed brackets in diagram"

        return True, None

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
            
            # Try different API methods depending on mermaid-py version
            if hasattr(mermaid, 'svg'):
                return mermaid.svg
            elif hasattr(mermaid, 'to_svg'):
                return mermaid.to_svg()
            elif hasattr(mermaid, '_repr_svg_'):
                return mermaid._repr_svg_()
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
