import streamlit as st
import pandas as pd
from agent import run_agent, task_account_brief, task_first_outreach, task_followup_plan, task_web_lead_search
from storage import load_leads, save_leads, create_lead, update_lead, add_note, delete_lead

st.set_page_config(page_title="OVRSEA Leads", layout="wide")
st.title("OVRSEA — Leads")

leads = load_leads()

# ----------------------------
# Session state (router + selection)
# ----------------------------
if "page" not in st.session_state:
    st.session_state.page = "Overview"

if "selected_lead_id" not in st.session_state:
    st.session_state.selected_lead_id = None

# Top navigation (acts like tabs, but we CAN redirect programmatically)
nav = st.radio(
    "Navigation",
    ["Overview", "Lead Detail", "Add Lead"],
    horizontal=True,
    index=["Overview", "Lead Detail", "Add Lead"].index(st.session_state.page),
)

# Keep session_state.page aligned if user clicks nav manually
st.session_state.page = nav


# ----------------------------
# Helpers
# ----------------------------
def find_lead_by_id(lead_id: str):
    return next((l for l in leads if l["id"] == lead_id), None)


def leads_to_table(ls):
    df = pd.DataFrame(ls)
    if len(df) == 0:
        return df
    # Make products readable in table
    df = df.copy()
    df["products"] = df["products"].apply(lambda x: ", ".join(x) if isinstance(x, list) else "")
    return df


# ============================
# PAGE: OVERVIEW
# ============================
if st.session_state.page == "Overview":
    st.subheader("All leads")

    q = st.text_input("Search leads", placeholder="name / HQ / industry / product")

    def matches(l):
        if not q.strip():
            return True
        hay = " ".join([
            l.get("name", ""),
            l.get("hq", ""),
            l.get("industry", ""),
            " ".join(l.get("products", []) or [])
        ]).lower()
        return q.lower() in hay

    filtered = [l for l in leads if matches(l)]

    if len(filtered) == 0:
        st.warning("No leads match your search.")
        st.stop()

    # Render "clickable rows" as full-width buttons (no checkbox UI)
    for l in filtered:
        label = f"**{l['name']}**  \n" \
                f"{l.get('industry','-')} • {l.get('hq','-')} • Founded: {l.get('founded') or '-'}"
        if st.button(label, key=f"open_{l['id']}", use_container_width=True):
            st.session_state.selected_lead_id = l["id"]
            st.session_state.page = "Lead Detail"
            st.rerun()



