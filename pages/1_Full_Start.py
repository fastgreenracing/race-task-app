import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Firestore secrets not found.")
    st.stop()

st.set_page_config(page_title="Full Start Coordinator", layout="wide")

# --- REFINED ALIGNMENT: CENTERED TEXT & LEFT-FLUSH CHECKMARK ---
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: "Times New Roman", Times, serif !important;
    }
    
    p, span, label, b, .stMarkdown {
        font-size: 16pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
    }

    h1 {
        font-size: 24pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* 1. THE MAIN MILESTONE CONTAINER */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 1px solid #000000 !important;
        border-radius: 2px;
        padding: 0px 10px !important; /* Minimal vertical padding for tighter fit */
        margin-bottom: 4px !important;
        background: #FFFFFF;
        display: flex;
        align-items: center; /* PERFECT VERTICAL CENTERING */
        overflow: visible !important;
        min-height: 50px; /* Ensures a consistent height for the text row */
    }
    
    /* 2. THE FLOATING CHECKMARK */
    [data-testid="stCheckbox"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 1px !important; /* Effectively invisible footprint */
        height: 1px !important;
        overflow: visible !important;
        /* Pulls the checkmark left and centers it vertically */
        transform: scale(2.6) translateX(-2px) translateY(-2px); 
        z-index: 99;
    }

    /* 3. STRIP ALL INTERNAL BOX ARTIFACTS */
    [data-testid="stCheckbox"] [role="checkbox"],
    [data-testid="stCheckbox"] div[data-testid="stWidgetLabel"] div {
        border: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
    }

    [data-testid="stCheckbox"] svg {
        fill: #FF0000 !important;
    }

    .status-header {
        padding: 25px;
        border: 2px solid #000000;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

MILESTONES = [
    "Staff on Site", "Volunteers on Site", "Announcers on Site", 
    "Timers on Site", "Set up of Start Line is Finished", 
    "Full Marathon Start is 100%-awaiting Go Ahead"
]

@st.fragment(run_every=2)
def render():
    st.title("Full Marathon Start Checklist")
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    count = sum(1 for m in MILESTONES if data.get(m) == True)
    director_signal = data.get("director_signal", False)
    note_active = data.get("note_active", False)
    emergency = data.get("emergency_cancel", False)

    if emergency:
        st.markdown("<div class='status-header' style='background:#FF0000;'><h1>🛑 EMERGENCY STOP</h1></div>", unsafe_allow_html=True)
    elif director_signal or note_active: 
        msg = data.get("custom_note", "Okay to start ontime") if note_active else "Okay to start ontime"
        st.markdown(f"<div class='status-header' style='background:#008000;'><h1>🚀 {msg}</h1></div>", unsafe_allow_html=True)
    elif count == 6:
        st.markdown("<div class='status-header' style='background:#FFD700; color:black;'><h1>⏳ WAITING FOR DIRECTOR</h1></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='status-header' style='background:#EEEEEE; color:black;'><h1>PREPARING ({count}/6)</h1></div>", unsafe_allow_html=True)

    st.divider()

    for m in MILESTONES:
        checked = data.get(m, False)
        # Ratio changed to give more room to text and keep the checkbox anchored far left
        col1, col2 = st.columns
