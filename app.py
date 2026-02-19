import streamlit as st
from google.cloud import firestore
import json
from datetime import datetime
import pytz

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Race Logistics", page_icon="🏃", layout="wide")

# --- CSS FOR UI ---
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
    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 3rem;
        border-radius: 25px;
        margin-top: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
    }}
    .bold-divider {{
        border: none;
        height: 5px;
        background-color: black;
        margin-top: 50px;
        margin-bottom: 30px;
        border-radius: 5px;
    }}
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {{
        border: 3px solid black !important;
        border-radius: 15px;
        padding: 20px !important;
        margin-bottom: 15px !important;
        background-color: rgba(255, 255, 255, 0.6);
    }}
    [data-testid="stCheckbox"] {{
        transform: scale(2.2);
        margin-left: 25px;
        margin-top: 10px;
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

# --- DATA FUNCTIONS ---
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    if cat_ref.exists:
        data = cat_ref.to_dict().get("data", [])
        return sorted(data, key=lambda x: x.get('order', 0))
    return []

def save_categories(cat_data_list):
    # Ensure orders are sequential 0, 1, 2...
    for i, cat in enumerate(cat_data_list):
        cat['order'] = i
    db.collection("settings").document("categories").set({"data": cat_data_list})

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

# --- SIDEBAR: ADMIN ---
with st.sidebar:
    st.header("🔐 Access Control")
    pwd = st.text_input("Admin Password", type="password")
    is_admin = (pwd == ADMIN_PASSWORD)
    
    if is_admin:
        st.success("Admin Mode")
        current_cats = get_categories()
        
        # --- CATEGORY MANAGEMENT ---
        st.divider()
        st.subheader("📁 Manage Categories")
        
        with st.expander("🔢 Move / 🗑️ Delete Categories"):
            for i, cat in enumerate(current_cats):
                col_name, col_up, col_down, col_del = st.columns([4, 1, 1, 1])
                col_name.write(f"**{cat['name']}**")
                
                if col_up.button("🔼", key=f"cat_up_{i}") and i > 0:
                    current_cats[i], current_cats[i-1] = current_cats[i-1], current_cats[i]
                    save_categories(current_cats)
                    st.rerun()
                
                if col_down.button("🔽", key=f"cat_down_{i}") and i < len(current_cats)-1:
                    current_cats[i], current_cats[i+1] = current_cats[i+1], current_cats[i]
                    save_categories(current_cats)
                    st.rerun()
                
                if col_del.button("🗑️", key=f"cat_del_{i}"):
                    current_cats.pop(i)
                    save_categories(current_cats)
                    st.rerun()

        with st.expander("➕ Add Category"):
            new_cat_name = st.text_input("New Category Name")
            if st.button("Create"):
                current_cats.append({"name": new_cat_name, "order": len(current_cats)})
                save_categories(current_cats)
                st.rerun()

        # --- TASK MANAGEMENT ---
        st.divider()
        st.subheader("📝 Manage Tasks")
        
        with st.expander("🔢 Move / 🗑️ Delete Tasks"):
            sel_cat = st.selectbox("Select Category", [c['name'] for c in current_cats], key="manage_task_cat")
            tasks_stream = db.collection("race_tasks").where("category", "==", sel_cat).order_by("sort_order").stream()
            tasks = [t for t in tasks_stream]
            
            for i, t in enumerate(tasks):
                td = t.to_dict()
                col_t_name, col_t_up, col_t_down, col_t_del = st.columns([4, 1, 1, 1])
                col_t_name.write(f"{td['title'][:15]}...")
                
                if col_t_up.button("🔼", key=f"t_up_{t.id}") and i > 0:
                    prev_t = tasks[i-1]
                    db.collection("race_tasks").document(t.id).update({"sort_order": i-1})
                    db.collection("race_tasks").document(prev_t.id).update({"sort_order": i})
                    st.rerun()
                
                if col_t_down.button("🔽", key=f"t_down_{t.id}") and i < len(tasks)-1:
                    next_t = tasks[i+1]
                    db.collection("race_tasks").document(t.id).update({"sort_order": i+1})
                    db.collection("race_tasks").document(next_t.id).update({"sort_order": i})
                    st.rerun()
                    
                if col_t_del.button("🗑️", key=f"t_del_{t.id}"):
                    db.collection("race_tasks").document(t.id).delete()
                    st.rerun()

        with st.expander("➕ Add Task"):
            t_cat = st.selectbox("Category", [c['name'] for c in current_cats], key="add_t_cat")
            t_title = st.text_input("Task Title")
            if st.button("Add Task"):
                # Get count for last position
                existing = db.collection("race_tasks").where("category", "==", t_cat).get()
                db.collection("race_tasks").add({
                    "category": t_cat,
                    "title": t_title,
                    "completed": False,
                    "sort_order": len(existing)
                })
                st.rerun()

        # --- STATUS CONTROL ---
        st.divider()
        st.subheader("🚥 Live Status Control")
        for c in current_cats:
            c_data = get_cat_data(c['name'])
            with st.expander(f"Edit {c['name']}"):
                new_s = st.toggle("Ready (GO)", value=c_data.get("completed", False), key=f"t_{c['name']}")
                new_n = st.text_input("Note", value=c_data.get("note", ""), key=f"n_{c['name']}")
                if st.button("Save", key=f"up_{c['name']}"):
                    set_cat_status(c['name'], new_s, new_n)
                    st.rerun()

# --- MAIN DISPLAY ---
@st.fragment(run_every=5)
def show_tasks():
    is_admin = st.session_state.get('admin_logged_in', False)
    categories = get_categories()
    
    for cat_dict in categories:
        cat = cat_dict['name']
        st.markdown('<div class="bold-divider"></div>', unsafe_allow_html=True)
        c_data = get_cat_data(cat)
        
        col_name, col_status_group = st.columns([7, 3])
        with col_name:
            st.header(f"📍 {cat}")
        with col_status_group:
            is_go = c_data.get("completed", False)
            s_text = "GO" if is_go else "NO GO"
            s_color = "green" if is_go else "red"
            st.markdown(f'<div style="text-align: center;"><p style="font-weight: bold; font-size: 20px; margin-bottom: -5px;">STATUS</p><h2 style="color: {s_color}; font-size: 48px; font-weight: 900; margin: 0;">{s_text}</h2></div>', unsafe_allow_html=True)

        if c_data.get("note"):
            st.info(f"**Note:** {c_data['note']} \n\n *Updated: {c_data.get('timestamp')}*")
        
        tasks_query = db.collection("race_tasks").where("category", "==", cat).order_by("sort_order").stream()
        for task in tasks_query:
            td = task.to_dict()
            t_cols = st.columns([1.5, 8.5])
            with t_cols[0]:
                check = st.checkbox("", value=td.get("completed", False), key=f"w_{task.id}", disabled=(td.get("completed") and not is_admin), label_visibility="collapsed")
                if check != td.get("completed"):
                    db.collection("race_tasks").document(task.id).update({"completed": check}); st.rerun()
            with t_cols[1]:
                icon = '✅ ' if td.get("completed") else ''
                st.markdown(f"### {icon}{td['title']}")

show_tasks()
