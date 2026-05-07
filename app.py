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

st.set_page_config(page_title="Ops Master Dashboard", layout="wide")

# --- CSS: Terminal Theme ---
st.markdown("""
    <style>
    .stApp { background-color: #000000; color: #28a745; }
    h1, h2, h3, p, span, label { color: #28a745 !important; }
    .status-card {
        border: 2px solid #28a745; border-radius: 15px; padding: 20px;
        background-color: #0a0a0a; margin-bottom: 20px; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    return sorted(cat_ref.to_dict().get("data", []), key=lambda x: x.get('order', 0)) if cat_ref.exists else []

def get_full_start_status():
    """HARD-CODED RECOUNT: Manual milestone verification."""
    doc = db.collection("site_statuses").document("full_start_FINAL").get()
    if doc.exists:
        data = doc.to_dict()
        m_list = [
            "Staff on Site", "Volunteers on Site", "Announcers on Site", 
            "Timers on Site", "Set up of Start Line is Finished", 
            "Full Marathon Start is 100%-awaiting Go Ahead"
        ]
        count = sum(1 for m in m_list if data.get(m) == True)
        ready = (count == 6)
        # Updated text for the 6/6 milestone reached
        return {"ready": ready, "label": "WAITING FOR FINAL GO AHEAD" if ready else f"{count}/6 MILESTONES READY"}
    return {"ready": False, "label": "0/6 READY"}

st.title("🎛️ Ops Master Dashboard")

@st.fragment(run_every=3)
def render_dashboard():
    categories = get_categories()
    if not categories: return
    
    cols = st.columns(len(categories))
    for i, cat in enumerate(categories):
        name = cat['name']
        
        if "Full" in name and "Start" in name:
            status = get_full_start_status()
            ready = status["ready"]
            display_text = status["label"]
        else:
            safe_id = name.replace("/", "_").replace(" ", "_")
            doc = db.collection("settings").document(f"status_{safe_id}").get()
            res = doc.to_dict() if doc.exists else {"completed": False}
            ready = res.get("completed", False)
            display_text = "READY" if ready else "NOT READY"
        
        color = "#28a745" if ready else "#ff4b4b"
        text = "GO" if ready else "NO GO"
        
        with cols[i]:
            st.markdown(f"""
                <div class="status-card" style="border-color: {color};">
                    <p style="font-size: 12px; opacity: 0.7;">LOCATION</p>
                    <h3 style="margin-top: 0;">{name}</h3>
                    <div style="height: 2px; background: {color}; opacity: 0.3; margin: 15px 0;"></div>
                    <h1 style="color: {color} !important; font-size: 54px; font-weight: 900;">{text}</h1>
                    <p style="font-weight: bold; background: {color}; color: black !important; border-radius: 5px; padding: 5px;">{display_text}</p>
                </div>
            """, unsafe_allow_html=True)

render_dashboard()
