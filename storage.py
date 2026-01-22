from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "leads.json")


def _read_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: str, data: List[Dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_leads() -> List[Dict[str, Any]]:
    if not os.path.exists(DATA_PATH):
        _write_json(DATA_PATH, [])
    return _read_json(DATA_PATH)


def save_leads(leads: List[Dict[str, Any]]) -> None:
    _write_json(DATA_PATH, leads)


def slugify(name: str) -> str:
    import re
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"(^-|-$)+", "", s)
    return s or "lead"


def create_lead(leads: List[Dict[str, Any]], lead: Dict[str, Any]) -> Dict[str, Any]:
    base = slugify(lead["name"])
    new_id = base
    i = 2
    existing = {l["id"] for l in leads}
    while new_id in existing:
        new_id = f"{base}-{i}"
        i += 1

    new_lead = {
        "id": new_id,
        "name": lead.get("name", "").strip(),
        "website": lead.get("website", "").strip(),
        "hq": lead.get("hq", "").strip(),
        "industry": lead.get("industry", "").strip(),
        "founded": lead.get("founded", None),
        "employees": lead.get("employees", None),
        "products": lead.get("products", []),
        "notes": [],
        "extra": {}
        }
    leads.insert(0, new_lead)
    return new_lead


def update_lead(leads: List[Dict[str, Any]], lead_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    idx = next((i for i, l in enumerate(leads) if l["id"] == lead_id), None)
    if idx is None:
        raise KeyError("Lead not found")

    allowed = {"name", "website", "hq", "industry", "founded", "employees", "products", "extra", "notes"}
    for k, v in patch.items():
        if k in allowed:
            leads[idx][k] = v
    return leads[idx]

def delete_lead(leads, lead_id: str) -> None:
    idx = next((i for i, l in enumerate(leads) if l["id"] == lead_id), None)
    if idx is None:
        raise KeyError("Lead not found")
    leads.pop(idx)



def add_note(leads: List[Dict[str, Any]], lead_id: str, text: str) -> Dict[str, Any]:
    import datetime as dt
    idx = next((i for i, l in enumerate(leads) if l["id"] == lead_id), None)
    if idx is None:
        raise KeyError("Lead not found")
    note = {"at": dt.datetime.utcnow().isoformat() + "Z", "text": text.strip()}
    leads[idx].setdefault("notes", [])
    leads[idx]["notes"].insert(0, note)
    return leads[idx]
