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

# --- CLEAN WHITE THEME: REMOVING INTERNAL CHECKBOX BORDERS ---
st.markdown("""
    <style>
    /* Base Page Styling */
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: "Times New Roman", Times, serif !important;
    }
    
    /* Standardized Text Size 16pt */
    p, span, label, b, .stMarkdown {
        font-size: 16pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
    }

    /* Titles at 24pt */
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
        padding: 6px 12px !important; /* Professional padding */
        margin-bottom: 4px !important;
        background: #FFFFFF;
        display: flex;
        align-items: center; /* Vertically Centers Checkbox & Text */
    }
    
    /* --- CSS TO REMOVE INNER BOX --- */
    /* Stripping all standard borders, backgrounds, and boxes from the inner widget */
    [data-testid="stCheckbox"] [role="checkbox"] {
        border: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
    }

    /* Scaling the Checkmark icon (Red X) itself */
    [data-testid="stCheckbox"] { 
        transform: scale(2.2); /* Adjust scale as needed to fill area */
        margin-left: 5px;
    }

    /* Hiding the native widget background entirely when unchecked */
    [data-testid="stCheckbox"] div[data-testid="stWidgetLabel"] div {
        background: transparent !important;
        border: none !important;
    }
    /* ------------------------------ */

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

    # Status Logic for Site Lead Header
    if emergency:
        st.markdown("<div class='status-header' style='background:#FF0000;'><h1>🛑 EMERGENCY STOP: RACE CANCELED</h1></div>", unsafe_allow_html=True)
    elif director_signal or note_active: 
        msg = data.get("custom_note", "Okay to start ontime") if note_active else "Okay to start ontime"
        st.markdown(f"<div class='status-header' style='background:#008000;'><h1>🚀 {msg}</h1></div>", unsafe_allow_html=True)
    elif count == 6:
        st.markdown("<div class='status-header' style='background:#FFD700; color:black;'><h1>⏳ WAITING FOR DIRECTOR</h1></div>", unsafe_allow_html=True)
    else:
        # Gray header while milestones are in progress
        st.markdown(f"<div class='status-header' style='background:#EEEEEE; color:black;'><h1>PREPARING ({count}/6)</h1></div>", unsafe_allow_html=True)

    st.divider()

    # Checklist Rendering
    for m in MILESTONES:
        checked = data.get(m, False)
        # Using columns to keep the checkmark aligned neatly to the left of the text
        col1, col2 = st.columns([0.4, 9.6]) # Checkbox gets small column to reduce gap
        with col1:
            # Render Checkbox
            val = st.checkbox("", value=checked, key=f"m_{m}")
            # If changed, update Database
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                # Auto-reset approval if a milestone is unchecked
                if not val: 
                    doc_ref.update({"director_signal": False, "note_active": False})
                st.rerun()
        with col2:
            # In-line text rendering with vertical offset to center with the scaled checkmark
            st.markdown(f"<div style='padding-top:10px;'><b>{m}</b></div>", unsafe_allow_html=True)

if __name__ == "__main__":
    render()
