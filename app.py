import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Ops Master Dashboard", layout="wide")

# --- SLEEK MODERN CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #28a745; font-family: 'Inter', sans-serif; }
    h1, h2, h3, p, span, label { color: #28a745 !important; }
    
    /* Sleek Dashboard Cards */
    .status-card {
        border: 1px solid rgba(40, 167, 69, 0.3);
        border-radius: 20px;
        padding: 30px;
        background: linear-gradient(145deg, #0a0a0a, #111111);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        text-align: center;
        transition: all 0.3s ease;
    }
    
    /* Professional Buttons */
    .stButton>button {
        border-radius: 12px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
        transition: all 0.2s;
    }
    
    /* Emergency Style */
    .emergency-btn button {
        background-color: #ff4b4b !important;
        color: white !important;
        border: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.fragment(run_every=3)
def render_dashboard():
    st.title("🛰️ RACE OPERATIONS COMMAND")
    
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    m_list = ["Staff on Site", "Volunteers on Site", "Announcers on Site", "Timers on Site", "Set up of Start Line is Finished", "Full Marathon Start is 100%-awaiting Go Ahead"]
    count = sum(1 for m in m_list if data.get(m) == True)
    
    director_approved = data.get("director_signal", False)
    director_note_active = data.get("note_active", False)
    emergency_stop = data.get("emergency_cancel", False)

    # UI Logic for Status Card
    if emergency_stop:
        color, status_text, sub_text = "#ff4b4b", "CANCELED", "Emergency Stop Active"
    elif director_approved or director_note_active:
        color, status_text = "#28a745", "SIGNAL SENT"
        sub_text = data.get("custom_note", "Okay to start ontime") if director_note_active else "Okay to start ontime"
    elif count == 6:
        color, status_text, sub_text = "#ffc107", "PENDING", "Waiting for Approval"
    else:
        color, status_text, sub_text = "#555555", "IN PROGRESS", f"{count}/6 Milestones Ready"

    col_card, col_actions = st.columns([1, 1])
    
    with col_card:
        st.markdown(f"""
            <div class="status-card" style="border-top: 5px solid {color};">
                <p style="opacity: 0.5; font-size: 0.8rem; letter-spacing: 2px;">SECTOR: FULL MARATHON START</p>
                <h1 style="color: {color} !important; font-size: 4rem; margin: 10px 0;">{status_text}</h1>
                <p style="font-size: 1.2rem; font-weight: 300;">{sub_text}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col_actions:
        if count == 6 and not (director_approved or director_note_active or emergency_stop):
            st.subheader("Decision Authority")
            btn1, btn2 = st.columns(2)
            with btn1:
                if st.button("🚀 APPROVE START", use_container_width=True):
                    doc_ref.update({"director_signal": True, "note_active": False, "emergency_cancel": False})
                    st.rerun()
            with btn2:
                note_text = st.text_input("Coordinator Note:", placeholder="Optional instructions...")
                if st.button("📝 SEND WITH NOTE", use_container_width=True):
                    if note_text:
                        doc_ref.update({"director_signal": False, "note_active": True, "custom_note": note_text, "emergency_cancel": False})
                        st.rerun()
        
        st.divider()
        
        # Reset and Emergency Actions
        if director_approved or director_note_active or emergency_stop:
            if st.button("🔄 CLEAR SIGNALS / RESET", use_container_width=True):
                doc_ref.update({"director_signal": False, "note_active": False, "custom_note": "", "emergency_cancel": False})
                st.rerun()
        
        # New Emergency Cancellation Button
        st.markdown('<div class="emergency-btn">', unsafe_allow_html=True)
        if st.button("⚠️ EMERGENCY CANCELLATION", use_container_width=True):
            doc_ref.update({"director_signal": False, "note_active": False, "emergency_cancel": True, "custom_note": "RACE CANCELED - STOP ALL OPERATIONS"})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

render_dashboard()
