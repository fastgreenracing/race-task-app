import streamlit as st
from google.cloud import firestore
import json
from datetime import datetime
import pytz

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Race Logistics", page_icon="🏃", layout="wide")
st.title("🏃 Fast Green Racing: Live Tracker")

# --- ADMIN SETTINGS ---
ADMIN_PASSWORD = "fastgreen2026" 
TIMEZONE = "US/Pacific"

def get_now():
    return datetime.now(pytz.timezone(TIMEZONE)).strftime("%m/%d %I:%M %p")

# --- DATA FUNCTIONS ---
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    if cat_ref.exists:
        return cat_ref.to_dict().get("list", ["Transportation", "Course & Traffic", "Vendors", "Finish Line"])
    return ["Transportation", "Course & Traffic", "Vendors", "Finish Line"]

def add_task(title, category):
    db.collection("race_tasks").add({
        "title": title, 
        "category": category, 
        "completed": False,
        "history": [] 
    })

def update_task_status(doc_id, new_status):
    # Strictly isolated database reference
    doc_ref = db.collection("race_tasks").document(doc_id)
    doc_snapshot = doc_ref.get().to_dict()
    
    # Only update if there is a real change to THIS specific task
    if doc_snapshot.get("completed") != new_status:
        status_text = "✅ Task Completed" if new_status else "⏳ Task Unchecked (Admin)"
        log_entry = f"{status_text} at {get_now()}"
        
        doc_ref.update({
            "completed": new_status,
            "history": firestore.ArrayUnion([log_entry])
        })

def add_note(doc_id, note_text):
    if note_text.strip():
        log_entry = f"📝 Note: {note_text} (Added at {get_now()})"
        db.collection("race_tasks").document(doc_id).update({
            "history": firestore.ArrayUnion([log_entry])
        })

current_categories = get_categories()

# --- SIDEBAR: ACCESS CONTROL ---
with st.sidebar:
    st.header("🔐 Access Control")
    pwd = st.text_input("Admin Password", type="password")
    is_admin = (pwd == ADMIN_PASSWORD)
    st.session_state.admin_logged_in = is_admin

    if is_admin:
        st.success("Admin Mode: Active")
        st.divider()
        st.subheader("➕ Add New Task")
        new_title = st.text_input("Task Description")
        new_cat = st.selectbox("Assign to Category", current_categories)
        if st.button("Add Task", use_container_width=True):
            if new_title:
                add_task(new_title, new_cat)
                st.rerun()

# --- MAIN UI DISPLAY ---
@st.fragment(run_every=10)
def show_tasks():
    is_admin = st.session_state.admin_logged_in
    
    for cat in current_categories:
        st.subheader(f"📍 {cat}")
        tasks = db.collection("race_tasks").where("category", "==", cat).stream()
        
        has_tasks = False
        for task in tasks:
            has_tasks = True
            td = task.to_dict()
            task_id = task.id
            is_done = td.get("completed", False)
            
            # Dynamic Colors
            bg_color, border_color = ("#dcfce7", "#22c55e") if is_done else ("#fee2e2", "#ef4444")
            
            st.markdown(
                f"""<div style="background-color: {bg_color}; border: 2px solid {border_color}; 
                padding: 15px; border-radius: 10px; margin-bottom: 10px; color: black;">""", 
                unsafe_allow_html=True
            )
            
            cols = st.columns([1, 7, 2]) if is_admin else st.columns([1, 9])

            with cols[0]:
                # LOCKING LOGIC: 
                # Disable checkbox if task is done AND user is not an admin
                is_disabled = is_done and not is_admin
                
                check_val = st.checkbox(
                    "", 
                    value=is_done, 
                    key=f"check_{task_id}", 
                    label_visibility="collapsed",
                    disabled=is_disabled
                )
                
                if check_val != is_done:
                    update_task_status(task_id, check_val)
                    st.rerun()
            
            with cols[1]:
                st.markdown(f"**{'✅' if is_done else '⏳'} {td['title']}**")
                
                if is_disabled:
                    st.caption("🔒 Locked (Only Admin can uncheck)")

                if td.get("history"):
                    with st.expander("View Activity Log", expanded=True):
                        # Use set to avoid any ghost duplicates in display
                        for log in reversed(td["history"]):
                            st.caption(log)
                
                if is_admin:
                    with st.popover("Add Note"):
                        note_input = st.text_area("Observations:", key=f"note_in_{task_id}")
                        if st.button("Save Note", key=f"save_btn_{task_id}"):
                            add_note(task_id, note_input)
                            st.rerun()
            
            if is_admin:
                with cols[2]:
                    if st.button("Delete", key=f"del_{task_id}", type="secondary", use_container_width=True):
                        db.collection("race_tasks").document(task_id).delete()
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        if not has_tasks:
            st.caption(f"No active tasks in {cat}")

show_tasks()
