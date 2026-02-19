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
    
    /* FIX FOR ADMIN SIDEBAR TOGGLE BOX */
    [data-testid="stSidebar"] [data-testid="stVerticalBlockBorderWrapper"] {{
        border: 2px solid black !important;
        border-radius: 10px;
        padding: 10px !important;
    }}
    
    /* Ensure toggle and text fit inside the sidebar container */
    [data-testid="stSidebar"] .stToggle {{
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 10px;
        width: 100%;
        overflow: hidden;
    }}
    
    [data-testid="stSidebar"] .stToggle label p {{
        font-size: 22px !important;
        font-weight: bold !important;
        color: #31333F !important;
        margin: 0 !important;
    }}

    /* Standard Task Card Styling (User Side) */
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
    [data-testid="stCheckbox"] div[role="checkbox"] {{
        border: 3px solid black !important;
    }}
    
    /* Status Light Style */
    .status-bulb {{
        width: 55px;
        height: 55px;
        border-radius: 50%;
        border: 4px solid black;
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
    return cat_ref.to_dict().get("list", ["Transportation", "Course & Traffic", "Vendors", "Finish Line"]) if cat_ref.exists else ["Transportation", "Course & Traffic", "Vendors", "Finish Line"]

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

# --- 3. SIDEBAR: ADMIN ---
with st.sidebar:
    st.header("🔐 Access Control")
    pwd = st.text_input("Admin Password", type="password")
    is_admin = (pwd == ADMIN_PASSWORD)
    st.session_state.admin_logged_in = is_admin
    
    if is_admin:
        st.success("Admin Mode")
        st.divider()
        cats = get_categories()
        for c in cats:
            c_data = get_cat_data(c)
            with st.expander(f"Edit {c}"):
                # Toggle box container for better layout
                with st.container(border=True):
                    new_s = st.toggle("Ready (GO)", value=c_data.get("completed", False), key=f"t_{c}")
                
                new_n = st.text_input("Note", value=c_data.get("note", ""), key=f"n_{c}")
                if st.button("Save", key=f"up_{c}"):
                    set_cat_status(c, new_s, new_n)
                    st.rerun()

# --- 4. MAIN DISPLAY ---
@st.fragment(run_every=5)
def show_tasks():
    is_admin = st.session_state.get('admin_logged_in', False)
    categories = get_categories()
    
    for cat in categories:
        st.divider()
        c_data = get_cat_data(cat)
        
        col_name, col_status_group, col_bulb = st.columns([7, 1.5, 1.5])
        
        with col_name:
            st.header(f"📍 {cat}")
            
        with col_status_group:
            is_go = c_data.get("completed", False)
            s_text = "GO" if is_go else "NO GO"
            s_color = "green" if is_go else "red"
            st.markdown(f"""
                <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding-top: 5px;">
                    <p style="margin-bottom: -5px; font-weight: bold; font-size: 18px; color: #333; text-transform: uppercase;">STATUS</p>
                    <h2 style="color: {s_color}; margin: 0; font-weight: 900; line-height: 1;">{s_text}</h2>
                </div>
            """, unsafe_allow_html=True)
            
        with col_bulb:
            l_color = "#22c55e" if is_go else "#ef4444"
            st.markdown(f'<div class="status-bulb" style="background-color: {l_color}; margin-top: 10px;"></div>', unsafe_allow_html=True)

        if c_data.get("note"):
            st.info(f"**Note:** {c_data['note']} \n\n *Updated: {c_data.get('timestamp')}*")
        
        tasks_query = db.collection("race_tasks").where("category", "==", cat).order_by("sort_order").stream()
        for task in tasks_query:
            td = task.to_dict()
            db_status = td.get("completed", False)
            
            t_cols = st.columns([1.5, 8.5])
            with t_cols[0]:
                check = st.checkbox("", value=db_status, key=f"w_{task.id}_{db_status}", disabled=(db_status and not is_admin), label_visibility="collapsed")
                if check != db_status:
                    db.collection("race_tasks").document(task.id).update({"completed": check}); st.rerun()
            with t_cols[1]:
                icon = '✅' if db_status else '⏳'
                st.markdown(f"### {icon} {td['title']}")
                if td.get("notes"): st.info(f"📝 {td['notes']}")

show_tasks()
