import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Race Logistics", page_icon="🏃", layout="wide")
st.title("🏃 Fast Green Racing: Live Tracker")

# --- ADMIN SETTINGS ---
ADMIN_PASSWORD = "fastgreen2026" 

# --- 2. DATA FUNCTIONS ---
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    if cat_ref.exists:
        return cat_ref.to_dict().get("list", ["Transportation", "Course & Traffic", "Vendors", "Finish Line"])
    return ["Transportation", "Course & Traffic", "Vendors", "Finish Line"]

def add_task(title, category):
    existing_tasks = db.collection("race_tasks").where("category", "==", category).get()
    new_order = len(existing_tasks)
    
    db.collection("race_tasks").add({
        "title": title, 
        "category": category, 
        "completed": False,
        "notes": "",
        "sort_order": new_order
    })

def update_task_status(doc_id, new_status):
    db.collection("race_tasks").document(doc_id).update({"completed": new_status})

def update_note(doc_id, note_text):
    db.collection("race_tasks").document(doc_id).update({"notes": note_text})

def move_task(task_id, category, current_order, direction):
    target_order = current_order + direction
    query = db.collection("race_tasks").where("category", "==", category).where("sort_order", "==", target_order).limit(1).get()
    
    if query:
        target_doc = query[0]
        db.collection("race_tasks").document(task_id).update({"sort_order": target_order})
        db.collection("race_tasks").document(target_doc.id).update({"sort_order": current_order})

# --- 3. SIDEBAR: ACCESS CONTROL ---
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
        if st.button("Add Task", use_container_width=True):
            if new_title:
                add_task(new_title, new_cat)
                st.rerun()

# --- 4. MAIN UI DISPLAY ---
@st.fragment(run_every=5)
def show_tasks():
    is_admin = st.session_state.get('admin_logged_in', False)
    categories = get_categories()
    
    for cat in categories:
        # CATEGORY DIVIDER & HEADER
        st.markdown("<hr style='border: 2px solid #333; margin-top: 40px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.markdown(f"<h1 style='font-size: 36px; margin-bottom: 20px;'>📍 {cat}</h1>", unsafe_allow_html=True)
        
        try:
            tasks_query = db.collection("race_tasks").where("category", "==", cat).order_by("sort_order").stream()
            tasks_list = list(tasks_query)
        except Exception:
            st.warning("Database is indexing. Please check logs for the Index Link if this persists.")
            tasks_list = []
        
        has_tasks = len(tasks_list) > 0
        
        for index, task in enumerate(tasks_list):
            td = task.to_dict()
            task_id = task.id
            db_status = td.get("completed", False)
            current_order = td.get("sort_order", index)
            
            unique_key = f"widget_{task_id}_{db_status}_{is_admin}"
            bg_color = "#dcfce7" if db_status else "#fee2e2"
            border_color = "#22c55e" if db_status else "#ef4444"
            
            st.markdown(
                f"""<div style="background-color: {bg_color}; border: 2px solid {border_color}; 
                padding: 20px; border-radius: 12px; margin-bottom: 5px; color: black;">""", 
                unsafe_allow_html=True
            )
            
            if is_admin:
                cols = st.columns([0.6, 0.8, 6.6, 2]) 
            else:
                cols = st.columns([1, 9])

            with cols[0]:
                is_disabled = db_status and not is_admin
                check_val = st.checkbox("", value=db_status, key=unique_key, disabled=is_disabled, label_visibility="collapsed")
                if check_val != db_status:
                    update_task_status(task_id, check_val)
                    st.rerun()
            
            if is_admin:
                with cols[1]:
                    up_c, down_c = st.columns(2)
                    if index > 0:
                        if up_c.button("▲", key=f"up_{task_id}"):
                            move_task(task_id, cat, current_order, -1)
                            st.rerun()
                    if index < len(tasks_list) - 1:
                        if down_c.button("▼", key=f"down_{task_id}"):
                            move_task(task_id, cat, current_order, 1)
                            st.rerun()

            text_col = cols[2] if is_admin else cols[1]
            with text_col:
                icon = '✅' if db_status else '⏳'
                st.markdown(f"<span style='font-size: 24px; font-weight: bold;'>{icon} {td['title']}</span>", unsafe_allow_html=True)
                
                if td.get("notes"):
                    st.info(f"📝 {td['notes']}")
                
                if is_admin:
                    with st.popover("Edit Notes"):
                        new_note = st.text_area("Notes:", value=td.get("notes", ""), key=f"note_{task_id}")
                        if st.button("Save", key=f"btn_note_{task_id}"):
                            update_note(task_id, new_note)
                            st.rerun()
            
            if is_admin:
                with cols[3]:
                    if st.button("Delete", key=f"del_{task_id}", type="secondary", use_container_width=True):
                        db.collection("race_tasks").document(task_id).delete()
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # TASK DIVIDER: A lesser defining line between tasks
            if index < len(tasks_list) - 1:
                st.markdown("<hr style='border: 0.5px dashed #bbb; margin-top: 10px; margin-bottom: 10px; width: 90%; margin-left: auto; margin-right: auto;'>", unsafe_allow_html=True)
        
        if not has_tasks:
            st.caption(f"No active tasks in {cat}")

show_tasks()
