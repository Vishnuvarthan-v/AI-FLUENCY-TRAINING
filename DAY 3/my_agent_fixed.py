"""Day 3: the same agent, with three guards added."""

import json

from config import client, MODEL, banner
from my_agent import SYSTEM_PROMPT
from my_tools import TOOLS, TOOL_FUNCTIONS


MAX_TOOL_CHARS = 5000       # guard 2: no single observation may be larger than this
CHAR_BUDGET = 30000         # guard 3: total characters sent to the model in one run
REPEAT_THRESHOLD = 2        # guard 1: stop after 2 identical tool calls


def agent(question, max_steps=12, verbose=True):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question}
    ]

    seen_calls = {}          # guard 1: repeat detection
    chars_sent = 0

    for step in range(1, max_steps + 1):

        # Guard 3: character budget
        chars_sent += sum(
            len(str(m.get("content", "")))
            for m in messages
        )

        if chars_sent > CHAR_BUDGET:
            return (
                f"Stopped: character budget exceeded "
                f"({chars_sent} sent)."
            )

        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            temperature=0
        )

        message = response.choices[0].message

        # No tool call -> final answer
        if not message.tool_calls:
            return (message.content or "").strip()

        # Add assistant tool-call message
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": c.id,
                    "type": "function",
                    "function": {
                        "name": c.function.name,
                        "arguments": c.function.arguments
                    }
                }
                for c in message.tool_calls
            ]
        })

        # Execute each requested tool
        for call in message.tool_calls:

            name = call.function.name
            arguments = {}

            try:
                arguments = json.loads(
                    call.function.arguments or "{}"
                )

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

            result = str(result)

            # Guard 1: repeated tool-call detection
            signature = (
                name,
                json.dumps(arguments, sort_keys=True)
            )

            seen_calls[signature] = (
                seen_calls.get(signature, 0) + 1
            )

            if seen_calls[signature] >= REPEAT_THRESHOLD:
                return (
                    f"Stopped: the tool {name} was called "
                    f"{REPEAT_THRESHOLD} times with the same "
                    f"arguments and no progress was made. "
                    f"Last result: {result[:200]}"
                )

            # Guard 2: observation-size limit
            if len(result) > MAX_TOOL_CHARS:
                result = (
                    result[:MAX_TOOL_CHARS]
                    + " ... [observation truncated]"
                )

            if verbose:
                print(
                    f"   step {step}: "
                    f"{name}({arguments}) -> "
                    f"{result[:120]}"
                )

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": result
            })

    return "Stopped: maximum steps reached without a final answer."


if __name__ == "__main__":

    banner("MY AGENT (guards on)")

    for question in [
        "Read notice.html and tell me the total fee for CS101 and AI202 after the merit scholarship.",

        "Read fees.html and tell me the fee for CS101.",

        "Read big.html and tell me how many students are listed.",
    ]:
        print("\nQ:", question)
        print("A:", agent(question))