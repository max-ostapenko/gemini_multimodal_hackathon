"""Agentic diagram validation and fixing service."""

import asyncio
import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from app.models.schemas import MermaidDiagram
from app.services.gemini import GeminiService


class MermaidErrorType(Enum):
    """Categories of Mermaid syntax errors."""
    LABEL_SYNTAX = "label_syntax"  # Wrong edge label format (A --> B: label)
    BRACKET_MISMATCH = "bracket_mismatch"  # Unbalanced brackets
    INVALID_NODE_ID = "invalid_node_id"  # Spaces or special chars in node IDs
    INVALID_ARROW = "invalid_arrow"  # Wrong arrow syntax
    MISSING_DECLARATION = "missing_declaration"  # No diagram type declaration
    SUBGRAPH_ERROR = "subgraph_error"  # Subgraph syntax issues
    QUOTE_ERROR = "quote_error"  # Unbalanced or missing quotes
    UNKNOWN = "unknown"


@dataclass
class ValidationResult:
    """Result of Mermaid syntax validation."""
    is_valid: bool
    error_message: Optional[str] = None
    error_type: MermaidErrorType = MermaidErrorType.UNKNOWN
    error_line: Optional[int] = None
    suggestion: Optional[str] = None


class MermaidSyntaxChecker:
    """Validates Mermaid diagram syntax and categorizes errors."""

    # Pattern for detecting wrong edge label syntax in flowcharts
    WRONG_LABEL_PATTERN = re.compile(r'(\w+)\s*--+>?\s*(\w+)\s*:\s*(.+?)(?=\n|$)')
    
    # Pattern for valid flowchart declarations
    FLOWCHART_PATTERN = re.compile(r'^(flowchart|graph)\s+(TD|TB|BT|RL|LR)', re.MULTILINE)
    
    # Pattern for sequence diagram
    SEQUENCE_PATTERN = re.compile(r'^sequenceDiagram', re.MULTILINE)
    
    # Pattern for unquoted labels with parentheses (CRITICAL BUG SOURCE)
    # Matches: NodeId[Label with (parentheses)] but NOT NodeId["Label with (parentheses)"]
    UNQUOTED_PARENS_PATTERN = re.compile(r'(\w+)\[([^\]"]*\([^\]]*\)[^\]"]*)\]')

    def validate(self, code: str) -> ValidationResult:
        """
        Validate Mermaid diagram syntax.
        
        Args:
            code: Mermaid diagram code
            
        Returns:
            ValidationResult with details about validity and any errors
        """
        code = code.strip()
        
        # Check for empty code
        if not code:
            return ValidationResult(
                is_valid=False,
                error_message="Empty diagram code",
                error_type=MermaidErrorType.MISSING_DECLARATION,
                suggestion="Provide a valid Mermaid diagram starting with diagram type declaration"
            )
        
        # Check for diagram type declaration
        has_flowchart = self.FLOWCHART_PATTERN.search(code)
        has_sequence = self.SEQUENCE_PATTERN.search(code)
        
        if not has_flowchart and not has_sequence and not self._has_valid_declaration(code):
            return ValidationResult(
                is_valid=False,
                error_message="Missing or invalid diagram type declaration",
                error_type=MermaidErrorType.MISSING_DECLARATION,
                suggestion="Start with 'flowchart TD', 'sequenceDiagram', 'classDiagram', etc."
            )
        
        # Check for unquoted parentheses in labels (CRITICAL - causes parse errors)
        if has_flowchart:
            unquoted_parens = self.UNQUOTED_PARENS_PATTERN.findall(code)
            if unquoted_parens:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Unquoted parentheses in label: '{unquoted_parens[0][0]}[{unquoted_parens[0][1]}]'",
                    error_type=MermaidErrorType.QUOTE_ERROR,
                    suggestion='Labels with parentheses need quotes: NodeId["Label (with parens)"]'
                )
        
        # Check for wrong edge label syntax in flowcharts (A --> B: label)
        if has_flowchart:
            wrong_labels = self.WRONG_LABEL_PATTERN.findall(code)
            if wrong_labels:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Invalid edge label syntax: '{wrong_labels[0][0]} --> {wrong_labels[0][1]}: {wrong_labels[0][2]}'",
                    error_type=MermaidErrorType.LABEL_SYNTAX,
                    suggestion="Use pipe syntax for flowchart labels: A -->|label text| B"
                )
        
        # Check for unbalanced brackets
        bracket_result = self._check_brackets(code)
        if not bracket_result.is_valid:
            return bracket_result
        
        # Check for invalid node IDs (spaces in IDs)
        invalid_id_result = self._check_node_ids(code)
        if not invalid_id_result.is_valid:
            return invalid_id_result
        
        # Check subgraph syntax
        subgraph_result = self._check_subgraphs(code)
        if not subgraph_result.is_valid:
            return subgraph_result
        
        return ValidationResult(is_valid=True)

    def _has_valid_declaration(self, code: str) -> bool:
        """Check if code has any valid Mermaid diagram declaration."""
        valid_starts = [
            'graph ', 'graph\n',
            'flowchart ', 'flowchart\n',
            'sequenceDiagram',
            'classDiagram',
            'stateDiagram',
            'erDiagram',
            'journey',
            'gantt',
            'pie',
            'gitGraph',
            'mindmap',
            'timeline',
        ]
        return any(code.strip().startswith(start) for start in valid_starts)

    def _check_brackets(self, code: str) -> ValidationResult:
        """Check for balanced brackets."""
        brackets = {'[': ']', '{': '}', '(': ')'}
        stack = []
        
        for i, char in enumerate(code):
            if char in brackets:
                stack.append((brackets[char], i))
            elif char in brackets.values():
                if not stack:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Unexpected closing bracket '{char}' at position {i}",
                        error_type=MermaidErrorType.BRACKET_MISMATCH,
                        suggestion="Check for unbalanced brackets in node definitions"
                    )
                expected, _ = stack.pop()
                if expected != char:
                    return ValidationResult(
                        is_valid=False,
                        error_message=f"Mismatched bracket: expected '{expected}', got '{char}'",
                        error_type=MermaidErrorType.BRACKET_MISMATCH,
                        suggestion="Ensure all brackets are properly matched"
                    )
        
        if stack:
            return ValidationResult(
                is_valid=False,
                error_message=f"Unclosed bracket '{list(brackets.keys())[list(brackets.values()).index(stack[0][0])]}'",
                error_type=MermaidErrorType.BRACKET_MISMATCH,
                suggestion="Close all open brackets"
            )
        
        return ValidationResult(is_valid=True)

    def _check_node_ids(self, code: str) -> ValidationResult:
        """Check for invalid node IDs (spaces in node IDs, not in labels)."""
        lines = code.split('\n')
        for i, line in enumerate(lines):
            # Skip comments and empty lines
            line = line.strip()
            if not line or line.startswith('%%'):
                continue
            
            # Skip lines that are just arrows/connections or subgraph declarations
            if line.startswith('subgraph') or line.startswith('end') or '-->' in line or '---' in line:
                continue
            
            # Look for node definitions: NodeId[label] or NodeId["label"] etc.
            # Invalid: "My Node[label]" - space in node ID
            # Valid: "MyNode[My Label]" - space in label is fine
            # Valid: MyNode["Label (with parens)"] - quoted label is fine
            
            # Pattern: word, space, word, then bracket WITHOUT a quote before the space
            # This catches: My Node[...] but not MyNode["My Label"]
            node_def_match = re.match(r'^(\w+)\s+(\w+)\s*[\[\(\{]', line)
            if node_def_match:
                # This looks like "Word1 Word2[" which is invalid node ID
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Invalid node ID with space on line {i+1}: '{node_def_match.group(0)}'",
                    error_type=MermaidErrorType.INVALID_NODE_ID,
                    suggestion="Use underscores instead of spaces in node IDs: My_Node instead of My Node"
                )
        
        return ValidationResult(is_valid=True)

    def _check_subgraphs(self, code: str) -> ValidationResult:
        """Check subgraph syntax."""
        subgraph_opens = code.count('subgraph ')
        subgraph_closes = code.count('\n    end') + code.count('\nend')
        
        # Also count 'end' at the end of file
        if code.rstrip().endswith('end'):
            subgraph_closes += 1
        
        if subgraph_opens > subgraph_closes:
            return ValidationResult(
                is_valid=False,
                error_message=f"Unclosed subgraph: {subgraph_opens} opened, {subgraph_closes} closed",
                error_type=MermaidErrorType.SUBGRAPH_ERROR,
                suggestion="Each 'subgraph' must have a matching 'end'"
            )
        
        return ValidationResult(is_valid=True)

    def identify_error_type(self, error_message: str) -> MermaidErrorType:
        """
        Identify error type from an error message string.
        
        Args:
            error_message: Error message from Mermaid parser
            
        Returns:
            Categorized error type
        """
        error_lower = error_message.lower()
        
        if 'node_string' in error_lower or 'label' in error_lower:
            return MermaidErrorType.LABEL_SYNTAX
        elif 'bracket' in error_lower or 'unexpected' in error_lower:
            return MermaidErrorType.BRACKET_MISMATCH
        elif 'subgraph' in error_lower or 'end' in error_lower:
            return MermaidErrorType.SUBGRAPH_ERROR
        elif 'arrow' in error_lower or 'link' in error_lower:
            return MermaidErrorType.INVALID_ARROW
        elif 'quote' in error_lower:
            return MermaidErrorType.QUOTE_ERROR
        else:
            return MermaidErrorType.UNKNOWN

    def get_fix_hint(self, error_type: MermaidErrorType) -> str:
        """Get a hint for fixing the given error type."""
        hints = {
            MermaidErrorType.LABEL_SYNTAX: (
                "CRITICAL FIX: In flowcharts, edge labels must use pipe syntax:\n"
                "WRONG: A --> B: some label\n"
                "RIGHT: A -->|some label| B\n"
                "The colon syntax (A --> B: label) is ONLY valid in sequenceDiagrams."
            ),
            MermaidErrorType.BRACKET_MISMATCH: (
                "Check all brackets are balanced:\n"
                "- Square brackets: [label]\n"
                "- Curly braces: {decision}\n"
                "- Parentheses: (rounded)\n"
                "- Double brackets: [[subroutine]]"
            ),
            MermaidErrorType.INVALID_NODE_ID: (
                "Node IDs cannot contain spaces. Use underscores:\n"
                "WRONG: My Node[Label]\n"
                "RIGHT: My_Node[Label]"
            ),
            MermaidErrorType.SUBGRAPH_ERROR: (
                "Each 'subgraph' must have a matching 'end':\n"
                "subgraph Title\n"
                "    A --> B\n"
                "end"
            ),
            MermaidErrorType.INVALID_ARROW: (
                "Valid arrow types:\n"
                "- --> : arrow\n"
                "- --- : line\n"
                "- -.-> : dotted arrow\n"
                "- ==> : thick arrow"
            ),
            MermaidErrorType.QUOTE_ERROR: (
                "CRITICAL: Labels with parentheses MUST have double quotes!\n"
                "WRONG: Node[Label (info)]  <-- This breaks!\n"
                'CORRECT: Node["Label (info)"]\n'
                'WRONG: DB[(Database (Primary))]\n'
                'CORRECT: DB[("Database (Primary)")]\n'
                "Add double quotes around ANY label containing ( or )"
            ),
            MermaidErrorType.UNKNOWN: (
                "Check Mermaid syntax documentation. Common issues:\n"
                "1. Edge labels in flowcharts: use A -->|label| B\n"
                "2. No spaces in node IDs\n"
                "3. Balance all brackets"
            ),
        }
        return hints.get(error_type, hints[MermaidErrorType.UNKNOWN])


