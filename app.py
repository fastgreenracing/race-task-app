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

# --- CATEGORY MANAGEMENT ---
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    if cat_ref.exists:
        return cat_ref.to_dict().get("list", ["General"])
    return ["General"]

def update_categories(new_list):
    db.collection("settings").document("categories").set({"list": new_list})

current_categories = get_categories()

# --- ADMIN CHECK ---
with st.sidebar:
    st.header("🔐 Admin Access")
    pwd = st.text_input("Enter Password to Edit", type="password")
    is_admin = (pwd == ADMIN_PASSWORD)
    
    if is_admin:
        st.success("Admin Mode Active")
    else:
        st.info("Volunteer Mode: View & Check only")

# --- TASK FUNCTIONS ---
def add_task(title, category):
    db.collection("race_tasks").add({"title": title, "category": category, "completed": False})

def delete_task(doc_id):
    db.collection("race_tasks").document(doc_id).delete()

# --- UI DISPLAY ---
@st.fragment(run_every=10)
def show_tasks():
    for cat in current_categories:
        st.subheader(f"📍 {cat}")
        tasks = db.collection("race_tasks").where("category", "==", cat).stream()
        
        has_tasks = False
        for task in tasks:
            has_tasks = True
            td = task.to_dict()
            
            with st.container(border=True):
                # Adjust columns based on Admin status
                if is_admin:
                    col_check, col_text, col_del = st.columns([1, 6, 2])
                else:
                    col_check, col_text = st.columns([1, 8])

                with col_check:
                    is_checked = st.checkbox("", value=td["completed"], key=f"check_{task.id}")
                    if is_checked != td["completed"]:
                        db.collection("race_tasks").document(task.id).update({"completed": is_checked})
                        st.rerun()
                
                with col_text:
                    if td["completed"]:
                        st.markdown(f"~~{td['title']}~~")
                    else:
                        st.write(td["title"])
                
                # Only show Delete button if password is correct
                if is_admin:
                    with col_del:
                        if st.button("Delete", key=f"del_{task.id}", type="secondary", use_container_width=True):
                            delete_task(task.id)
                            st.rerun()
        
        if not has_tasks:
            st.info(f"No tasks for {cat}")

show_tasks()

# --- SIDEBAR: HIDDEN ADMIN TOOLS ---
if is_admin:
    st.divider()
    st.header("➕ Add New Task")
    new_title = st.text_input("Task Name")
    new_cat = st.selectbox("Assign to Category", current_categories)
    if st.button("Add Task"):
        if new_title:
            add_task(new_title, new_cat)
            st.rerun()

    st.divider()
    st.header("⚙️ Category Manager")
    new_cat_name = st.text_input("New Category Name")
    if st.button("Add Category"):
        if new_cat_name and new_cat_name not in current_categories:
            current_categories.append(new_cat_name)
            update_categories(current_categories)
            st.rerun()
