import streamlit as st
from google.cloud import firestore
import json

# Standard DB Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Ops Master Dashboard", layout="wide")

# Apply your Black & Green CSS here (omitted for brevity)

st.title("🎛️ Ops Master Dashboard")
st.write("Real-time readiness of all race locations.")

def get_site_readiness():
    # Get all categories (Locations)
    cat_ref = db.collection("settings").document("categories").get()
    categories = cat_ref.to_dict().get("data", []) if cat_ref.exists else []
    
    for cat in categories:
        site_name = cat['name']
        
        # Query tasks for this specific site
        tasks = db.collection("race_tasks").where("category", "==", site_name).stream()
        task_list = [t.to_dict() for t in tasks]
        
        if not task_list:
            continue
            
        total = len(task_list)
        completed = sum(1 for t in task_list if t.get('completed') == True)
        is_fully_ready = total == completed
        
        # Display Logic
        col1, col2, col3 = st.columns([4, 4, 2])
        with col1:
            st.subheader(site_name)
        with col2:
            progress = completed / total
            st.progress(progress)
        with col3:
            if is_fully_ready:
                st.markdown("### ✅ READY")
            else:
                st.markdown(f"### ⏳ {completed}/{total}")
        st.divider()

get_site_readiness()