# System instruction for the fixer agent - focused ONLY on fixing
FIXER_SYSTEM_INSTRUCTION = """You are a Mermaid diagram syntax fixer. Your ONLY job is to fix syntax errors in Mermaid diagrams.

You will receive:
1. Broken Mermaid code
2. Error message
3. Specific fix instructions

RULES:
1. ONLY fix the syntax error - do not add, remove, or change the diagram content
2. Preserve the original structure and meaning
3. Return ONLY the fixed Mermaid code - no explanations, no markdown code blocks
4. Apply the specific fix suggested

CRITICAL MERMAID SYNTAX RULES:
- FLOWCHART edge labels: A -->|label text| B (NEVER use A --> B: label)
- SEQUENCE diagram messages: A->>B: message text (colon syntax is OK here)
- Node IDs: No spaces (use underscores: My_Node not My Node)

LABELS WITH PARENTHESES (VERY IMPORTANT!):
- ANY label containing parentheses MUST be in double quotes
- WRONG: Node[Label (info)]  <-- BREAKS PARSER!
- CORRECT: Node["Label (info)"]
- WRONG: DB[(Database (Primary))]
- CORRECT: DB[("Database (Primary)")]
- This applies to ALL node shapes: [], [()], (()), etc.

- Subgraphs: Must have matching 'end' for each 'subgraph'
"""


