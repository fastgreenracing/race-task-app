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

# --- CLEAN BULLET CHECKLIST THEME ---
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: "Times New Roman", Times, serif !important;
    }
    
    /* Title Styling (24pt) */
    h1 {
        font-size: 24pt !important;
        font-family: "Times New Roman", Times, serif !important;
        font-weight: bold !important;
        margin-bottom: 20px;
    }

    /* Checklist Item Styling (16pt) */
    [data-testid="stCheckbox"] label p {
        font-size: 16pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
        font-weight: bold !important;
        padding-left: 10px;
    }

    /* Entire Checklist Container */
    .checklist-container {
        border: 1px solid #000000;
        padding: 20px;
        border-radius: 4px;
        background-color: #FFFFFF;
    }

    /* Remove the 'box' around the native checkbox and scale the checkmark */
    [data-testid="stCheckbox"] [role="checkbox"] {
        border: none !important;
        background: transparent !important;
        box-shadow: none !important;
    }

    [data-testid="stCheckbox"] svg {
        fill: #FF0000 !important; /* Keep the red checkmark */
        transform: scale(2.5);
    }

    .status-header {
        padding: 25px;
        border: 2px solid #000000;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 25px;
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
    
    # Firestore Sync
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

    # Render the Bulleted Checklist
    st.markdown('<div class="checklist-container">', unsafe_allow_html=True)
    
    for m in MILESTONES:
        checked = data.get(m, False)
        
        # We use a simple checkbox here; the CSS makes it look like a bulleted item
        val = st.checkbox(m, value=checked, key=f"bullet_{m}")
        
        if val != checked:
            doc_ref.set({m: val}, merge=True)
            # Logic: If any box is unchecked, the director's green light is reset
            if not val: 
                doc_ref.update({"director_signal": False, "note_active": False})
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    render()
