import streamlit as st
from google.cloud import firestore
import json

# Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

# --- CATEGORIES ---
CATEGORIES = ["Transportation", "Course & Traffic", "Vendors & Hydration", "Finish Line"]

st.set_page_config(page_title="Race Logistics", page_icon="🏃")
st.title("🏃 Fast Green Racing: Live Tracker")

def add_task(title, category):
    db.collection("race_tasks").add({
        "title": title,
        "category": category,
        "completed": False
    })

def delete_task(doc_id):
    db.collection("race_tasks").document(doc_id).delete()

@st.fragment(run_every=10)
def show_tasks():
    for cat in CATEGORIES:
        st.subheader(f"📍 {cat}")
        tasks = db.collection("race_tasks").where("category", "==", cat).stream()
        
        has_tasks = False
        for task in tasks:
            has_tasks = True
            td = task.to_dict()
            
            # Create three columns: Checkbox, Task Text, and Delete Button
            col_check, col_text, col_del = st.columns([0.1, 0.7, 0.2])
            
            # 1. Completion Toggle
            is_checked = col_check.checkbox("", value=td["completed"], key=f"check_{task.id}")
            if is_checked != td["completed"]:
                db.collection("race_tasks").document(task.id).update({"completed": is_checked})
                st.rerun()
            
            # 2. Task Text (Strike through if completed)
            display_text = f"~~{td['title']}~~" if td["completed"] else td["title"]
            col_text.write(display_text)
            
            # 3. Delete Button (Inside an expander to prevent accidental taps)
            if col_del.button("🗑️", key=f"del_{task.id}"):
                delete_task(task.id)
                st.rerun()
        
        if not has_tasks:
            st.info(f"No tasks for {cat}")
        st.divider()

show_tasks()

with st.sidebar:
    st.header("➕ Add New Task")
    new_title = st.text_input("Task Name")
    new_cat = st.selectbox("Category", CATEGORIES)
    if st.button("Add to List"):
        if new_title:
            add_task(new_title, new_cat)
            st.success("Added!")
            st.rerun()
