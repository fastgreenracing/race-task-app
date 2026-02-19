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
BACKGROUND_IMAGE_URL = "https://photos.smugmug.com/Mountains-2-Beach-Marathons/2018-Clif-Bar-Mountains-to-Beach-Marathon-Half/M2B-2018-Full-Marathon/M2B-2018-Full-Marathon-The-Start/i-dfXFsF4/2/KhM2r3JQqVtWPLHJdSsTbZzbPRTQp8fjhcHzQ2rCN/X2/DHHolmes_180527_DH0114_M2B-X2.jpg"

st.markdown(
    f"""
    <style>
    :root {{ --primary-color: #28a745 !important; }}
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
    .bold-divider {{ border: none; height: 5px; background-color: black; margin-top: 50px; margin-bottom: 30px; border-radius: 5px; }}
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {{
        border: 3px solid black !important; border-radius: 15px; padding: 20px !important; margin-bottom: 15px !important; background-color: rgba(255, 255, 255, 0.6);
    }}
    [data-testid="stCheckbox"] {{ transform: scale(2.2); margin-left: 25px; margin-top: 10px; }}
    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] {{ background-color: #28a745 !important; border-color: #28a745 !important; }}
    [data-testid="stCheckbox"] div[role="checkbox"] {{ border: 3px solid black !important; }}
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
        # Admin controls follow (Status, Categories, Tasks, Map Management)...
        st.divider()
        st.subheader("🗺️ Map Management")
        if st.button("CLEAR ALL STAFF FROM MAP", type="primary", use_container_width=True):
            for doc in db.collection("staff_locations").stream():
                db.collection("staff_locations").document(doc.id).delete()
            st.warning("Map Reset Complete."); st.rerun()

# --- MAIN DISPLAY ---
@st.fragment(run_every=5)
def show_tasks():
    is_admin = st.session_state.authenticated
    categories = get_categories()
    for cat_dict in categories:
        cat = cat_dict['name']
        st.markdown('<div class="bold-divider"></div>', unsafe_allow_html=True)
        c_data = get_cat_data(cat)
        col_name, col_status_group = st.columns([7, 3])
        with col_name: st.markdown(f"## <u>**{cat}**</u>", unsafe_allow_html=True)
        with col_status_group:
            is_go = c_data.get("completed", False)
            s_color = "green" if is_go else "red"
            st.markdown(f'<div style="text-align: center;"><p style="font-weight: bold; font-size: 20px;">STATUS</p><h2 style="color: {s_color}; font-size: 48px; font-weight: 900;">{"GO" if is_go else "NO GO"}</h2></div>', unsafe_allow_html=True)
        if c_data.get("note"): st.info(f"**Note:** {c_data['note']} \n\n *Updated: {c_data.get('timestamp')}*")
        
        tasks_query = db.collection("race_tasks").where("category", "==", cat).order_by("sort_order").stream()
        for task in tasks_query:
            td = task.to_dict()
            t_cols = st.columns([1.5, 8.5])
            with t_cols[0]:
                check = st.checkbox("", value=td.get("completed", False), key=f"w_{task.id}_{td.get('completed')}", disabled=(td.get("completed") and not is_admin), label_visibility="collapsed")
                if check != td.get("completed"):
                    db.collection("race_tasks").document(task.id).update({"completed": check}); st.rerun()
            with t_cols[1]: st.markdown(f"### {td['title']}")

show_tasks()
