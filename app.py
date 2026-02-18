To give you that immediate visual satisfaction of a job well done, we can wrap each task in a custom "Status Box."

Since standard Streamlit checkboxes don't support dynamic background colors out of the box, I’ve used a small bit of Markdown with HTML/CSS to style the container. Now, when a volunteer checks a task, the entire background of that row will glow green.

Updated app.py
Replace your show_tasks function (or the whole file) with this version:

Python
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
    if 'admin_logged_in' not in st.session_state:
        st.session_state.admin_logged_in = False

    pwd = st.text_input("Admin Password", type="password")
    if pwd == ADMIN_PASSWORD:
        st.session_state.admin_logged_in = True
        st.success("Admin Mode: Active")
    else:
        st.session_state.admin_logged_in = False

    if st.session_state.admin_logged_in:
        st.divider()
        st.subheader("➕ Add New Task")
        new_title = st.text_input("Task Description")
        new_cat = st.selectbox("Assign to Category", current_categories)
        if st.button("Add Task", use_container_width=True):
            if new_title:
                add_task(new_title, new_cat)
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
            
            # --- CUSTOM DYNAMIC STYLING ---
            bg_color = "rgba(40, 167, 69, 0.2)" if td["completed"] else "rgba(0,0,0,0)"
            border_color = "#28a745" if td["completed"] else "#d1d5db"
            
            # This creates a "wrapper" around the task
            st.markdown(
                f"""
                <div style="background-color: {bg_color}; border: 2px solid {border_color}; 
                            padding: 10px; border-radius: 10px; margin-bottom: 5px;">
                """, 
                unsafe_allow_html=True
            )
            
            # Place the interactive elements on top of the styled background
            if is_admin:
                col_check, col_text, col_del = st.columns([1, 6, 2])
            else:
                col_check, col_text = st.columns([1, 8])

            with col_check:
                is_done = st.checkbox("", value=td["completed"], key=f"check_{task.id}", label_visibility="collapsed")
                if is_done != td["completed"]:
                    db.collection("race_tasks").document(task.id).update({"completed": is_done})
                    st.rerun()
            
            with col_text:
                if td["completed"]:
                    st.markdown(f"**✅ {td['title']}**")
                else:
                    st.write(td["title"])
            
            if is_admin:
                with col_del:
                    if st.button("Delete", key=f"del_{task.id}", type="secondary", use_container_width=True):
                        delete_task(task.id)
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        
        if not has_tasks:
            st.caption(f"No active tasks in {cat}")
        st.write("") 

show_tasks()
