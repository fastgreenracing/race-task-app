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

# --- THE 1PX THEME ---
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: "Times New Roman", Times, serif !important;
    }
    
    h1 {
        font-size: 24pt !important;
        font-family: "Times New Roman", Times, serif !important;
        font-weight: bold !important;
    }

    /* Milestone Row */
    .milestone-row {
        display: flex;
        align-items: center; 
        height: 100px; 
        border-bottom: 3px solid #000000;
        margin: 0 !important;
        padding: 0 !important;
        background-color: transparent;
    }

    .milestone-text {
        font-size: 24pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
        font-weight: bold !important;
        margin-left: 20px; /* Reduced margin since box is tiny */
        display: flex;
        align-items: center;
        height: 100%;
        line-height: 1.0 !important;
    }

    /* 1. SHRINK THE CHECKBOX TO 1PX */
    [data-testid="stCheckbox"] div[role="checkbox"] {
        background-color: #000000 !important;
        border: none !important;
        opacity: 1 !important; 
        width: 1px !important;  
        height: 1px !important; 
        cursor: pointer !important;
        position: relative;
    }

    /* 2. CUSTOM RED CHECKMARK (Shrunk/Hidden to match) */
    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::after {
        content: '' !important;
        position: absolute;
        visibility: visible !important;
        left: 0px; 
        top: 0px; 
        width: 15px; 
        height: 30px; 
        border: solid #FF0000;
        border-width: 0 5px 5px 0; 
        transform: rotate(45deg);
    }

    /* Hide the default Streamlit check icon */
    [data-testid="stCheckbox"] svg {
        display: none !important;
    }

    /* Centering the tiny widget in the 100px row */
    [data-testid="stCheckbox"] {
        margin: 0 !important;
        padding: 0 !important;
        height: 100px !important;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 40px !important; /* Keep a small hit zone width */
    }

    .status-header {
        padding: 25px;
        border: 2px solid #000000;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 20px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

MILESTONES = [
    "Staff on Site",
    "Volunteers on Site",
    "Announcers on Site",
    "Timers on Site",
    "Set up of Start Line is Finished",
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
        
        st.markdown('<div class="milestone-row">', unsafe_allow_html=True)
        col_check, col_text = st.columns([0.05, 9.95])
        
        with col_check:
            val = st.checkbox("", value=checked, key=f"tiny_dot_{m}")
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                if not val: 
                    doc_ref.update({"director_signal": False, "note_active": False})
                st.rerun()
        
        with col_text:
            st.markdown(f'<div class="milestone-text">{m}</div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
