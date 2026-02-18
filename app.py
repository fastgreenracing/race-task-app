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
        "completed_at": None,
        "history": [] # Stores a log of changes
    })

def update_task_status(doc_id, status):
    update_data = {"completed": status}
    if status:
        # Only set timestamp if it hasn't been set before to prevent "shifting"
        update_data["completed_at"] = get_now()
    
    log_entry = f"{'✅ Task Completed' if status else '⏳ Task Unchecked'} at {get_now()}"
    db.collection("race_tasks").document(doc_id).update({
        **update_data,
        "history": firestore.ArrayUnion([log_entry])
    })

def add_note(doc_id, note_text):
    if note_text.strip():
        log_entry = f"📝 Note: {note_text} (Added at {get_now()})"
        db.collection("race_tasks").document(doc_id).update({
            "history": firestore.ArrayUnion([log_entry])
        })

current_categories = get_categories()

# --- SIDEBAR LOGIC ---
with st.sidebar:
    st.header("🔐 Access Control")
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False

    pwd = st.text_input("Admin Password", type="password")
    st.session_state.admin_logged_in = (pwd == ADMIN_PASSWORD)

    if st.session_state.admin_logged_in:
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
            is_done = td.get("completed", False)
            
            # Stable Color Logic
            bg_color, border_color = ("#dcfce7", "#22c55e") if is_done else ("#fee2e2", "#ef4444")
            
            st.markdown(
                f"""<div style="background-color: {bg_color}; border: 2px solid {border_color}; 
                padding: 15px; border-radius: 10px; margin-bottom: 10px; color: black;">""", 
                unsafe_allow_html=True
            )
            
            cols = st.columns([1, 7, 2]) if is_admin else st.columns([1, 9])

            with cols[0]:
                check = st.checkbox("", value=is_done, key=f"check_{task.id}", label_visibility="collapsed")
                if check != is_done:
                    update_task_status(task.id, check)
                    st.rerun()
            
            with cols[1]:
                st.markdown(f"**{'✅' if is_done else '⏳'} {td['title']}**")
                
                # Show Task History (Visible to everyone)
                if td.get("history"):
                    with st.expander("View Activity Log"):
                        for log in reversed(td["history"]):
                            st.caption(log)
                
                # Admin Notes
                if is_admin:
                    with st.popover("Add Note"):
                        note_text = st.text_area("Note content:", key=f"input_{task.id}")
                        if st.button("Save Note", key=f"btn_{task.id}"):
                            add_note(task.id, note_text)
                            st.rerun()
            
            if is_admin:
                with cols[2]:
                    if st.button("Delete", key=f"del_{task.id}", type="secondary", use_container_width=True):
                        db.collection("race_tasks").document(task.id).delete()
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        if not has_tasks:
            st.caption(f"No active tasks in {cat}")

show_tasks()
