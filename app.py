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

def add_task(title, category, is_admin_only=False):
    # Get current max order to put new task at the bottom
    tasks = db.collection("race_tasks").where("category", "==", category).stream()
    order = len(list(tasks))
    db.collection("race_tasks").add({
        "title": title, 
        "category": category, 
        "completed": False,
        "notes": "",
        "sort_order": order,
        "admin_only": is_admin_only,
        "completed_at": None
    })

def move_task(doc_id, current_order, direction, category):
    new_order = current_order + direction
    # Find the task currently in the target spot and swap them
    target_tasks = db.collection("race_tasks").where("category", "==", category).where("sort_order", "==", new_order).limit(1).stream()
    for t in target_tasks:
        db.collection("race_tasks").document(t.id).update({"sort_order": current_order})
    db.collection("race_tasks").document(doc_id).update({"sort_order": new_order})

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
        new_cat = st.selectbox("Assign to Category", get_categories())
        admin_task_check = st.checkbox("Admin-Only Toggle (Locked for Users)")
        if st.button("Add Task", use_container_width=True):
            if new_title:
                add_task(new_title, new_cat, is_admin_only=admin_task_check)
                st.rerun()

# --- MAIN UI DISPLAY ---
@st.fragment(run_every=5)
def show_tasks():
    is_admin = st.session_state.get('admin_logged_in', False)
    categories = get_categories()
    
    for cat in categories:
        st.subheader(f"📍 {cat}")
        # Sort by the new sort_order field
        tasks = db.collection("race_tasks").where("category", "==", cat).order_by("sort_order").stream()
        
        task_list = list(tasks)
        for i, task in enumerate(task_list):
            td = task.to_dict()
            task_id = task.id
            db_status = td.get("completed", False)
            is_locked_admin = td.get("admin_only", False)
            
            # Formatting
            bg_color = "#dcfce7" if db_status else "#fee2e2"
            border_color = "#22c55e" if db_status else "#ef4444"
            
            st.markdown(
                f"""<div style="background-color: {bg_color}; border: 2px solid {border_color}; 
                padding: 15px; border-radius: 10px; margin-bottom: 10px; color: black;">""", 
                unsafe_allow_html=True
            )
            
            # Layout
            cols = st.columns([1, 0.5, 6, 2.5]) if is_admin else st.columns([1, 9])

            with cols[0]:
                # USER LOCK: Disabled if (done AND user) OR (Admin Task AND user)
                user_is_locked = (db_status and not is_admin) or (is_locked_admin and not is_admin)
                
                check_val = st.checkbox("", value=db_status, key=f"w_{task_id}_{db_status}", 
                                        disabled=user_is_locked, label_visibility="collapsed")
                
                if check_val != db_status:
                    ts = get_now() if check_val else None
                    db.collection("race_tasks").document(task_id).update({
                        "completed": check_val,
                        "completed_at": ts
                    })
                    st.rerun()
            
            if is_admin:
                with cols[1]:
                    # Move Arrows
                    if i > 0:
                        if st.button("▲", key=f"up_{task_id}"):
                            move_task(task_id, td['sort_order'], -1, cat)
                            st.rerun()
                    if i < len(task_list) - 1:
                        if st.button("▼", key=f"down_{task_id}"):
                            move_task(task_id, td['sort_order'], 1, cat)
                            st.rerun()

            with cols[2 if is_admin else 1]:
                admin_label = " [ADMIN CONTROL]" if is_locked_admin else ""
                st.markdown(f"**{'✅' if db_status else '⏳'} {td['title']}{admin_label}**")
                
                if td.get("completed_at"):
                    st.caption(f"🕒 Completed: {td['completed_at']}")
                
                if td.get("notes"):
                    st.info(f"📝 {td['notes']}")
            
            if is_admin:
                with cols[3]:
                    c1, c2 = st.columns(2)
                    with c1:
                        with st.popover("Note"):
                            n = st.text_area("Edit:", value=td.get("notes", ""), key=f"n_{task_id}")
                            if st.button("Save", key=f"sb_{task_id}"):
                                db.collection("race_tasks").document(task_id).update({"notes": n})
                                st.rerun()
                    with c2:
                        if st.button("🗑️", key=f"del_{task_id}"):
                            db.collection("race_tasks").document(task_id).delete()
                            st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

show_tasks()
