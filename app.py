import streamlit as st
from google.cloud import firestore
import json
from datetime import datetime
import pytz

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

# THEME OVERRIDE
st.set_page_config(
    page_title="Race Logistics", 
    page_icon="🏃", 
    layout="wide"
)

# --- CSS FOR UI (BLACK & GREEN THEME) ---
st.markdown(
    """
    <style>
    /* Global Background and Text Colors */
    .stApp {
        background-color: #000000;
        color: #28a745;
    }
    
    /* Main Content Container */
    .main .block-container {
        background-color: #000000;
        color: #28a745;
        padding: 3rem;
    }

    /* Headlines and Labels */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #28a745 !important;
    }

    /* Dividers */
    .bold-divider { 
        border: none; 
        height: 5px; 
        background-color: #28a745; 
        margin-top: 50px; 
        margin-bottom: 30px; 
        border-radius: 5px; 
    }

    /* Task Boxes */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 2px solid #28a745 !important; 
        border-radius: 15px; 
        padding: 20px !important; 
        margin-bottom: 15px !important; 
        background-color: #111111; /* Slightly lighter black for depth */
    }

    /* Checkbox Styling */
    [data-testid="stCheckbox"] { transform: scale(2.2); margin-left: 25px; margin-top: 10px; }
    [data-testid="stCheckbox"] div[role="checkbox"] { 
        border: 2px solid #28a745 !important; 
        background-color: transparent !important;
    }
    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] { 
        background-color: #28a745 !important; 
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #28a745;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {
        color: #28a745 !important;
    }

    /* Inputs and Buttons */
    .stTextInput input, .stSelectbox div {
        background-color: #111111 !important;
        color: #28a745 !important;
        border: 1px solid #28a745 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Fast Green Racing: Live Tracker")

# --- ADMIN SETTINGS & PERSISTENCE ---
ADMIN_PASSWORD = "fastgreen2026" 
TIMEZONE = "US/Pacific"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def get_now():
    return datetime.now(pytz.timezone(TIMEZONE)).strftime("%I:%M %p")

# --- DATA FUNCTIONS ---
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    return sorted(cat_ref.to_dict().get("data", []), key=lambda x: x.get('order', 0)) if cat_ref.exists else []

def save_categories(cat_data_list):
    for i, cat in enumerate(cat_data_list): cat['order'] = i
    db.collection("settings").document("categories").set({"data": cat_data_list})

def get_cat_data(cat_name):
    safe_id = cat_name.replace("/", "_").replace(" ", "_")
    doc = db.collection("settings").document(f"status_{safe_id}").get()
    return doc.to_dict() if doc.exists else {"completed": False, "note": "", "timestamp": ""}

def set_cat_status(cat_name, status, note=None):
    safe_id = cat_name.replace("/", "_").replace(" ", "_")
    data = {"completed": status}
    if note is not None:
        data.update({"note": note, "timestamp": get_now()})
    db.collection("settings").document(f"status_{safe_id}").set(data, merge=True)

# --- SIDEBAR: ADMIN ---
with st.sidebar:
    st.header("🔐 Access Control")
    if not st.session_state.authenticated:
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.authenticated = True; st.rerun()
            else: st.error("Incorrect Password")
    else:
        st.success("Admin Mode Active")
        if st.button("Logout"): st.session_state.authenticated = False; st.rerun()
        
        current_cats = get_categories()
        
        # 🚥 1. LIVE STATUS
        st.divider()
        st.subheader("🚥 Live Status Control")
        for c in current_cats:
            c_data = get_cat_data(c['name'])
            with st.expander(f"Status: {c['name']}"):
                new_s = st.toggle("Ready (GO)", value=c_data.get("completed", False), key=f"sb_t_{c['name']}")
                new_n = st.text_input("Note", value=c_data.get("note", ""), key=f"sb_n_{c['name']}")
                if st.button("Save", key=f"sb_btn_{c['name']}"):
                    set_cat_status(c['name'], new_s, new_n); st.rerun()

        # 📁 2. CATEGORY ADMIN
        st.divider()
        st.subheader("📁 Manage Categories")
        with st.expander("Move / Rename / Delete"):
            for i, cat in enumerate(current_cats):
                col_name, col_up, col_down, col_del = st.columns([4, 1, 1, 1])
                col_name.write(f"**{cat['name']}**")
                if col_up.button("🔼", key=f"cat_up_{i}") and i > 0:
                    current_cats[i], current_cats[i-1] = current_cats[i-1], current_cats[i]
                    save_categories(current_cats); st.rerun()
                if col_down.button("🔽", key=f"cat_down_{i}") and i < len(current_cats)-1:
                    current_cats[i], current_cats[i+1] = current_cats[i+1], current_cats[i]
                    save_categories(current_cats); st.rerun()
                if col_del.button("🗑️", key=f"cat_del_{i}"):
                    current_cats.pop(i); save_categories(current_cats); st.rerun()
                
                new_c_name = st.text_input("Rename:", value=cat['name'], key=f"ren_c_{i}")
                if new_c_name != cat['name'] and st.button(f"Confirm Rename", key=f"cren_{i}"):
                    old = cat['name']; cat['name'] = new_c_name; save_categories(current_cats)
                    for t in db.collection("race_tasks").where("category", "==", old).stream():
                        db.collection("race_tasks").document(
