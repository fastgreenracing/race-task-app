import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Ops Master Dashboard", layout="wide")

# --- CLEAN WHITE THEME (TIMES NEW ROMAN) ---
st.markdown("""
    <style>
    /* Base Page Styling */
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: "Times New Roman", Times, serif !important;
    }

    /* Standardized Text Size 16pt */
    p, span, label, .stMarkdown, .stButton button, input {
        font-size: 16pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
    }

    /* Titles at 24pt */
    h1, h2 {
        font-size: 24pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* Card Styling for Visibility on White */
    .status-card {
        border: 2px solid #000000;
        border-radius: 10px;
        padding: 25px;
        background-color: #F9F9F9;
        text-align: center;
        margin-bottom: 20px;
    }

    /* Button Formatting */
    .stButton>button {
        border: 1px solid #000000 !important;
        background-color: #EEEEEE !important;
        color: #000000 !important;
        border-radius: 5px !important;
    }
    
    .emergency-btn button {
        background-color: #FF0000 !important;
        color: #FFFFFF !important;
        border: 2px solid #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.fragment(run_every=3)
def render_dashboard():
    st.title("Ops Command: Master Dashboard")
    
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    m_list = ["Staff on Site", "Volunteers on Site", "Announcers on Site", "Timers on Site", "Set up of Start Line is Finished", "Full Marathon Start is 100%-awaiting Go Ahead"]
    count = sum(1 for m in m_list if data.get(m) == True)
    
    director_approved = data.get("director_signal", False)
    director_note_active = data.get("note_active", False)
    emergency_stop = data.get("emergency_cancel", False)

    # Status Logic
    if emergency_stop:
        color, status_text, sub_text = "#FF0000", "CRITICAL STOP", "Race Canceled"
    elif director_approved or director_note_active:
        color, status_text = "#008000", "AUTHORIZED"
        sub_text = data.get("custom_note", "Start on Time") if director_note_active else "Start on Time"
    elif count == 6:
        color, status_text, sub_text = "#FFD700", "PENDING", "Waiting for Signal"
    else:
        color, status_text, sub_text = "#808080", "PREPARING", f"{count}/6 Milestones"

    col_card, col_actions = st.columns([1, 1])
    
    with col_card:
        st.markdown(f"""
            <div class="status-card" style="border-top: 10px solid {color};">
                <p style="font-weight: bold; text-decoration: underline;">Full Marathon Start</p>
                <h1 style="color: {color} !important; font-size: 36pt !important;">{status_text}</h1>
                <p>{sub_text}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col_actions:
        if count == 6 and not (director_approved or director_note_active or emergency_stop):
            st.markdown("<b>Decision Authority</b>", unsafe_allow_html=True)
            if st.button("Authorize Start", use_container_width=True):
                doc_ref.update({"director_signal": True, "note_active": False, "emergency_cancel": False})
                st.rerun()
            
            note_text = st.text_input("Coordinator Note:", placeholder="Optional...")
            if st.button("Send with Note", use_container_width=True):
                if note_text:
                    doc_ref.update({"director_signal": False, "note_active": True, "custom_note": note_text, "emergency_cancel": False})
                    st.rerun()
        
        st.divider()
        if director_approved or director_note_active or emergency_stop:
            if st.button("System Reset", use_container_width=True):
                doc_ref.update({"director_signal": False, "note_active": False, "custom_note": "", "emergency_cancel": False})
                st.rerun()
        
        st.markdown('<div class="emergency-btn">', unsafe_allow_html=True)
        if st.button("Emergency Cancellation", use_container_width=True):
            doc_ref.update({"director_signal": False, "note_active": False, "emergency_cancel": True, "custom_note": "RACE CANCELED"})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

render_dashboard()
