import streamlit as st
from google.cloud import firestore
import json
from datetime import datetime
import pytz

# 1. Database Connection
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Firestore secrets not found.")
    st.stop()

# 2. Page Configuration
THIS_LOCATION = "Full Marathon Start" 
TIMEZONE = "US/Pacific"

st.set_page_config(page_title=f"{THIS_LOCATION} Checklist", layout="wide")

# --- CSS: Terminal Green & High-Vis Status ---
st.markdown(
    """
    <style>
    .stApp { background-color: #000000; color: #28a745; }
    h1, h2, h3, p, span, label, a { color: #28a745 !important; }
    
    .main-link { 
        text-decoration: none; font-weight: bold; border: 1px solid #28a745; 
        padding: 8px 20px; border-radius: 10px; display: inline-block; margin-bottom: 20px;
    }
    .main-link:hover { background-color: #28a745; color: black !important; }
    
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 2px solid #28a745 !important; 
        border-radius: 15px; padding: 25px !important; 
        margin-bottom: 15px !important; background-color: #0a0a0a;
    }
    
    [data-testid="stCheckbox"] { transform: scale(2.5); margin-left: 30px; }
    
    .status-box {
        text-align: center; padding: 20px; border-radius: 15px; margin-bottom: 30px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Helper Functions ---
def get_now():
    return datetime.now(pytz.timezone(TIMEZONE)).strftime("%I:%M %p")

# --- Ordered Milestone Logic ---
MILESTONES = [
    "Staff on Site",
    "Volunteers on Site",
    "Announcers on Site",
    "Timers on Site",
    "Set up of Start Line is Finished",
    "Full Marathon Start is 100% Ready",
    "Awaiting Start Go Ahead"
]

@st.fragment(run_every=5)
def render_checklist():
    st.markdown('<a href="/" target="_self" class="main-link">⬅ Return to Ops Dashboard</a>', unsafe_allow_html=True)
    st.title(f"🏁 {THIS_LOCATION}")
    
    doc_ref = db.collection("site_statuses").document("full_start")
    doc = doc_ref.get()
    data = doc.to_dict() if doc.exists else {}

    # Calculate Readiness
    completed_count = sum(1 for m in MILESTONES if data.get(m, False))
    is_ready = data.get("Awaiting Start Go Ahead", False)

    # Status Display
    if is_ready:
        st.markdown(f'<div class="status-box" style="background-color: #1b5e20; border: 3px solid #28a745;"><h1 style="color: white !important; margin:0;">GO FOR START</h1><p style="color: white !important;">Final Signal Received</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'