# ============================
# PAGE: LEAD DETAIL
# ============================
elif st.session_state.page == "Lead Detail":
    st.subheader("Lead Detail")

    if len(leads) == 0:
        st.info("No leads yet. Add one in 'Add Lead'.")
        st.stop()

    # Default selection
    if not st.session_state.selected_lead_id:
        st.session_state.selected_lead_id = leads[0]["id"]

    # Dropdown selection (still useful even with row-click)
    options = {f"{l['name']} • {l.get('hq','-')}": l["id"] for l in leads}
    current_label = next((k for k, v in options.items() if v == st.session_state.selected_lead_id), None)
    if current_label is None:
        current_label = list(options.keys())[0]

    selected_label = st.selectbox(
        "Select a lead",
        options=list(options.keys()),
        index=list(options.keys()).index(current_label),
    )
    st.session_state.selected_lead_id = options[selected_label]

    selected = find_lead_by_id(st.session_state.selected_lead_id)
        # If the selected lead was deleted or not found, go back to Overview
    if st.session_state.selected_lead_id is not None and not selected:
        st.session_state.selected_lead_id = None
        st.session_state.page = "Overview"
        st.rerun()



    # Header
    st.markdown(f"## {selected['name']}")
    st.write("**Website:**", selected.get("website") or "-")
    st.write("**Products:**", ", ".join(selected.get("products") or []) or "-")
    st.write("**HQ:**", selected.get("hq") or [] or "-")
    st.write("**Industry:**", selected.get("industry") or [] or "-")
    st.write("**Founded:**",str(selected.get("founded") or "-"))
    st.write("**Employees:**", str(selected.get("employees") or "-"))


    # cols = st.columns(4)
    # cols[0].metric("HQ", selected.get("hq") or "-")
    # cols[1].metric("Industry", selected.get("industry") or "-")
    # cols[2].metric("Founded", str(selected.get("founded") or "-"))
    # cols[3].metric("Employees", str(selected.get("employees") or "-"))

    st.divider()
    st.markdown("### Edit lead")

    # ---- EDIT FORM (ISOLATED & SAFE) ----
    edit_form = st.form("edit_lead_form")

    e_name = edit_form.text_input("Company name", value=selected.get("name", ""))
    e_website = edit_form.text_input("Website", value=selected.get("website", ""))
    e_hq = edit_form.text_input("HQ", value=selected.get("hq", ""))
    e_industry = edit_form.text_input("Industry", value=selected.get("industry", ""))

    c1, c2 = edit_form.columns(2)
    with c1:
        e_founded = edit_form.text_input(
            "Founded (year)",
            value="" if selected.get("founded") is None else str(selected.get("founded"))
        )
    with c2:
        e_employees = edit_form.text_input(
            "Employees",
            value="" if selected.get("employees") is None else str(selected.get("employees"))
        )

    e_products = edit_form.text_input(
        "Products (comma-separated)",
        value=", ".join(selected.get("products") or [])
    )

    save_btn = edit_form.form_submit_button("Save changes")

    if save_btn:
        patch = {
            "name": e_name.strip(),
            "website": e_website.strip(),
            "hq": e_hq.strip(),
            "industry": e_industry.strip(),
            "founded": int(e_founded) if e_founded.strip().isdigit() else None,
            "employees": int(e_employees) if e_employees.strip().isdigit() else None,
            "products": [p.strip() for p in e_products.split(",") if p.strip()]
        }

        update_lead(leads, selected["id"], patch)
        save_leads(leads)
        st.success("Lead updated successfully.")
        st.rerun()

    st.divider()
    st.markdown("### Delete Lead")

    confirm = st.checkbox(
        "I understand this will permanently delete the lead.",
        key=f"confirm_delete_{selected['id']}"
    )

    
    if st.button("Delete lead", type="secondary", disabled=not confirm):
        delete_lead(leads, selected["id"])
        save_leads(leads)

        # Reset selection + redirect back to Overview
        st.session_state.selected_lead_id = None
        st.session_state.page = "Overview"
        st.success("Lead deleted.")
        st.rerun()

    
    st.divider()
    st.markdown("### Notes")

    notes = selected.get("notes") or []
    if not notes:
        st.info("No notes yet. Add one above.")
    else:
        # Show newest first (your add_note already inserts at 0, but we keep safe)
        for n in notes[:30]:
            ts = n.get("at", "")
            text = n.get("text", "")
            with st.container(border=True):
                st.caption(ts.replace("T", " ").replace("Z", " UTC"))
                st.markdown(text)

    st.divider()

    st.markdown("### Add Note")
    note = st.text_area("New note", placeholder="Add context: pain points, lanes, contact attempts, news…")
    if st.button("Add note", type="primary"):
        if note.strip():
            add_note(leads, selected["id"], note)
            save_leads(leads)
            st.success("Note added.")
            st.rerun()
        else:
            st.warning("Write a note first.")

    st.divider()

    st.markdown("### Add info (Key/Value enrichment)")
    key = st.text_input("Field name", placeholder="e.g. Contact Email")
    val = st.text_input("Value", placeholder="e.g. info@gmail.com")
    if st.button("Save field"):
        if key.strip():
            extra = dict(selected.get("extra") or {})
            extra[key.strip()] = val.strip()
            updated = update_lead(leads, selected["id"], {"extra": extra})
            save_leads(leads)
            st.success("Saved.")
            st.rerun()
        else:
            st.warning("Field name required.")

    st.divider()

    st.markdown("### Saved info")
    st.write("**Extra fields**")
    st.json(selected.get("extra") or {})

# ============================
# PAGE: ADD LEAD
# ============================
else:
    st.subheader("Create a new lead")

    with st.form("create_lead_form"):
        name = st.text_input("Company name *")
        website = st.text_input("Website *")
        hq = st.text_input("HQ")
        industry = st.text_input("Industry")
        founded = st.text_input("Founded (year)")
        employees = st.text_input("Employees")
        products = st.text_input("Products (comma-separated)")

        submitted = st.form_submit_button("Create", type="primary")

        if submitted:
            if not name.strip() or not website.strip():
                st.error("Company name and website are required.")
            else:
                new = create_lead(leads, {
                    "name": name,
                    "website": website,
                    "hq": hq,
                    "industry": industry,
                    "founded": int(founded) if founded.strip().isdigit() else None,
                    "employees": int(employees) if employees.strip().isdigit() else None,
                    "products": [p.strip() for p in products.split(",") if p.strip()]
                })
                save_leads(leads)
                st.session_state.selected_lead_id = new["id"]
                st.session_state.page = "Lead Detail"
                st.success(f"Created lead: {new['name']}")
                st.rerun()

st.divider()
st.markdown("### Agent actions")

a1, a2, a3, a4 = st.columns(4)

if a1.button("Generate account brief"):
    text, _ = run_agent(leads, selected, task_account_brief(selected))
    save_leads(leads)
    st.success("Done.")
    st.write(text)

if a2.button("Draft first outreach"):
    text, _ = run_agent(leads, selected, task_first_outreach(selected))
    save_leads(leads)
    st.success("Done.")
    st.write(text)

if a3.button("Create follow-up plan"):
    text, _ = run_agent(leads, selected, task_followup_plan(selected))
    save_leads(leads)
    st.success("Done.")
    st.write(text)

if a4.button("Search the Web for the lead"):
    text, _ = run_agent(leads, selected, task_web_lead_search(selected))
    save_leads(leads)
    st.success("Done.")
    st.write(text)