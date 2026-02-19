import streamlit as st
from google.cloud import firestore
import json
from datetime import datetime
import pytz

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Race Logistics", page_icon="🏃", layout="wide")

# --- CUSTOM BACKGROUND & THEMING ---
BACKGROUND_IMAGE_URL = "https://images.unsplash.com/photo-1530541930197-ff16ac917b0e?auto=format&fit=crop&w=2070&q=80"

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(rgba(255, 255, 255, 0.7), rgba(255, 255, 255, 0.7)), 
                    url("{BACKGROUND_IMAGE_URL}");
        background-attachment: fixed;
        background-size: cover;
        background-position: center;
    }}
    /* Main Container */
    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 3rem;
        border-radius: 25px;
        margin-top: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
    }}
    
    /* ENLARGE CHECKBOXES AND BOLD OUTLINE */
    [data-testid="stCheckbox"] {{
        transform: scale(2.2); /* Increased from 1.8 to 2.2 */
        margin-left: 25px;
        margin-top: 10px;
    }}
    
    /* Extra thick black border for high visibility */
    [data-testid="stCheckbox"] div[role="checkbox"] {{
        border: 3px solid black !important;
        background-color: white !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }}

    /* Remove the default Streamlit focus/selection lines */
    [data-testid="stCheckbox"] div {{
        border: none !important;
    }}
    
    h1 {{
        color: #000000 !important;
        font-family: 'Helvetica Neue', sans-serif;
    }}
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

def move_task(task_id, category, current_order, direction):
    target_order = current_order + direction
    query = db.collection("race_tasks").where("category", "==", category).where("sort_order", "==", target_order).limit(1).get()
    if query:
        target_doc = query[0]
        db.collection("race_tasks").document(task_id).update({"sort_order": target_order})
        db.collection("race_tasks").document(target_doc.id).update({"sort_order": current_order})

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
                existing = db.collection("race_tasks").where("category", "==", new_cat).get()
                db.collection("race_tasks").add({
                    "title": new_title, "category": new_cat, "completed": False, 
                    "notes": "", "sort_order": len(existing)
                })
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
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
                <h1 style="font-size: 38px; margin: 0;">📍 {cat}</h1>
                <div style="width: 55px; height: 55px; background-color: {light_color}; border-radius: 50%; border: 4px solid #000;"></div>
            </div>
            """, unsafe_allow_html=True
        )
        
        if c_data.get("note"):
            st.markdown(f"<div style='background-color:#e1f5fe; padding:15px; border-radius:10px; border-left: 8px solid #03a9f4; margin-bottom:20px;'><span style='font-size: 20px;'><strong>Status Note:</strong> {c_data['note']}</span><br><small>Updated: {c_data.get('timestamp')}</small></div>", unsafe_allow_html=True)
        
        try:
            tasks_query = db.collection("race_tasks").where("category", "==", cat).order_by("sort_order").stream()
            tasks_list = list(tasks_query)
        except Exception:
            tasks_list = []
        
        for index, task in enumerate(tasks_list):
            td = task.to_dict()
            task_id = task.id
            db_status = td.get("completed", False)
            current_order = td.get("sort_order", index)
            
            unique_key = f"w_{task_id}_{db_status}_{is_admin}"
            bg_color = "rgba(220, 252, 231, 1.0)" if db_status else "rgba(254, 226, 226, 1.0)"
            
            st.markdown(f"""<div style="background-color: {bg_color}; border: 3px solid black; padding: 30px; border-radius: 15px; margin-bottom: 15px; color: black;">""", unsafe_allow_html=True)
            
            # Widened the checkbox column to accommodate the larger scale
            cols = st.columns([1.2, 0.8, 6.0, 2]) if is_admin else st.columns([1.5, 8.5])

            with cols[0]:
                is_disabled = db_status and not is_admin
                check_val = st.checkbox("", value=db_status, key=unique_key, disabled=is_disabled, label_visibility="collapsed")
                if check_val != db_status:
                    update_task_status(task_id, check_val)
                    st.rerun()
            
            if is_admin:
                with cols[1]:
                    u, d = st.columns(2)
                    if index > 0 and u.button("▲", key=f"u_{task_id}"):
                        move_task(task_id, cat, current_order, -1); st.rerun()
                    if index < len(tasks_list) - 1 and d.button("▼", key=f"d_{task_id}"):
                        move_task(task_id, cat, current_order, 1); st.rerun()

            text_col = cols[2] if is_admin else cols[1]
            with text_col:
                icon = '✅' if db_status else '⏳'
                st.markdown(f"<span style='font-size: 28px; font-weight: bold;'>{icon} {td['title']}</span>", unsafe_allow_html=True)
                if td.get("notes"): st.info(f"📝 {td['notes']}")
                
                if is_admin:
                    with st.popover("Edit Note"):
                        n = st.text_area("Edit:", value=td.get("notes", ""), key=f"nt_{task_id}")
                        c1, c2 = st.columns(2)
                        if c1.button("Save", key=f"s_{task_id}"):
                            db.collection("race_tasks").document(task_id).update({"notes": n}); st.rerun()
                        if c2.button("🗑️", key=f"del_n_{task_id}"):
                            db.collection("race_tasks").document(task_id).update({"notes": ""}); st.rerun()
            
            if is_admin:
                with cols[3]:
                    if st.button("Delete Task", key=f"dt_{task_id}", use_container_width=True):
                        db.collection("race_tasks").document(task_id).delete(); st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

show_tasks()
