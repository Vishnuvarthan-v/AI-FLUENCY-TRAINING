"""Day 3: tools for the agent you build yourself."""

import ast
import operator
import os
import re


# ============================================================
# TOOL 1: SAFE CALCULATOR
# ============================================================

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}


def _evaluate(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](
            _evaluate(node.left),
            _evaluate(node.right)
        )

    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](
            _evaluate(node.operand)
        )

    raise ValueError("Unsupported expression")


def calculator(expression: str) -> str:
    """Evaluate a basic arithmetic expression."""

    try:
        return str(
            _evaluate(
                ast.parse(expression, mode="eval").body
            )
        )

    except Exception as error:
        return (
            f"Calculator error: {error}. "
            "Use only numbers and + - * / ** ( )."
        )


# ============================================================
# TOOL 2: WEB PAGE READER
# ============================================================

TAG = re.compile(
    r"<(script|style)[^>]*>.*?</\1>|<[^>]+>",
    re.S | re.I
)

SPACES = re.compile(r"\s+")


def read_webpage(url: str, max_chars: int = 200000) -> str:
    """
    Fetch a web page or local HTML/text file
    and return its readable text.

    NOTE:
    max_chars is intentionally set to 200000
    for the context-overflow experiment.
    """

    try:

        # ----------------------------------------------------
        # Read an online webpage
        # ----------------------------------------------------

        if url.startswith("http://") or url.startswith("https://"):

            import requests

            response = requests.get(
                url,
                timeout=10,
                headers={
                    "User-Agent": "AgenticAI-Lab/1.0"
                }
            )

            response.raise_for_status()

            raw = response.text

        # ----------------------------------------------------
        # Read a local file
        # ----------------------------------------------------

        elif os.path.exists(url):

            with open(
                url,
                encoding="utf-8",
                errors="ignore"
            ) as file:

                raw = file.read()

        # ----------------------------------------------------
        # File does not exist
        # ----------------------------------------------------

        else:

            return (
                f"Read error: '{url}' is not a URL "
                "and no such file exists."
            )

    except Exception as error:

        return (
            f"Read error: "
            f"{type(error).__name__}: {error}"
        )

    # --------------------------------------------------------
    # Remove HTML tags
    # --------------------------------------------------------

    text = TAG.sub(" ", raw)

    # --------------------------------------------------------
    # Remove extra spaces/newlines
    # --------------------------------------------------------

    text = SPACES.sub(" ", text).strip()

    # --------------------------------------------------------
    # CONTEXT LIMIT
    # --------------------------------------------------------
    # For this experiment the limit is 200000 characters.
    # --------------------------------------------------------

    if len(text) > max_chars:

        text = (
            text[:max_chars]
            + f" ... [truncated, {len(text)} characters total]"
        )

    # --------------------------------------------------------
    # Empty page check
    # --------------------------------------------------------

    if not text:

        return "Read error: the page contained no readable text."

    return text


# ============================================================
# TOOL REGISTRY
# ============================================================

TOOL_FUNCTIONS = {
    "calculator": calculator,
    "read_webpage": read_webpage,
}


# ============================================================
# OPENAI-COMPATIBLE TOOL DEFINITIONS
# ============================================================

TOOLS = [

    {
        "type": "function",

        "function": {

            "name": "calculator",

            "description": (
                "Evaluate an arithmetic expression using "
                "+ - * / ** and brackets. "
                "For example: (12000 + 18000) * 0.9."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "expression": {
                        "type": "string",
                        "description": (
                            "The arithmetic expression "
                            "to evaluate."
                        )
                    }

                },

                "required": ["expression"]
            }
        }
    },


    {
        "type": "function",

        "function": {

            "name": "read_webpage",

            "description": (
                "Read a web page or a local HTML/text file "
                "and return its visible text. "
                "Give a full URL such as "
                "https://example.com or a local file name "
                "such as notice.html."
            ),

            "parameters": {

                "type": "object",

                "properties": {

                    "url": {
                        "type": "string",
                        "description": (
                            "URL or local file name to read."
                        )
                    }

                },

                "required": ["url"]
            }
        }
    }

]


# ============================================================
# TEST THE TOOLS DIRECTLY
# ============================================================

if __name__ == "__main__":

    print("=== Calculator Tests ===")

    print(
        calculator(
            "(12000 + 18000) * 0.9"
        )
    )

    print(
        calculator(
            "2 ** 10"
        )
    )

    print(
        calculator(
            "import os"
        )
    )

    print()

    print("=== Webpage Reader Tests ===")

    print(
        read_webpage("notice.html")[:200]
    )

    print()

    print(
        read_webpage("no_such_file.html")
    )