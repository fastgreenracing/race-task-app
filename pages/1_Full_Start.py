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

# 2. Configuration - CRITICAL: This must match your Admin Category Name exactly
# If your category is just "Full Start", change this line to: THIS_LOCATION = "Full Start"
THIS_LOCATION = "Full Marathon Start"
TIMEZONE = "US/Pacific"

st.set_page_config(page_title=f"{THIS_LOCATION} Checklist", layout="wide")

# --- CSS: Terminal Theme ---
st.markdown(
    """
    <style>
    .stApp { background-color: #000000; color: #28a745; }
    h1, h2, h3, p, span, label, a { color: #28a745 !important; }
    .main-link { 
        text-decoration: none; font-weight: bold; border: 1px solid #28a745; 
        padding: 8px 20px; border-radius: 10px; display: inline-block; margin-bottom: 20px;
    }
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 2px solid #28a745 !important; 
        border-radius: 15px; padding: 25px !important; 
        margin-bottom: 15px !important; background-color: #0a0a0a;
    }
    [data-testid="stCheckbox"] { transform: scale(2.5); margin-left: 30px; }
    .status-box { text-align: center; padding: 20px; border-radius: 15px; margin-bottom: 30px; }
    </style>
    """,
    unsafe_allow_html=True
)

def get_now():
    return datetime.now(pytz.timezone(TIMEZONE)).strftime("%I:%M %p")

# --- Ordered Milestones ---
MILESTONES = [
    "Staff on Site",
    "Volunteers on Site",
    "Announcers on Site",
    "Timers on Site",
    "Set up of Start Line is Finished",
    "Full Marathon Start is 100%-awaiting Go Ahead",
]

@st.fragment(run_every=5)
def render_checklist():
    st.markdown('<a href="/" target="_self" class="main-link">⬅ Return to Ops Dashboard</a>', unsafe_allow_html=True)
    st.title(f"🏁 {THIS_LOCATION}")
    
    # Get current status from site-specific collection
    doc_ref = db.collection("site_statuses").document("full_start")
    doc = doc_ref.get()
    data = doc.to_dict() if doc.exists else {}

    # Logic: Only Ready if ALL milestones are True
    completed_count = sum(1 for m in MILESTONES if data.get(m, False))
    is_fully_ready = (completed_count == len(MILESTONES))

    # 🚦 Site Lead Visual Status
    if is_fully_ready:
        st.markdown('<div class="status-box" style="background-color: #1b5e20; border: 3px solid #28a745;"><h1>GO FOR START</h1></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-box" style="background-color: #4c0000; border: 3px solid #ff4b4b;"><h1>NO GO</h1><p>{completed_count} / {len(MILESTONES)} Milestones</p></div>', unsafe_allow_html=True)

    st.divider()

    # Render Checklist
    for m in MILESTONES:
        is_checked = data.get(m, False)
        col_check, col_txt = st.columns([2, 8])
        
        with col_check:
            val = st.checkbox("", value=is_checked, key=f"m_{m}")
            if val != is_checked:
                # 1. Update the milestone data
                new_data = {m: val, f"{m}_time": get_now() if val else ""}
                doc_ref.set(new_data, merge=True)
                
                # 2. Recalculate total readiness for the Master Dashboard
                # We fetch fresh data to be sure
                updated_data = doc_ref.get().to_dict() or {}
                new_total = sum(1 for milestone in MILESTONES if updated_data.get(milestone, False))
                master_ready = (new_total == len(MILESTONES))
                
                # 3. Force update to the Master Dashboard status record
                safe_id = THIS_LOCATION.replace("/", "_").replace(" ", "_")
                db.collection("settings").document(f"status_{safe_id}").set({
                    "completed": master_ready,
                    "timestamp": get_now()
                }, merge=True)
                
                st.rerun()

        with col_txt:
            if is_checked:
                st.markdown(f"## <span style='color: #1b5e20;'>{m}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"## {m}")

render_checklist()
