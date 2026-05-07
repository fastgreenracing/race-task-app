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
    
    /* Navigation Link */
    .main-link { 
        text-decoration: none; font-weight: bold; border: 1px solid #28a745; 
        padding: 8px 20px; border-radius: 10px; display: inline-block; margin-bottom: 20px;
    }
    .main-link:hover { background-color: #28a745; color: black !important; }
    
    /* Checklist Item Box */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 2px solid #28a745 !important; 
        border-radius: 15px; padding: 25px !important; 
        margin-bottom: 15px !important; background-color: #0a0a0a;
    }
    
    /* Large Checkbox */
    [data-testid="stCheckbox"] { transform: scale(2.5); margin-left: 30px; }
    
    /* Status Headers */
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

# --- Milestone Logic ---
# These are the specific items you requested
MILESTONES = [
    "Staff on Site",
    "Volunteers on Site",
    "Announcers on Site",
    "Timers on Site",
    "Set up Start Line is Finished",
    "Full Marathon Start is 100% Set Up-awaiting Go Ahead",
]

@st.fragment(run_every=5)
def render_checklist():
    # Header & Nav
    st.markdown('<a href="/" target="_self" class="main-link">⬅ Return to Ops Dashboard</a>', unsafe_allow_html=True)
    st.title(f"🏁 {THIS_LOCATION}")
    
    # Fetch current statuses from Firestore
    # We store these under a specific doc for this location to keep it clean
    doc_ref = db.collection("site_statuses").document("full_start")
    doc = doc_ref.get()
    data = doc.to_dict() if doc.exists else {}

    # Calculate Readiness
    completed_count = sum(1 for m in MILESTONES if data.get(m, False))
    is_ready = completed_count == len(MILESTONES)

    # Big Visual Status for Site Lead
    if is_ready:
        st.markdown(f'<div class="status-box" style="background-color: #1b5e20; border: 3px solid #28a745;"><h1 style="color: white !important; margin:0;">GO FOR START</h1><p style="color: white !important;">All {len(MILESTONES)} Milestones Cleared</p></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-box" style="background-color: #4c0000; border: 3px solid #ff4b4b;"><h1 style="color: white !important; margin:0;">NO GO</h1><p style="color: white !important;">{completed_count} of {len(MILESTONES)} Milestones Ready</p></div>', unsafe_allow_html=True)

    st.divider()

    # Render Checklist
    for m in MILESTONES:
        is_checked = data.get(m, False)
        col_check, col_txt = st.columns([2, 8])
        
        with col_check:
            # Update Firestore immediately on toggle
            val = st.checkbox("", value=is_checked, key=f"m_{m}")
            if val != is_checked:
                doc_ref.set({m: val, f"{m}_time": get_now()}, merge=True)
                
                # Also update the main 'settings' status for the Ops Dashboard
                # This ensures your 'Master Page' turns Green automatically
                safe_id = THIS_LOCATION.replace("/", "_").replace(" ", "_")
                db.collection("settings").document(f"status_{safe_id}").set({
                    "completed": val if m == "Awaiting Start Signal" else (completed_count + 1 == len(MILESTONES)),
                    "timestamp": get_now()
                }, merge=True)
                
                st.rerun()

        with col_txt:
            if is_checked:
                st.markdown(f"## <span style='color: #1b5e20;'>{m}</span>", unsafe_allow_html=True)
                st.caption(f"Confirmed at {data.get(f'{m}_time')}")
            else:
                st.markdown(f"## {m}")

render_checklist()
