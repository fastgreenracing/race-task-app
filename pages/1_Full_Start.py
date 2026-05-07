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

# 2. Configuration
THIS_LOCATION = "Full Marathon Start"
TIMEZONE = "US/Pacific"

st.set_page_config(page_title=f"{THIS_LOCATION} Checklist", layout="wide")

# --- CSS: Terminal Theme ---
st.markdown("""
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
    """, unsafe_allow_html=True)

def get_now():
    return datetime.now(pytz.timezone(TIMEZONE)).strftime("%I:%M %p")

# --- THE DEFINITIVE MILESTONE LIST ---
MILESTONES = [
    "Staff on Site",
    "Volunteers on Site",
    "Announcers on Site",
    "Timers on Site",
    "Set up of Start Line is Finished",
    "Full Marathon Start is 100%-awaiting Go Ahead"
]

@st.fragment(run_every=5)
def render_checklist():
    st.markdown('<a href="/" target="_self" class="main-link">⬅ Return to Ops Dashboard</a>', unsafe_allow_html=True)
    st.title(f"🏁 {THIS_LOCATION}")
    
    doc_ref = db.collection("site_statuses").document("full_start")
    doc = doc_ref.get()
    data = doc.to_dict() if doc.exists else {}

    # STRICT CALCULATION: Total count of checked milestones
    completed_count = sum(1 for m in MILESTONES if data.get(m, False))
    total_needed = len(MILESTONES)
    is_fully_ready = (completed_count == total_needed)

    # Site Lead Banner
    if is_fully_ready:
        st.markdown('<div class="status-box" style="background-color: #1b5e20; border: 3px solid #28a745;"><h1>GO FOR START</h1></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-box" style="background-color: #4c0000; border: 3px solid #ff4b4b;"><h1>NO GO</h1><p>{completed_count} / {total_needed} Milestones Cleared</p></div>', unsafe_allow_html=True)

    st.divider()

    for m in MILESTONES:
        is_checked = data.get(m, False)
        col_check, col_txt = st.columns([2, 8])
        
        with col_check:
            val = st.checkbox("", value=is_checked, key=f"m_{m}")
            if val != is_checked:
                # Update individual item
                doc_ref.set({m: val, f"{m}_time": get_now() if val else ""}, merge=True)
                
                # RE-FETCH AND RE-CALCULATE TO PREVENT "GHOST" GO SIGNALS
                fresh_data = doc_ref.get().to_dict() or {}
                fresh_count = sum(1 for milestone in MILESTONES if fresh_data.get(milestone, False))
                
                # This boolean is what the Master Dashboard reads
                master_ready_signal = (fresh_count == len(MILESTONES))
                
                safe_id = THIS_LOCATION.replace("/", "_").replace(" ", "_")
                db.collection("settings").document(f"status_{safe_id}").set({
                    "completed": master_ready_signal,
                    "timestamp": get_now()
                }, merge=True)
                
                st.rerun()

        with col_txt:
            if is_checked:
                st.markdown(f"## <span style='color: #1b5e20;'>{m}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"## {m}")

render_checklist()
