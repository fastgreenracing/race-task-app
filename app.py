import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Ops Master Dashboard", layout="wide")

# --- CSS: Terminal Theme ---
st.markdown("<style>.stApp { background-color: #000000; color: #28a745; } h1,h2,h3,p,span,label { color: #28a745 !important; } .status-card { border: 2px solid #28a745; border-radius: 15px; padding: 20px; background-color: #0a0a0a; text-align: center; }</style>", unsafe_allow_html=True)

@st.fragment(run_every=3)
def render_dashboard():
    st.title("🎛️ Ops Master Dashboard")
    
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    m_list = ["Staff on Site", "Volunteers on Site", "Announcers on Site", "Timers on Site", "Set up of Start Line is Finished", "Full Marathon Start is 100%-awaiting Go Ahead"]
    count = sum(1 for m in m_list if data.get(m) == True)
    director_approved = data.get("director_signal", False)
    director_note_active = data.get("note_active", False)

    # UI Logic for Status Card
    if director_approved or director_note_active:
        color, status_text = "#28a745", "SIGNAL SENT"
        sub_text = data.get("custom_note", "Okay to start ontime") if director_note_active else "Okay to start ontime"
    elif count == 6:
        color, status_text, sub_text = "#ffc107", "WAITING FOR APPROVAL", "Site Lead is Ready"
    else:
        color, status_text, sub_text = "#ff4b4b", "NOT READY", f"{count}/6 Milestones"

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"""<div class="status-card" style="border-color: {color};">
            <h3>Full Marathon Start</h3>
            <h1 style="color: {color} !important;">{status_text}</h1>
            <p style="font-weight: bold;">{sub_text}</p></div>""", unsafe_allow_html=True)
    
    with col2:
        if count == 6 and not (director_approved or director_note_active):
            st.write("### Authorize Start")
            btn1, btn2 = st.columns(2)
            
            with btn1:
                if st.button("🚀 Approve Start", use_container_width=True):
                    doc_ref.update({"director_signal": True, "note_active": False})
                    st.rerun()
            
            with btn2:
                # Text input for the custom note
                note_text = st.text_input("Enter Instruction:", placeholder="e.g. Hold 5 mins for train")
                if st.button("📝 See Notes", use_container_width=True):
                    if note_text:
                        doc_ref.update({"director_signal": False, "note_active": True, "custom_note": note_text})
                        st.rerun()
                    else:
                        st.warning("Type a note first")
                        
        elif director_approved or director_note_active:
            if st.button("🛑 RESET (Emergency Hold)", use_container_width=True):
                doc_ref.update({"director_signal": False, "note_active": False, "custom_note": ""})
                st.rerun()

render_dashboard()
