import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Full Start Site Lead", layout="wide")
st.markdown("<style>.stApp { background-color: #000000; color: #28a745; } h1,h2,h3,p,label { color: #28a745 !important; } [data-testid='stCheckbox'] { transform: scale(2.5); margin-left: 30px; }</style>", unsafe_allow_html=True)

MILESTONES = ["Staff on Site", "Volunteers on Site", "Announcers on Site", "Timers on Site", "Set up of Start Line is Finished", "Full Marathon Start is 100%-awaiting Go Ahead"]

@st.fragment(run_every=2)
def render():
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data = doc_ref.get().to_dict() or {}
    
    count = sum(1 for m in MILESTONES if data.get(m) == True)
    director_signal = data.get("director_signal", False)

    # VISUAL HEADER LOGIC
    if director_signal:
        st.markdown("<div style='background:#1b5e20; padding:30px; border-radius:15px; text-align:center; border: 5px solid #28a745;'><h1>🚀 START SIGNAL RECEIVED: GO GO GO!</h1></div>", unsafe_allow_html=True)
    elif count == 6:
        st.markdown("<div style='background:#5a4100; padding:30px; border-radius:15px; text-align:center; border: 2px solid #ffc107;'><h1>⏳ WAITING FOR DIRECTOR APPROVAL...</h1></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='background:#4c0000; padding:20px; border-radius:15px; text-align:center;'><h1>NO GO ({count}/6)</h1></div>", unsafe_allow_html=True)

    st.divider()
    for m in MILESTONES:
        checked = data.get(m, False)
        col1, col2 = st.columns([2, 8])
        with col1:
            val = st.checkbox("", value=checked, key=f"m_{m}")
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                # If they uncheck something, we should probably pull the director signal too
                if not val: doc_ref.update({"director_signal": False})
                st.rerun()
        with col2: st.markdown(f"## {m}")

render()
