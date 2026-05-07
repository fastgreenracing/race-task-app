import streamlit as st
from google.cloud import firestore
import json
from datetime import datetime
import pytz

# 1. Database Connection
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Firestore secrets not found.")
    st.stop()

THIS_LOCATION = "Full Marathon Start"
TIMEZONE = "US/Pacific"
st.set_page_config(page_title=THIS_LOCATION, layout="wide")

st.markdown("<style>.stApp { background-color: #000000; color: #28a745; } h1,h2,h3,p,label { color: #28a745 !important; } [data-testid='stCheckbox'] { transform: scale(2.5); margin-left: 30px; }</style>", unsafe_allow_html=True)

MILESTONES = [
    "Staff on Site", "Volunteers on Site", "Announcers on Site", 
    "Timers on Site", "Set up of Start Line is Finished", 
    "Full Marathon Start is 100%-awaiting Go Ahead"
]

def get_now():
    return datetime.now(pytz.timezone(TIMEZONE)).strftime("%I:%M %p")

@st.fragment(run_every=3)
def render():
    st.title(f"🏁 {THIS_LOCATION} Site Lead")
    # Using the NEW V2 ID
    doc_ref = db.collection("site_statuses").document("full_start_v2")
    data = doc_ref.get().to_dict() or {}

    count = sum(1 for m in MILESTONES if data.get(m, False))
    ready = (count == 6)

    c = "#1b5e20" if ready else "#4c0000"
    st.markdown(f"<div style='background:{c}; padding:20px; border-radius:15px; text-align:center;'><h1>{'GO' if ready else 'NO GO'} ({count}/6)</h1></div>", unsafe_allow_html=True)
    st.divider()

    for m in MILESTONES:
        checked = data.get(m, False)
        col1, col2 = st.columns([2, 8])
        with col1:
            val = st.checkbox("", value=checked, key=f"m_{m}")
            if val != checked:
                doc_ref.set({m: val}, merge=True)
                
                # Update the settings doc for the master page
                safe_id = THIS_LOCATION.replace("/", "_").replace(" ", "_")
                db.collection("settings").document(f"status_{safe_id}").set({
                    "completed": (count + (1 if val else -1) == 6),
                    "timestamp": get_now()
                }, merge=True)
                st.rerun()
        with col2:
            st.markdown(f"## {m}")

render()
