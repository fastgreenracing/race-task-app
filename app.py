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
    .main .block-container {{
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 3rem;
        border-radius: 25px;
        margin-top: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.15);
    }}
    /* The Card Styling */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {{
        border: 3px solid black !important;
        border-radius: 15px;
        padding: 20px !important;
        margin-bottom: 15px !important;
        background-color: rgba(255, 255, 255, 0.5);
    }}
    [data-testid="stCheckbox"] {{
        transform: scale(2.2);
        margin-left: 25px;
        margin-top: 10px;
    }}
    [data-testid="stCheckbox"] div[role="checkbox"] {{
        border: 3px solid black !important;
        background-color: white !important;
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

# --- DATA FUNCTIONS ---
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    return cat_ref.to_dict().get("list", ["Transportation", "Course & Traffic", "Vendors", "Finish Line"]) if cat_ref.exists else ["Transportation", "Course & Traffic", "Vendors", "Finish Line"]

def get_cat_data(cat_name):
    safe_id = cat_name.replace("/", "_").replace(" ", "_")
    doc = db.collection("settings").document(f"status_{safe_id}").get()
    return doc.to_dict() if doc.exists else {"completed": False, "note": "", "timestamp": "", "show_start_msg": False}

def set_cat_status(cat_name, status, note=None, show_start=False):
    safe_id = cat_name.replace("/", "_").replace(" ", "_")
    data = {"completed": status, "show_start_msg": show_start}
    if note is not None:
        data["note"] = note
        data["timestamp"] = get_now() if note else ""
    db.collection("settings").document(f"status_{safe_id}").set(data, merge=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔐 Access Control")
    pwd = st.text_input("Admin Password", type="password")
    is_admin = (pwd == ADMIN_PASSWORD)
    st.session_state.admin_logged_in = is_admin

    if is_admin:
        st.success("Admin Mode: Active")
        st.divider()
        cats = get_categories()
        for c in cats:
            c_data = get_cat_data(c)
            with st.expander(f"Edit {c}"):
                new_s = st.toggle("Ready (GO)", value=c_data.get("completed", False), key=f"t_{c}")
                new_start = st.radio("Start Msg?", ["Yes", "No"], index=0 if c_data.get("show_start_msg") else 1, horizontal=True, key=f"s_{c}")
                new_n = st.text_input("Note", value=c_data.get("note", ""), key=f"n_{c}")
                if st.button("Save", key=f"up_{c}"):
                    set_cat_status(c, new_s, new_n, show_start=(new_start == "Yes"))
                    st.rerun()

# --- MAIN DISPLAY ---
@st.fragment(run_every=5)
def show_tasks():
    is_admin = st.session_state.get('admin_logged_in', False)
    categories = get_categories()
    
    for cat in categories:
        st.markdown("<hr style='border: 2px solid #333; margin-top: 40px;'>", unsafe_allow_html=True)
        
        c_data = get_cat_data(cat)
        is_go = c_data.get("completed", False)
        l_color = "#22c55e" if is_go else "#ef4444"
        s_text = "GO" if is_go else "NO GO"
        s_color = "#166534" if is_go else "#991b1b"
        
        # FINAL ATTEMPT FIX: Building HTML string outside the markdown call to prevent code-block detection
        start_html = f"<div style='color:black; font-weight:bold; font-size:14px; text-align:center; margin-top:5px;'>Go ahead and start.<br>See note.</div>" if c_data.get("show_start_msg") else ""
        
        header_template = f"""
        <div style="display:flex; justify-content:space-between; align-items:flex-start; width:100%; margin-bottom:20px;">
            <div style="font-size:38px; font-weight:bold; color:black;">📍 {cat}</div>
            <div style="display:flex; align-items:center;">
                <div style="text-align:right; margin-right:15px;">
                    <div style="font-size:12px; font-weight:bold; color:#333;">STATUS</div>
                    <div style="font-size:32px; font-weight:900; color:{s_color};">{s_text}</div>
                </div>
                <div style="display:flex; flex-direction:column; align-items:center;">
                    <div style="width:55px; height:55px; background-color:{l_color}; border-radius:50%; border:4px solid black;"></div>
                    {start_html}
                </div>
            </div>
        </div>
        """
        st.markdown(header_template, unsafe_allow_html=True)
        
        if c_data.get("note"):
            st.markdown(f"<div style='background-color:#e1f5fe; padding:15px; border-radius:10px; border-left:8px solid #03a9f4; margin-bottom:20px; color:black;'><strong>Note:</strong> {c_data['note']}<br><small>Updated: {c_data.get('timestamp')}</small></div>", unsafe_allow_html=True)
        
        tasks_query = db.collection("race_tasks").where("category", "==", cat).order_by("sort_order").stream()
        for task in tasks_query:
            td = task.to_dict()
            db_status = td.get("completed", False)
            cols = st.columns([1.2, 0.8, 6.0, 2]) if is_admin else st.columns([1.5, 8.5])
            with cols[0]:
                check = st.checkbox("", value=db_status, key=f"w_{task.id}_{db_status}", disabled=(db_status and not is_admin), label_visibility="collapsed")
                if check != db_status:
                    db.collection("race_tasks").document(task.id).update({"completed": check}); st.rerun()
            text_col = cols[2] if is_admin else cols[1]
            with text_col:
                icon = '✅' if db_status else '⏳'
                st.markdown(f"### {icon} {td['title']}")
                if td.get("notes"): st.info(f"📝 {td['notes']}")

show_tasks()
