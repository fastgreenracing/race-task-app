import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Ops Master Dashboard", layout="wide")

# --- SLEEK TECH GRADIENT CSS ---
st.markdown("""
    <style>
    /* Professional Deep Charcoal Gradient Background */
    .stApp {
        background: radial-gradient(circle at top left, #1a1c1e, #0f1011);
        background-attachment: fixed;
        color: #e0e0e0;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Subtle Grid Overlay for "Technical" look */
    .stApp::before {
        content: "";
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background-image: radial-gradient(rgba(40, 167, 69, 0.05) 1px, transparent 1px);
        background-size: 30px 30px;
        pointer-events: none;
    }

    h1, h2, h3 { 
        color: #28a745 !important; 
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }

    /* Glassmorphism Dashboard Cards */
    .status-card {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 24px;
        padding: 35px;
        background: rgba(255, 255, 255, 0.03);
        backdrop-filter: blur(10px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        text-align: center;
    }

    /* Sleek Action Buttons */
    .stButton>button {
        border-radius: 12px !important;
        border: 1px solid rgba(40, 167, 69, 0.3) !important;
        background: rgba(40, 167, 69, 0.1) !important;
        color: #28a745 !important;
        font-weight: 600 !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: rgba(40, 167, 69, 0.2) !important;
        border-color: #28a745 !important;
        transform: translateY(-2px);
    }
    
    /* Emergency Style Override */
    .emergency-btn button {
        background: rgba(255, 75, 75, 0.1) !important;
        color: #ff4b4b !important;
        border-color: rgba(255, 75, 75, 0.3) !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.fragment(run_every=3)
def render_dashboard():
    st.title("🛰️ COMMAND CENTER | MASTER OPS")
    
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    m_list = ["Staff on Site", "Volunteers on Site", "Announcers on Site", "Timers on Site", "Set up of Start Line is Finished", "Full Marathon Start is 100%-awaiting Go Ahead"]
    count = sum(1 for m in m_list if data.get(m) == True)
    
    director_approved = data.get("director_signal", False)
    director_note_active = data.get("note_active", False)
    emergency_stop = data.get("emergency_cancel", False)

    if emergency_stop:
        color, status_text, sub_text = "#ff4b4b", "CRITICAL", "Emergency Stop Initiated"
    elif director_approved or director_note_active:
        color, status_text = "#28a745", "AUTHORIZED"
        sub_text = data.get("custom_note", "Proceeding on Schedule") if director_note_active else "Okay to start ontime"
    elif count == 6:
        color, status_text, sub_text = "#ffc107", "READY", "Waiting for Director Signal"
    else:
        color, status_text, sub_text = "#777777", "PREPARING", f"{count}/6 Milestones Logged"

    col_card, col_actions = st.columns([1, 1])
    
    with col_card:
        st.markdown(f"""
            <div class="status-card" style="border-top: 6px solid {color};">
                <p style="opacity: 0.5; font-size: 0.7rem; letter-spacing: 3px; font-weight: 800;">SECTOR: FULL START</p>
                <h1 style="color: {color} !important; font-size: 4.5rem; margin: 15px 0;">{status_text}</h1>
                <p style="font-size: 1.1rem; opacity: 0.8; letter-spacing: 0.5px;">{sub_text}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col_actions:
        if count == 6 and not (director_approved or director_note_active or emergency_stop):
            st.subheader("Decision Authority")
            btn1, btn2 = st.columns(2)
            with btn1:
                if st.button("🚀 AUTHORIZE START", use_container_width=True):
                    doc_ref.update({"director_signal": True, "note_active": False, "emergency_cancel": False})
                    st.rerun()
            with btn2:
                note_text = st.text_input("Coordinator Instruction:", placeholder="Add timing notes...")
                if st.button("📝 ISSUE WITH NOTE", use_container_width=True):
                    if note_text:
                        doc_ref.update({"director_signal": False, "note_active": True, "custom_note": note_text, "emergency_cancel": False})
                        st.rerun()
        
        st.divider()
        if director_approved or director_note_active or emergency_stop:
            if st.button("🔄 SYSTEM RESET", use_container_width=True):
                doc_ref.update({"director_signal": False, "note_active": False, "custom_note": "", "emergency_cancel": False})
                st.rerun()
        
        st.markdown('<div class="emergency-btn">', unsafe_allow_html=True)
        if st.button("⚠️ EMERGENCY CANCELLATION", use_container_width=True):
            doc_ref.update({"director_signal": False, "note_active": False, "emergency_cancel": True, "custom_note": "RACE CANCELED - ALL HANDS STOP"})
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

render_dashboard()
