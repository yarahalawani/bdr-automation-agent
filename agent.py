import json
from typing import Any, Dict, List, Tuple

from llm import get_client, get_model
from agent_tools import TOOLS, TOOL_IMPL

SYSTEM = """You are a BDR copilot for OVRSEA.
Goal: help the rep qualify the lead and create actionable next steps.

Rules:
- Prefer concise, actionable outputs.
- Use tools to write notes and update lead fields when useful.
- If details are missing, make reasonable assumptions but write them as notes ("assumption: ...").
"""

def run_agent(
    leads: List[Dict[str, Any]],
    lead: Dict[str, Any],
    user_task: str
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Returns (final_text, updated_leads)
    """
    client = get_client()
    model = get_model()

    messages = [
        {"role": "system", "content": SYSTEM},
        {
            "role": "user",
            "content": f"""Lead context (JSON):
{json.dumps(lead, indent=2)}

Task:
{user_task}
"""
        }
    ]

    # Tool-calling loop
    for _ in range(6):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )

        msg = resp.choices[0].message
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": getattr(msg, "tool_calls", None)})

        tool_calls = getattr(msg, "tool_calls", None)
        if not tool_calls:
            return (msg.content or "", leads)

        # Execute each tool call
        for tc in tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments or "{}")

            if name not in TOOL_IMPL:
                tool_result = {"error": f"Unknown tool: {name}"}
            else:
                tool_result = TOOL_IMPL[name](leads, **args)

            # Return tool output back to the model
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "name": name,
                    "content": json.dumps(tool_result, ensure_ascii=False),
                }
            )

    return ("Reached tool-call limit; partial result.", leads)


# ---- BDR Tasks----
def task_account_brief(lead: Dict[str, Any]) -> str:
    return (
        "Create an account brief for this lead: ICP fit, likely shipping needs, "
        "key hypotheses, 5 discovery questions, and a 3-step next action plan. "
        "Also add a concise note and set next_followup to a reasonable date."
    )

def task_first_outreach(lead: Dict[str, Any]) -> str:
    return (
        "Draft a first outreach email to the lead (short, friendly, B2B). "
        "Include: personalization using lead info, a clear value prop, and a CTA. "
        "Add a note summarizing the messaging angle and set status to Contacted."
    )

def task_followup_plan(lead: Dict[str, Any]) -> str:
    return (
        "Create a follow-up plan: 3 touchpoints over 10 days (email/LinkedIn/call). "
        "Add a note with the plan and set next_followup."
    )

def task_web_lead_search(lead: Dict[str, Any]) -> str :
    return (

    )
