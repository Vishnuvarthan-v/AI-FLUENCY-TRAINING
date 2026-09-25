"""Day 3: Failure 2 - Hallucinated tool call"""

import json

from config import client, MODEL, banner
from my_tools import TOOLS, TOOL_FUNCTIONS


# ============================================================
# TEMPORARY send_email TOOL
# ============================================================
# We tell the model that send_email exists,
# BUT we do NOT add it to TOOL_FUNCTIONS.
#
# This is intentional for the Failure 2 experiment.
# ============================================================

TOOLS = TOOLS + [
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Send an email to a recipient. "
                "Use this to inform the accounts department."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Email address of the recipient."
                    },
                    "body": {
                        "type": "string",
                        "description": "Content of the email."
                    }
                },
                "required": ["to", "body"]
            }
        }
    }
]


# ============================================================
# SYSTEM PROMPT
# ============================================================

SYSTEM_PROMPT = (
    "You are a college assistant. "
    "Use read_webpage to read any page or file the user mentions, "
    "and use calculator for every arithmetic step. "
    "Never guess a number that should come from a page. "
    "If no tool is needed, answer directly. "
    "If the fee is above 25000, use send_email to inform the "
    "accounts department."
)


# ============================================================
# AGENT
# ============================================================

def agent(question, max_steps=6, verbose=True):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": question
        }
    ]

    for step in range(1, max_steps + 1):

        # ----------------------------------------------------
        # 1. REASON
        # ----------------------------------------------------

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0
        )

        message = response.choices[0].message

        # ----------------------------------------------------
        # 2. STOP if no tool is requested
        # ----------------------------------------------------

        if not message.tool_calls:
            return (message.content or "").strip()

        # ----------------------------------------------------
        # 3. RECORD the model's tool request
        # ----------------------------------------------------

        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments
                    }
                }
                for call in message.tool_calls
            ]
        })

        # ----------------------------------------------------
        # 4. ACT and 5. OBSERVE
        # ----------------------------------------------------

        for call in message.tool_calls:

            name = call.function.name
            arguments = {}

            try:

                # Convert JSON arguments into a Python dictionary
                arguments = json.loads(
                    call.function.arguments or "{}"
                )

                # =================================================
                # SAFE REGISTRY LOOKUP
                # =================================================
                # IMPORTANT:
                # Use .get() so an unknown tool does NOT crash.
                # =================================================

                function = TOOL_FUNCTIONS.get(name)

                if function is None:

                    result = (
                        f"Unknown tool: {name}. "
                        f"Available: {list(TOOL_FUNCTIONS)}"
                    )

                else:

                    result = function(**arguments)

            except json.JSONDecodeError as error:

                result = (
                    f"Argument error: {error}. "
                    "Send valid JSON."
                )

            except TypeError as error:

                result = f"Argument error: {error}"

            # ----------------------------------------------------
            # Show the tool execution
            # ----------------------------------------------------

            if verbose:

                print(
                    f"   step {step}: "
                    f"{name}({arguments}) -> "
                    f"{str(result)[:200]}"
                )

            # ----------------------------------------------------
            # Send tool result back to the model
            # ----------------------------------------------------

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result)
            })

    # --------------------------------------------------------
    # SAFETY EXIT
    # --------------------------------------------------------

    return "Stopped: maximum steps reached without a final answer."


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    banner("MY AGENT - CONTEXT OVERFLOW")

    question = "Read big.html and tell me how many students are listed."

    print("Q:", question)
    print("A:", agent(question))