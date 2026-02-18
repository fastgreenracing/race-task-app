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

# --- 2. DATA FUNCTIONS (Defined first to prevent errors) ---
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
        "notes": ""
    })

def update_task_status(doc_id, new_status):
    db.collection("race_tasks").document(doc_id).update({"completed": new_status})

def update_note(doc_id, note_text):
    db.collection("race_tasks").document(doc_id).update({"notes": note_text})

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
        st.subheader(f"📍 {cat}")
        tasks = db.collection("race_tasks").where("category", "==", cat).stream()
        
        has_tasks = False
        for task in tasks:
            has_tasks = True
            td = task.to_dict()
            task_id = task.id
            db_status = td.get("completed", False)
            
            # --- COLOR STABILITY ---
            bg_color = "#dcfce7" if db_status else "#fee2e2"
            border_color = "#22c55e" if db_status else "#ef4444"
            
            st.markdown(
                f"""<div style="background-color: {bg_color}; border: 2px solid {border_color}; 
                padding: 15px; border-radius: 10px; margin-bottom: 10px; color: black;">""", 
                unsafe_allow_html=True
            )
            
            cols = st.columns([1, 7, 2]) if is_admin else st.columns([1, 9])

            with cols[0]:
                is_disabled = db_status and not is_admin
                
                # We use the database status as the ONLY source of truth for the checkbox
                check_val = st.checkbox(
                    "", 
                    value=db_status, 
                    key=f"widget_{task_id}_{is_admin}", # Unique key for admin vs user
                    disabled=is_disabled, 
                    label_visibility="collapsed"
                )
                
                if check_val != db_status:
                    update_task_status(task_id, check_val)
                    st.rerun()
            
            with cols[1]:
                st.markdown(f"**{'✅' if db_status else '⏳'} {td['title']}**")
                if td.get("notes"):
                    st.info(f"📝 {td['notes']}")
                
                if is_admin:
                    with st.popover("Edit Notes"):
                        new_note = st.text_area("Notes:", value=td.get("notes", ""), key=f"note_{task_id}")
                        if st.button("Save", key=f"btn_{task_id}"):
                            update_note(task_id, new_note)
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