class DiagramFixerAgent:
    """Agent dedicated to fixing Mermaid diagram syntax errors."""

    MAX_ITERATIONS = 3
    BASE_DELAY_SECONDS = 1.0  # Base delay between retries for rate limiting

    def __init__(self, gemini_service: GeminiService | None = None):
        """Initialize the fixer agent."""
        self.gemini = gemini_service or GeminiService()
        self.checker = MermaidSyntaxChecker()

    def auto_fix_common_issues(self, code: str) -> str:
        """
        Automatically fix common Mermaid syntax issues without LLM.
        This is faster and more reliable for known patterns.
        
        Args:
            code: Mermaid diagram code
            
        Returns:
            Fixed code
        """
        fixed = code
        
        # Fix 1: Add quotes to labels with parentheses
        # Pattern: NodeId[Label (with parens)] -> NodeId["Label (with parens)"]
        # But skip already quoted: NodeId["Label (with parens)"]
        def quote_parens_label(match):
            node_id = match.group(1)
            label = match.group(2)
            # Don't double-quote
            if label.startswith('"') and label.endswith('"'):
                return match.group(0)
            return f'{node_id}["{label}"]'
        
        # Fix square bracket labels with parentheses
        fixed = re.sub(r'(\w+)\[([^\]"]*\([^\]]*\)[^\]"]*)\]', quote_parens_label, fixed)
        
        # Fix 2: Database shape with parentheses: [(Label (info))] -> [("Label (info)")]
        def quote_db_parens_label(match):
            label = match.group(1)
            if label.startswith('"') and label.endswith('"'):
                return match.group(0)
            return f'[("{label}")]'
        
        fixed = re.sub(r'\[\(([^)]*\([^)]*\)[^)]*)\)\]', quote_db_parens_label, fixed)
        
        # Fix 3: Circle shape with parentheses: ((Label (info))) -> (("Label (info)"))
        def quote_circle_parens_label(match):
            label = match.group(1)
            if label.startswith('"') and label.endswith('"'):
                return match.group(0)
            return f'(("{label}"))'
        
        fixed = re.sub(r'\(\(([^)]*\([^)]*\)[^)]*)\)\)', quote_circle_parens_label, fixed)
        
        return fixed

    async def fix(
        self,
        broken_code: str,
        error_message: str,
        original_error_type: MermaidErrorType | None = None,
    ) -> tuple[str, bool, int]:
        """
        Attempt to fix broken Mermaid diagram code.
        
        Args:
            broken_code: The Mermaid code with syntax errors
            error_message: The error message from the parser
            original_error_type: Optional pre-identified error type
            
        Returns:
            Tuple of (fixed_code, is_valid, iterations_used)
        """
        # Step 0: Try auto-fix first (fast, no LLM needed)
        print("DiagramFixerAgent: Attempting auto-fix for common issues...")
        auto_fixed = self.auto_fix_common_issues(broken_code)
        
        if auto_fixed != broken_code:
            print("DiagramFixerAgent: Auto-fix applied changes")
            validation = self.checker.validate(auto_fixed)
            if validation.is_valid:
                print("DiagramFixerAgent: Auto-fix successful!")
                return auto_fixed, True, 0
            # Continue with auto-fixed code as starting point
            broken_code = auto_fixed
        
        current_code = broken_code
        
        # Identify error type if not provided
        if original_error_type is None:
            original_error_type = self.checker.identify_error_type(error_message)
        
        for iteration in range(self.MAX_ITERATIONS):
            # Get fix hint for this error type
            fix_hint = self.checker.get_fix_hint(original_error_type)
            
            # Build the fix prompt
            fix_prompt = self._build_fix_prompt(current_code, error_message, fix_hint)
            
            # Call LLM to fix
            try:
                fixed_code = await self.gemini.generate_text(
                    prompt=fix_prompt,
                    system_instruction=FIXER_SYSTEM_INSTRUCTION,
                )
                
                # Clean up response
                fixed_code = self._clean_response(fixed_code)
                
                # Validate the fix
                validation = self.checker.validate(fixed_code)
                
                if validation.is_valid:
                    print(f"DiagramFixerAgent: Fixed diagram in {iteration + 1} iteration(s)")
                    return fixed_code, True, iteration + 1
                
                # Update for next iteration
                current_code = fixed_code
                error_message = validation.error_message or "Unknown validation error"
                original_error_type = validation.error_type
                
                print(f"DiagramFixerAgent: Iteration {iteration + 1} still has errors: {error_message}")
                
            except Exception as e:
                print(f"DiagramFixerAgent: Error in iteration {iteration + 1}: {e}")
            
            # Rate limit delay with exponential backoff
            if iteration < self.MAX_ITERATIONS - 1:
                delay = self.BASE_DELAY_SECONDS * (2 ** iteration)
                await asyncio.sleep(delay)
        
        # Return last attempt even if not valid
        print(f"DiagramFixerAgent: Max iterations ({self.MAX_ITERATIONS}) reached, returning best effort")
        return current_code, False, self.MAX_ITERATIONS

    def _build_fix_prompt(self, code: str, error_message: str, fix_hint: str) -> str:
        """Build a focused prompt for fixing the diagram."""
        return f"""Fix this broken Mermaid diagram.

ERROR MESSAGE:
{error_message}

HOW TO FIX:
{fix_hint}

BROKEN CODE:
{code}

Return ONLY the fixed Mermaid code. No explanations, no markdown code blocks, just the corrected diagram code."""

    def _clean_response(self, response: str) -> str:
        """Clean up LLM response to extract just the Mermaid code."""
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith('```mermaid'):
            response = response[10:]
        elif response.startswith('```'):
            response = response[3:]
        
        if response.endswith('```'):
            response = response[:-3]
        
        return response.strip()

