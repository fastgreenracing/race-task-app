import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Ops Master Dashboard", layout="wide")

# --- REFINED SLEEK UI CSS ---
st.markdown("""
    <style>
    /* Professional Deep Grey Gradient (No Pure Black) */
    .stApp {
        background: radial-gradient(circle at center, #23272a 0%, #17191b 100%);
        background-attachment: fixed;
        color: #e0e0e0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Technical Grid Overlay */
    .stApp::before {
        content: "";
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        background-image: radial-gradient(rgba(40, 167, 69, 0.08) 1px, transparent 1px);
        background-size: 35px 35px; pointer-events: none;
    }

    /* Standardized Font Size for general text (approx 16px) */
    p, span, label, .stMarkdown {
        font-size: 16px !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Exceptions: Titles and Ready Signals */
    h1 { font-size: 3rem !important; font-weight: 800 !important; color: #28a745 !important; }
    h2 { font-size: 2.2rem !important; color: #28a745 !important; }
    h3 { font-size: 1.5rem !important; color: #28a745 !important; }

    .status-card {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 30px;
        background: rgba(255, 255, 255, 0.04);
        backdrop-filter: blur(12px);
        text-align: center;
    }
    
    .emergency-btn button {
        background: rgba(255, 75, 75, 0.15) !important;
        color: #ff4b4b !important;
        border: 1px solid #ff4b4b !important;
    }
    </style>
    """, unsafe_allow_html=True)

@st.fragment(run_every=3)
def render_dashboard():
    st.title("🛰️ COMMAND CENTER")
    
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
        color, status_text, sub_text = "#aaaaaa", "PREPARING", f"{count}/6 Milestones Logged"

    col_card, col_actions = st.columns([1, 1])
    
    with col_card:
        st.markdown(f"""
            <div class="status-card" style="border-top: 6px solid {color};">
                <p style="opacity: 0.6; font-size: 14px; letter-spacing: 2px; font-weight: 800; color: #28a745 !important;">SECTOR: FULL START</p>
                <h1 style="color: {color} !important; font-size: 4rem; margin: 10px 0;">{status_text}</h1>
                <p style="font-size: 16px; opacity: 0.9;">{sub_text}</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col_actions:
        if count == 6 and not (director_approved or director_note_active or emergency_stop):
            st.subheader("Decision Authority")
            btn1, btn2 = st.columns(2)
            with btn
