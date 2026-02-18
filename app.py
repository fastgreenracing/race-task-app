import streamlit as st
from google.cloud import firestore
import json

# Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Race Logistics", page_icon="🏃")
st.title("🏃 Fast Green Racing: Live Tracker")

# 1. Function to Add Tasks
def add_task(title, category):
    db.collection("race_tasks").add({
        "title": title,
        "category": category,
        "completed": False
    })

# 2. Main Task Display (Refreshes every 10s)
@st.fragment(run_every=10)
def show_tasks():
    categories = ["Transportation", "Course & Traffic", "Vendors & Hydration", "Finish Line"]
    for cat in categories:
        st.subheader(f"📍 {cat}")
        tasks = db.collection("race_tasks").where("category", "==", cat).stream()
        
        has_tasks = False
        for task in tasks:
            has_tasks = True
            td = task.to_dict()
            col1, col2 = st.columns([0.1, 0.9])
            if col1.checkbox("", value=td["completed"], key=task.id):
                if not td["completed"]:
                    db.collection("race_tasks").document(task.id).update({"completed": True})
                    st.rerun()
            elif td["completed"]:
                db.collection("race_tasks").document(task.id).update({"completed": False})
                st.rerun()
            
            col2.write(td["title"])
        
        if not has_tasks:
            st.info(f"No tasks for {cat}")
        st.divider()

show_tasks()

# 3. Sidebar: Add New Tasks (Perfect for on-site use)
with st.sidebar:
    st.header("➕ Add New Task")
    new_title = st.text_input("Task Name")
    new_cat = st.selectbox("Category", ["Transportation", "Course & Traffic", "Vendors & Hydration", "Finish Line"])
    if st.button("Add to List"):
        if new_title:
            add_task(new_title, new_cat)
            st.success("Added!")
            st.rerun()
