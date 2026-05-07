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
    
    # 1. Check Site Lead Progress
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    m_list = ["Staff on Site", "Volunteers on Site", "Announcers on Site", "Timers on Site", "Set up of Start Line is Finished", "Full Marathon Start is 100%-awaiting Go Ahead"]
    count = sum(1 for m in m_list if data.get(m) == True)
    
    # 2. Check if Director has approved
    director_approved = data.get("director_signal", False)

    # UI Logic for Director
    if director_approved:
        color, status_text, sub_text = "#28a745", "START SIGNAL SENT", "Okay to start ontime"
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
        if count == 6 and not director_approved:
            st.write("### Authorize Start")
            if st.button("🚀 APPROVE START", use_container_width=True):
                doc_ref.update({"director_signal": True})
                st.rerun()
        elif director_approved:
            if st.button("🛑 RESET (Emergency Hold)", use_container_width=True):
                doc_ref.update({"director_signal": False})
                st.rerun()

render_dashboard()
