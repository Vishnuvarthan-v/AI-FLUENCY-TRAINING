
"""Step 5: Agentic RAG Helpdesk in LangGraph
Tools + loop + memory + exam eligibility.
"""

import ast
import operator

from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from lc_config import get_model, get_vectorstore


# --------------------------------------------------
# 1. COURSE FEE DATA
# --------------------------------------------------

COURSE_FEES = {
    "CS101": 12000,
    "AI202": 18000,
    "DS303": 15000
}

store = get_vectorstore()


# --------------------------------------------------
# 2. SEARCH COLLEGE HANDBOOK
# --------------------------------------------------

@tool
def search_handbook(query: str) -> str:
    """Search the college handbook for fees, hostel, exams,
    library, AI training, and college policies."""
    
    docs = store.similarity_search(query, k=3)

    if not docs:
        return "No matching information found in the handbook."

    return "\n\n".join(
        f"[{d.metadata.get('source', 'Unknown source')}] {d.page_content}"
        for d in docs
    )


# --------------------------------------------------
# 3. GET COURSE FEE
# --------------------------------------------------

@tool
def get_course_fee(course_code: str) -> str:
    """Return the fee in rupees for CS101, AI202, or DS303."""

    code = course_code.strip().upper()
    fee = COURSE_FEES.get(code)

    if fee is not None:
        return f"{code} fee is Rs. {fee}"

    return f"Unknown course code: {course_code}"


# --------------------------------------------------
# 4. CHECK EXAM ELIGIBILITY (NEW TOOL - PART B)
# --------------------------------------------------

@tool
def check_exam_eligibility(attendance_percent: float) -> str:
    """Check whether a student with attendance from 0 to 100
    may write the end-semester exam.

    Rules:
    75% or above: Eligible.
    65% to below 75%: Condonation of Rs. 500 per course.
    Below 65%: Not eligible.
    Values outside 0-100: Return an error message.
    """

    # TODO 1: Validate attendance
    if not 0 <= attendance_percent <= 100:
        return (
            "ERROR: Attendance must be between 0 and 100 percent."
        )

    # TODO 2: Attendance is 75% or above
    if attendance_percent >= 75:
        return (
            f"ELIGIBLE: Attendance is {attendance_percent}%. "
            "The student may write the end-semester exam."
        )

    # TODO 3: Attendance is 65% to below 75%
    elif attendance_percent >= 65:
        return (
            f"CONDONATION: Attendance is {attendance_percent}%. "
            "The student requires condonation. "
            "Fee: Rs. 500 per course."
        )

    # TODO 4: Attendance is below 65%
    else:
        return (
            f"NOT ELIGIBLE: Attendance is {attendance_percent}%. "
            "The student does not meet the minimum attendance "
            "requirement for the end-semester exam."
        )


# --------------------------------------------------
# 5. CALCULATOR TOOL
# --------------------------------------------------

OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv
}


@tool
def calculator(expression: str) -> str:
    """Evaluate simple arithmetic using +, -, *, and /.
    Example: '18000 + 15000' or '100 * 12'.
    """

    def ev(node):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, (int, float))
            and not isinstance(node.value, bool)
        ):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](
                ev(node.left),
                ev(node.right)
            )

        raise ValueError("Only +, -, *, and / on numbers are allowed.")

    try:
        expression_tree = ast.parse(expression, mode="eval").body
        return str(ev(expression_tree))

    except Exception as e:
        return f"Error: {e}"


# --------------------------------------------------
# 6. REGISTER ALL TOOLS
# --------------------------------------------------

tools = [
    search_handbook,
    get_course_fee,
    check_exam_eligibility,  # NEW TOOL ADDED
    calculator
]


# --------------------------------------------------
# 7. MODEL AND SYSTEM PROMPT
# --------------------------------------------------

model = get_model().bind_tools(tools)

SYSTEM = """
You are the Greenfield College Helpdesk assistant.

Follow these rules:

1. For college rules, policies, late fees, hostel rules,
   library rules, and exam regulations, use search_handbook.

2. For course fees, use get_course_fee.
   Valid course codes are CS101, AI202, and DS303.

3. For student exam eligibility based on attendance percentage,
   use check_exam_eligibility.
   Never guess the eligibility result yourself.

4. For arithmetic calculations, use calculator.
   Do not calculate manually when the calculator tool is needed.

5. Answer briefly and clearly.

6. When answering handbook questions, name the source file
   returned by search_handbook.

7. If the tools do not provide the required information,
   say that you do not know. Do not invent college policies.

8. If the user asks a follow-up question, use the conversation
   history to understand what they mean.

9. If a tool returns an error, explain it clearly to the user.
"""


# --------------------------------------------------
# 8. LANGGRAPH AGENT NODE
# --------------------------------------------------

def agent(state: MessagesState):
    """Read conversation history and answer or request a tool."""

    reply = model.invoke(
        [("system", SYSTEM)] + state["messages"]
    )

    return {"messages": [reply]}


# --------------------------------------------------
# 9. BUILD LANGGRAPH
# --------------------------------------------------

builder = StateGraph(MessagesState)

builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(tools))

builder.add_edge(START, "agent")

# If the model requests a tool, route to tools.
# Otherwise, finish the conversation.
builder.add_conditional_edges(
    "agent",
    tools_condition
)

# Return to the agent after executing tools.
builder.add_edge("tools", "agent")

# Save conversation history separately for each thread.
graph = builder.compile(
    checkpointer=InMemorySaver()
)


# --------------------------------------------------
# 10. ASK FUNCTION
# --------------------------------------------------

def ask(question, thread_id):
    """Ask a question while preserving memory for its thread."""

    config = {
        "configurable": {
            "thread_id": thread_id
        },
        "recursion_limit": 10
    }

    print(f"\n[{thread_id}] USER: {question}")

    for step in graph.stream(
        {"messages": [("user", question)]},
        config,
        stream_mode="updates"
    ):
        for node, update in step.items():
            for msg in update.get("messages", []):

                # Show requested tool calls
                if getattr(msg, "tool_calls", None):
                    for call in msg.tool_calls:
                        print(
                            f"   {node:6} -> call "
                            f"{call['name']}({call['args']})"
                        )

                # Show tool results
                elif node == "tools":
                    print(
                        f"   {node:6} -> {msg.name} returned "
                        f"{str(msg.content)[:100]!r}"
                    )

                # Show final answer
                else:
                    print(
                        f"   {node:6} -> ANSWER: {msg.content}"
                    )



# --------------------------------------------------
# 11. MAIN PROGRAM: FIVE QUESTIONS IN ONE THREAD
# --------------------------------------------------

if __name__ == "__main__":

    questions = [
        "How much is the late fee for paying fees after the due date?",
        "What time should hostel students return?",
        "Can I write the exam with 70% attendance?",
        "What CGPA do I need to be eligible for placements?",
        "What is the capital of France?"
    ]

    for question in questions:
        ask(question, "task-run")

