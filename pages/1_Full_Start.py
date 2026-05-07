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

# --- CLEAN WHITE THEME: TOTAL INTERNAL BOX REMOVAL ---
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

    /* Milestone Container Box */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 1px solid #000000 !important;
        border-radius: 2px;
        padding: 8px 12px !important;
        margin-bottom: 4px !important;
        background: #FFFFFF;
        display: flex;
        align-items: center;
    }
    
    /* TARGETING THE INNER BOX DIRECTLY */
    /* This removes the border and background of the actual square box */
    [data-testid="stCheckbox"] div[role="checkbox"] {
        border: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        outline: none !important;
    }

    /* This removes the 'hover' and 'focus' states that re-draw the box */
    [data-testid="stCheckbox"] div[role="checkbox"]:hover,
    [data-testid="stCheckbox"] div[role="checkbox"]:focus,
    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] {
        border: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* This targets the internal div that Streamlit often uses for the widget's visual state */
    [data-testid="stCheckbox"] div[data-testid="stWidgetLabel"] div {
        border: none !important;
        background: transparent !important;
    }

    /* Scale only the red check icon */
    [data-testid="stCheckbox"] { 
        transform: scale(2.2); 
        margin-left: 5px;
    }
    
    /* Ensure the check icon (SVG) is visible even when the background is gone */
    [data-testid="stCheckbox"] svg {
        fill: #FF0000 !important; /* Forces the checkmark to remain red/visible */
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
        col1, col2 = st.columns([0.5, 9.5])
        with col1:
            val = st.checkbox("", value=checked,
