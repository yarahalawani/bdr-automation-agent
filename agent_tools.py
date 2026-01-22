from typing import Any, Dict, List
from storage import update_lead, add_note

# Tool schemas (JSON schema) for tool calling. 
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "add_lead_note",
            "description": "Add a note to a lead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "string"},
                    "text": {"type": "string"}
                },
                "required": ["lead_id", "text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_lead_fields",
            "description": "Update basic fields on a lead (status/contact/next follow-up).",
            "parameters": {
                "type": "object",
                "properties": {
                    "lead_id": {"type": "string"},
                    "patch": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "contact_name": {"type": "string"},
                            "contact_email": {"type": "string"},
                            "next_followup": {"type": "string"}
                        }
                    }
                },
                "required": ["lead_id", "patch"]
            }
        }
    }
]

def tool_add_lead_note(leads: List[Dict[str, Any]], lead_id: str, text: str) -> Dict[str, Any]:
    return add_note(leads, lead_id, text)

def tool_update_lead_fields(leads: List[Dict[str, Any]], lead_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    return update_lead(leads, lead_id, patch)

TOOL_IMPL = {
    "add_lead_note": tool_add_lead_note,
    "update_lead_fields": tool_update_lead_fields,
}
