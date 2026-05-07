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

# --- THE "GHOST-KILLER" THEME ---
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
        padding: 0px 10px !important;
        margin-bottom: 4px !important;
        background: #FFFFFF;
        display: flex;
        align-items: center; 
        min-height: 55px;
        overflow: visible !important;
    }
    
    /* 2. THE TOTAL WIDGET HIDE */
    [data-testid="stCheckbox"] {
        visibility: hidden !important; /* Hides the base box and label completely */
        width: 1px !important;
        height: 1px !important;
        overflow: visible !important;
    }

    /* 3. REVEAL ONLY THE CHECKMARK ICON */
    [data-testid="stCheckbox"] svg {
        visibility: visible !important; /* Overrides the parent hidden state */
        fill: #FF0000 !important;
        transform: scale(3.5) translateX(-2px); /* Makes it large and positions it */
        z-index: 999;
    }

    /* 4. CLEAN UP RESIDUAL BORDERS */
    [data-testid="stCheckbox"] div[role="checkbox"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
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
        # Using a very tiny column for the "invisible" widget anchor
        col1, col2 = st.columns([0.05, 9.95]) 
        with col1:
            val = st.checkbox("", value=checked, key=f"m_{m}")
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                if not val: 
                    doc_ref.update({"director_signal": False, "note_active": False})
                st.rerun()
        with col2:
            st.markdown(f"<div style='margin-left:55px; padding-top:2px;'><b>{m}</b></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    render()
