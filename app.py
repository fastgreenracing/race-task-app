import streamlit as st
from google.cloud import firestore
import json
import time

# 1. Database Connection
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Secrets not found! Check your Advanced Settings in Streamlit.")
    st.stop()

st.set_page_config(page_title="Race Logistics Tracker", page_icon="🏃")

st.title("🏃 Fast Green Racing: Live Tracker")

# 2. Logic to update tasks
def update_task(doc_id, status):
    db.collection("race_tasks").document(doc_id).update({"completed": status})

# 3. This "Fragment" auto-refreshes every 10 seconds WITHOUT crashing
@st.fragment(run_every=10)
def show_tasks():
    categories = ["Transportation", "Course & Traffic", "Vendors & Hydration", "Finish Line"]
    
    for cat in categories:
        st.subheader(f"📍 {cat}")
        tasks = db.collection("race_tasks").where("category", "==", cat).stream()
        
        # Track if any tasks exist for this category
        has_tasks = False
        for task in tasks:
            has_tasks = True
            task_data = task.to_dict()
            
            col1, col2 = st.columns([0.1, 0.9])
            # Unique key prevents the checkbox from "flickering"
            is_done = col1.checkbox("", value=task_data["completed"], key=f"check_{task.id}")
            
            if is_done != task_data["completed"]:
                update_task(task.id, is_done)
                st.rerun() # This is safe here because it's inside a user-interaction trigger
            
            col2.write(task_data["title"])
        
        if not has_tasks:
            st.info(f"No tasks yet for {cat}. Add them in Firestore!")
        st.divider()

# Run the task list
show_tasks()

st.caption("Auto-refreshing every 10 seconds...")
