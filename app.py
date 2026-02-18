import streamlit as st
from google.cloud import firestore
import json
from datetime import datetime
import pytz

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Race Logistics", page_icon="🏃", layout="wide")

# --- CSS FOR BACKGROUND IMAGE AND READABILITY ---
st.markdown(
    """
    <style>
    .stApp {
        background-image: url("https://images.unsplash.com/photo-1530541930197-ff16ac917b0e?ixlib=rb-4.0.3&auto=format&fit=crop&w=2070&q=80");
        background-attachment: fixed;
        background-size: cover;
    }
    /* Main container overlay to protect readability */
    .main .block-container {
        background-color: rgba(255, 255, 255, 0.85); 
        padding: 40px;
        border-radius: 20px;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    /* Style headers to stand out */
    h1, h2, h3 {
        color: #1e3a1e !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

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
    return doc.to_dict() if doc.exists else {"completed": False, "note": "", "timestamp": ""}

def set_cat_status(cat_name, status, note=None):
    safe_id = cat_name.replace("/", "_").replace(" ", "_")
    data = {"completed": status}
    if note is not None:
        data["note"] = note
        data["timestamp"] = get_now() if note else ""
    db.collection("settings").document(f"status_{safe_id}").set(data, merge=True)

def update_task_status(doc_id, new_status):
    db.collection("race_tasks").document(doc_id).update({"completed": new_status})

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
                db.collection("race_tasks").add({"title": new_title, "category": new_cat, "completed": False, "notes": "", "sort_order": 99})
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
        
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
                <h1 style="font-size: 36px; margin: 0;">📍 {cat}</h1>
                <div style="width: 45px; height: 45px; background-color: {light_color}; border-radius: 50%; border: 3px solid #333;"></div>
            </div>
            """, unsafe_allow_html=True
        )
        
        if c_data.get("note"):
            st.markdown(f"**Status Note:** {c_data['note']} <br> <small>Last Updated: {c_data.get('timestamp', 'N/A')}</small>", unsafe_allow_html=True)
        
        tasks_query = db.collection("race_tasks").where("category", "==", cat).order_by("sort_order").stream()
        tasks_list = list(tasks_query)
        
        for index, task in enumerate(tasks_list):
            td = task.to_dict()
            db_status = td.get("completed", False)
            bg_color = "rgba(220, 252, 231, 0.9)" if db_status else "rgba(254, 226, 226, 0.9)"
            
            st.markdown(f"""<div style="background-color: {bg_color}; border: 2px solid #333; padding: 20px; border-radius: 12px; margin-bottom: 5px; color: black;">""", unsafe_allow_html=True)
            
            cols = st.columns([0.6, 0.8, 6.6, 2]) if is_admin else st.columns([1, 9])
            with cols[0]:
                check_val = st.checkbox("", value=db_status, key=f"w_{task.id}_{db_status}", disabled=(db_status and not is_admin), label_visibility="collapsed")
                if check_val != db_status:
                    update_task_status(task.id, check_val); st.rerun()

            text_col = cols[2] if is_admin else cols[1]
            with text_col:
                icon = '✅' if db_status else '⏳'
                st.markdown(f"<span style='font-size: 24px; font-weight: bold;'>{icon} {td['title']}</span>", unsafe_allow_html=True)
                if td.get("notes"): st.info(f"📝 {td['notes']}")
            
            st.markdown("</div>", unsafe_allow_html=True)

show_tasks()
