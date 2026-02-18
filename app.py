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

# --- ADMIN PASSWORD ---
ADMIN_PASSWORD = "fastgreen2026" 
TIMEZONE = "US/Pacific" # Adjusted for Ventura/Ojai logistics

# --- DATA FUNCTIONS ---
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    if cat_ref.exists:
        return cat_ref.to_dict().get("list", ["Transportation", "Course & Traffic", "Vendors", "Finish Line"])
    return ["Transportation", "Course & Traffic", "Vendors", "Finish Line"]

def update_categories(new_list):
    db.collection("settings").document("categories").set({"list": new_list})

def add_task(title, category):
    db.collection("race_tasks").add({
        "title": title, 
        "category": category, 
        "completed": False,
        "completed_at": None
    })

def delete_task(doc_id):
    db.collection("race_tasks").document(doc_id).delete()

current_categories = get_categories()

# --- SIDEBAR LOGIC ---
with st.sidebar:
    st.header("🔐 Access Control")
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False

    pwd = st.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        st.session_state.admin_logged_in = True
        st.success("Admin Mode: Active")
    else:
        st.session_state.admin_logged_in = False

    if st.session_state.admin_logged_in:
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
            
            # --- COLOR LOGIC ---
            if td["completed"]:
                bg_color = "#dcfce7" # Light Green
                border_color = "#22c55e"
                text_color = "#166534"
            else:
                bg_color = "#fee2e2" # Light Red/Pink
                border_color = "#ef4444"
                text_color = "#991b1b"
            
            st.markdown(
                f"""
                <div style="background-color: {bg_color}; border: 2px solid {border_color}; 
                            padding: 15px; border-radius: 10px; margin-bottom: 10px; color: {text_color};">
                """, 
                unsafe_allow_html=True
            )
            
            cols = st.columns([1, 6, 2]) if is_admin else st.columns([1, 8])

            with cols[0]:
                is_done = st.checkbox("", value=td["completed"], key=f"check_{task.id}", label_visibility="collapsed")
                if is_done != td.get("completed"):
                    # Record timestamp on completion
                    ts = datetime.now(pytz.timezone(TIMEZONE)).strftime("%m/%d %I:%M %p") if is_done else None
                    db.collection("race_tasks").document(task.id).update({
                        "completed": is_done,
                        "completed_at": ts
                    })
                    st.rerun()
            
            with cols[1]:
                status_icon = "✅" if td["completed"] else "⏳"
                st.markdown(f"**{status_icon} {td['title']}**")
                if td.get("completed_at"):
                    st.caption(f"Finished: {td['completed_at']}")
            
            if is_admin:
                with cols[2]:
                    if st.button("Delete", key=f"del_{task.id}", type="secondary", use_container_width=True):
                        delete_task(task.id)
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        if not has_tasks:
            st.caption(f"No active tasks in {cat}")

show_tasks()
