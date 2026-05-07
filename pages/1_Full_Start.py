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

# --- PRECISION GRID ALIGNMENT THEME ---
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
        color: #000000 !important;
    }

    /* Individual Milestone Grid Box */
    .milestone-grid {
        border: 1px solid #000000;
        border-radius: 2px;
        padding: 5px 15px !important;
        margin-bottom: 10px;
        display: flex;
        align-items: center; /* Vertically centers the checkbox column and text column */
        min-height: 70px;
        background-color: #FFFFFF;
    }

    /* Milestone Text Styling */
    .milestone-text {
        font-size: 16pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
        font-weight: bold !important;
        margin-left: 50px; /* Space to prevent text overlap with the large check */
        padding-top: 2px;
    }

    /* Invisible clickable area for native checkbox */
    [data-testid="stCheckbox"] div[role="checkbox"] {
        opacity: 0 !important;
        width: 50px !important;
        height: 50px !important;
        cursor: pointer !important;
    }

    /* Large Floating Red Checkmark */
    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"]::after {
        content: '' !important;
        position: absolute;
        visibility: visible !important;
        opacity: 1 !important;
        left: 10px;
        top: -5px; /* Adjusted to center the check within the taller grid */
        width: 20px;
        height: 40px;
        border: solid #FF0000;
        border-width: 0 8px 8px 0;
        transform: rotate(45deg);
    }

    /* Cleanup Native Streamlit Overlays */
    [data-testid="stCheckbox"] svg {
        display: none !important;
    }
    
    [data-testid="stCheckbox"] {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
        display: flex;
        align-items: center;
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

    # Status Logic Header
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

    # Rendering logic: Checkbox and Verbiage INSIDE the Grid
    for m in MILESTONES:
        checked = data.get(m, False)
        
        # This div wraps the columns, ensuring the border goes around both
        st.markdown('<div class="milestone-grid">', unsafe_allow_html=True)
        
        col_check, col_text = st.columns([0.1, 9.9])
        
        with col_check:
            val = st.checkbox("", value=checked, key=f"grid_in_{m}")
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                if not val: 
                    doc_ref.update({"director_signal": False, "note_active": False})
                st.rerun()
        
        with col_text:
            # Displays the verbiage inside the second column of the grid
            st.markdown(f'<div class="milestone-text">{m}</div>', unsafe_allow_html=True)
            
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
