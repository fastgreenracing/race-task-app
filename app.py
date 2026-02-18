import streamlit as st
from google.cloud import firestore
import json

# Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Race Logistics", page_icon="🏃", layout="wide")
st.title("🏃 Fast Green Racing: Live Tracker")

# --- SET YOUR PASSWORD HERE ---
ADMIN_PASSWORD = "fastgreen2026" 

# --- DATA FUNCTIONS ---
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    if cat_ref.exists:
        return cat_ref.to_dict().get("list", ["Transportation", "Course & Traffic", "Vendors", "Finish Line"])
    return ["Transportation", "Course & Traffic", "Vendors", "Finish Line"]

def update_categories(new_list):
    db.collection("settings").document("categories").set({"list": new_list})

def add_task(title, category):
    db.collection("race_tasks").add({"title": title, "category": category, "completed": False})

def delete_task(doc_id):
    db.collection("race_tasks").document(doc_id).delete()

current_categories = get_categories()

# --- SIDEBAR LOGIC ---
with st.sidebar:
    st.header("🔐 Access Control")
    # Using session state to "remember" login during the session
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False

    pwd = st.text_input("Admin Password", type="password")
    
    if pwd == ADMIN_PASSWORD:
        st.session_state.admin_logged_in = True
        st.success("Admin Mode: Active")
    else:
        st.session_state.admin_logged_in = False
        st.info("Volunteer Mode: Read-Only Checkboxes")

    # This section stays visible only if the password is correct
    if st.session_state.admin_logged_in:
        st.divider()
        st.subheader("➕ Add New Task")
        new_title = st.text_input("Task Description")
        new_cat = st.selectbox("Assign to Category", current_categories)
        if st.button("Add Task", use_container_width=True):
            if new_title:
                add_task(new_title, new_cat)
                st.toast(f"Added: {new_title}") # Small notification at bottom
                st.rerun()

        st.divider()
        st.subheader("⚙️ Category Manager")
        new_cat_name = st.text_input("New Category Name")
        if st.button("Add Category", use_container_width=True):
            if new_cat_name and new_cat_name not in current_categories:
                current_categories.append(new_cat_name)
                update_categories(current_categories)
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
            
            with st.container(border=True):
                # Adjust layout based on mode
                if is_admin:
                    col_check, col_text, col_del = st.columns([1, 6, 2])
                else:
                    col_check, col_text = st.columns([1, 8])

                with col_check:
                    is_done = st.checkbox("", value=td["completed"], key=f"check_{task.id}")
                    if is_done != td["completed"]:
                        db.collection("race_tasks").document(task.id).update({"completed": is_done})
                        st.rerun()
                
                with col_text:
                    if td["completed"]:
                        st.markdown(f"~~{td['title']}~~")
                    else:
                        st.write(td["title"])
                
                if is_admin:
                    with col_del:
                        if st.button("Delete", key=f"del_{task.id}", type="secondary", use_container_width=True):
                            delete_task(task.id)
                            st.rerun()
        
        if not has_tasks:
            st.caption(f"No active tasks in {cat}")
        st.write("") # Padding

show_tasks()
