import streamlit as st
from google.cloud import firestore
import json

# Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Race Logistics", page_icon="🏃", layout="wide")
st.title("🏃 Fast Green Racing: Live Tracker")

# --- CATEGORY MANAGEMENT ---
# We store categories in Firestore so they persist even when the app restarts
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    if cat_ref.exists:
        return cat_ref.to_dict().get("list", ["General"])
    return ["General"]

def update_categories(new_list):
    db.collection("settings").document("categories").set({"list": new_list})

current_categories = get_categories()

# --- TASK FUNCTIONS ---
def add_task(title, category):
    db.collection("race_tasks").add({
        "title": title,
        "category": category,
        "completed": False
    })

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
            
            # Use a container to keep things together
            with st.container(border=True):
                col_check, col_text, col_del = st.columns([1, 6, 2])
                
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
                
                with col_del:
                    if st.button("Delete", key=f"del_{task.id}", type="secondary", use_container_width=True):
                        delete_task(task.id)
                        st.rerun()
        
        if not has_tasks:
            st.info(f"No tasks for {cat}")

show_tasks()

# --- SIDEBAR: MANAGEMENT ---
with st.sidebar:
    st.header("➕ Add New Task")
    new_title = st.text_input("Task Name")
    new_cat = st.selectbox("Assign to Category", current_categories)
    if st.button("Add Task"):
        if new_title:
            add_task(new_title, new_cat)
            st.success("Task Added!")
            st.rerun()

    st.divider()
    st.header("⚙️ Category Manager")
    new_cat_name = st.text_input("New Category Name")
    if st.button("Add Category"):
        if new_cat_name and new_cat_name not in current_categories:
            current_categories.append(new_cat_name)
            update_categories(current_categories)
            st.success(f"Added {new_cat_name}")
            st.rerun()
    
    if st.button("Clear Empty Categories"):
        # Resets back to default
        update_categories(["Transportation", "Course & Traffic", "Vendors", "Finish Line"])
        st.rerun()
