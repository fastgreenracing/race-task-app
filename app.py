import streamlit as st
from google.cloud import firestore
import json
from datetime import datetime
import pytz

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Race Logistics", page_icon="🏃", layout="wide")
st.title("🏃 Fast Green Racing: Live Tracker")

# --- ADMIN SETTINGS ---
ADMIN_PASSWORD = "fastgreen2026" 
TIMEZONE = "US/Pacific"

def get_now():
    return datetime.now(pytz.timezone(TIMEZONE)).strftime("%I:%M %p")

# --- 2. DATA FUNCTIONS ---
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    if cat_ref.exists:
        return cat_ref.to_dict().get("list", ["Transportation", "Course & Traffic", "Vendors", "Finish Line"])
    return ["Transportation", "Course & Traffic", "Vendors", "Finish Line"]

def get_cat_data(cat_name):
    safe_id = cat_name.replace("/", "_").replace(" ", "_")
    doc = db.collection("settings").document(f"status_{safe_id}").get()
    if doc.exists:
        return doc.to_dict()
    return {"completed": False, "note": "", "timestamp": ""}

def set_cat_status(cat_name, status, note=None):
    safe_id = cat_name.replace("/", "_").replace(" ", "_")
    data = {"completed": status}
    if note is not None:
        data["note"] = note
        data["timestamp"] = get_now() if note else ""
    db.collection("settings").document(f"status_{safe_id}").update(data) if db.collection("settings").document(f"status_{safe_id}").get().exists else db.collection("settings").document(f"status_{safe_id}").set(data, merge=True)

def add_task(title, category):
    existing_tasks = db.collection("race_tasks").where("category", "==", category).get()
    new_order = len(existing_tasks)
    db.collection("race_tasks").add({
        "title": title, "category": category, "completed": False, "notes": "", "sort_order": new_order
    })

# --- 3. SIDEBAR: ACCESS CONTROL ---
with st.sidebar:
    st.header("🔐 Access Control")
    pwd = st.text_input("Admin Password", type="password")
    is_admin = (pwd == ADMIN_PASSWORD)
    st.session_state.admin_logged_in = is_admin

    if is_admin:
        st.success("Admin Mode: Active")
        st.divider()
        
        st.subheader("🚥 Category Control")
        cats = get_categories()
        for c in cats:
            c_data = get_cat_data(c)
            with st.expander(f"Edit {c}"):
                new_s = st.toggle("Ready Status", value=c_data.get("completed", False), key=f"t_{c}")
                new_n = st.text_input("Category Note", value=c_data.get("note", ""), key=f"n_{c}")
                if st.button("Update Category", key=f"up_{c}"):
                    set_cat_status(c, new_s, new_n)
                    st.rerun()
        
        st.divider()
        st.subheader("➕ Add New Task")
        new_title = st.text_input("Task Description")
        new_cat = st.selectbox("Assign to Category", cats)
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
        st.markdown("<hr style='border: 2px solid #333; margin-top: 40px; margin-bottom: 20px;'>", unsafe_allow_html=True)
        
        c_data = get_cat_data(cat)
        light_color = "#22c55e" if c_data.get("completed") else "#ef4444"
        
        # Header Layout: Name then Light
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <h1 style="font-size: 36px; margin: 0;">📍 {cat}</h1>
                <div style="width: 45px; height: 45px; background-color: {light_color}; 
                            border-radius: 50%; border: 3px solid #333;"></div>
            </div>
            """, unsafe_allow_html=True
        )
        
        # Display Category Note and Timestamp
        if c_data.get("note"):
            st.markdown(f"**Status Note:** {c_data['note']} <br> <small>Last Updated: {c_data.get('timestamp', 'N/A')}</small>", unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)
        
        try:
            tasks_query = db.collection("race_tasks").where("category", "==", cat).order_by("sort_order").stream()
            tasks_list = list(tasks_query)
        except Exception:
            st.warning("Database is indexing. Please wait...")
            tasks_list = []
        
        for index, task in enumerate(tasks_list):
            td = task.to_dict()
            task_id = task.id
            db_status = td.get("completed", False)
            current_order = td.get("sort_order", index)
            
            unique_key = f"widget_{task_id}_{db_status}_{is_admin}"
            bg_color = "#dcfce7" if db_status else "#fee2e2"
            border_color = "#22c55e" if db_status else "#ef4444"
            
            st.markdown(f"""<div style="background-color: {bg_color}; border: 2px solid {border_color}; padding: 20px; border-radius: 12px; margin-bottom: 5px; color: black;">""", unsafe_allow_html=True)
            
            cols = st.columns([0.6, 0.8, 6.6, 2]) if is_admin else st.columns([1, 9])
            with cols[0]:
                is_disabled = db_status and not is_admin
                if st.checkbox("", value=db_status, key=unique_key, disabled=is_disabled, label_visibility="collapsed"):
                    if not db_status: 
                        db.collection("race_tasks").document(task_id).update({"completed": True}); st.rerun()
                elif db_status:
                    if is_admin: 
                        db.collection("race_tasks").document(task_id).update({"completed": False}); st.rerun()

            if is_admin:
                with cols[1]:
                    u, d = st.columns(2)
                    if index > 0 and u.button("▲", key=f"u_{task_id}"):
                        target_order = current_order - 1
                        q = db.collection("race_tasks").where("category", "==", cat).where("sort_order", "==", target_order).limit(1).get()
                        if q: db.collection("race_tasks").document(q[0].id).update({"sort_order": current_order})
                        db.collection("race_tasks").document(task_id).update({"sort_order": target_order}); st.rerun()
                    if index < len(tasks_list)-1 and d.button("▼", key=f"d_{task_id}"):
                        target_order = current_order + 1
                        q = db.collection("race_tasks").where("category", "==", cat).where("sort_order", "==", target_order).limit(1).get()
                        if q: db.collection("race_tasks").document(q[0].id).update({"sort_order": current_order})
                        db.collection("race_tasks").document(task_id).update({"sort_order": target_order}); st.rerun()

            text_col = cols[2] if is_admin else cols[1]
            with text_col:
                icon = '✅' if db_status else '⏳'
                st.markdown(f"<span style='font-size: 24px; font-weight: bold;'>{icon} {td['title']}</span>", unsafe_allow_html=True)
                if td.get("notes"): st.info(f"📝 {td['notes']}")
                if is_admin:
                    with st.popover("Edit"):
                        n = st.text_area("Note", value=td.get("notes", ""), key=f"nt_{task_id}")
                        c1, c2 = st.columns(2)
                        if c1.button("Save", key=f"s_{task_id}"):
                            db.collection("race_tasks").document(task_id).update({"notes": n}); st.rerun()
                        if c2.button("🗑️", key=f"del_n_{task_id}"):
                            db.collection("race_tasks").document(task_id).update({"notes": ""}); st.rerun()
            
            if is_admin and cols[3].button("Delete Task", key=f"dt_{task_id}", use_container_width=True):
                db.collection("race_tasks").document(task_id).delete(); st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
            if index < len(tasks_list) - 1: st.markdown("<hr style='border: 0.5px dashed #bbb; margin: 10px auto; width: 90%;'>", unsafe_allow_html=True)

show_tasks()
