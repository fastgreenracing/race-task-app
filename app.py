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
    
    /* TASK CARD STYLING */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {{
        border: 3px solid black !important;
        border-radius: 15px;
        padding: 20px !important;
        margin-bottom: 15px !important;
        background-color: rgba(255, 255, 255, 0.6);
    }}

    /* CHECKBOX SCALING & STYLE */
    [data-testid="stCheckbox"] {{
        transform: scale(2.2);
        margin-left: 25px;
        margin-top: 10px;
    }}
    
    /* Force checkbox to turn green when checked */
    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] {{
        background-color: #28a745 !important;
        border-color: #28a745 !important;
    }}

    /* Standard border when unchecked */
    [data-testid="stCheckbox"] div[role="checkbox"] {{
        border: 3px solid black !important;
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

# --- SIDEBAR: ADMIN CONTROLS ---
with st.sidebar:
    st.header("🔐 Access Control")
    pwd = st.text_input("Admin Password", type="password")
    is_admin = (pwd == ADMIN_PASSWORD)
    st.session_state.admin_logged_in = is_admin
    
    if is_admin:
        st.success("Admin Mode")
        current_cats = get_categories()
        
        st.divider()
        st.subheader("🚥 Live Status Control")
        for c in current_cats:
            c_data = get_cat_data(c['name'])
            with st.expander(f"Status: {c['name']}"):
                new_s = st.toggle("Ready (GO)", value=c_data.get("completed", False), key=f"sidebar_t_{c['name']}")
                new_n = st.text_input("Note", value=c_data.get("note", ""), key=f"sidebar_n_{c['name']}")
                if st.button("Save Changes", key=f"sidebar_btn_{c['name']}"):
                    set_cat_status(c['name'], new_s, new_n)
                    st.rerun()

        st.divider()
        st.subheader("📁 Structure Admin")
        with st.expander("Move / Rename / Delete"):
            for i, cat in enumerate(current_cats):
                col_name, col_up, col_down = st.columns([6, 1, 1])
                col_name.write(f"**{cat['name']}**")
                if col_up.button("🔼", key=f"cat_up_{i}") and i > 0:
                    current_cats[i], current_cats[i-1] = current_cats[i-1], current_cats[i]
                    save_categories(current_cats); st.rerun()
                if col_down.button("🔽", key=f"cat_down_{i}") and i < len(current_cats)-1:
                    current_cats[i], current_cats[i+1] = current_cats[i+1], current_cats[i]
                    save_categories(current_cats); st.rerun()

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
                check = st.checkbox("", value=td.get("completed", False), key=f"w_{task.id}_{td.get('completed')}", disabled=(td.get("completed") and not is_admin), label_visibility="collapsed")
                if check != td.get("completed"):
                    db.collection("race_tasks").document(task.id).update({"completed": check})
                    st.rerun()
            with t_cols[1]:
                # REMOVED the redundant icon logic here
                st.markdown(f"### {td['title']}")

show_tasks()
