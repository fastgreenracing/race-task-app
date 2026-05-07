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

# 2. Page Configuration
st.set_page_config(page_title="Ops Master Dashboard", page_icon="🎛️", layout="wide")

# --- CSS: Terminal Green Ops Theme ---
st.markdown(
    """
    <style>
    .stApp { background-color: #000000; color: #28a745; }
    h1, h2, h3, p, span, label { color: #28a745 !important; }
    .status-card {
        border: 2px solid #28a745;
        border-radius: 15px;
        padding: 20px;
        background-color: #0a0a0a;
        margin-bottom: 20px;
        text-align: center;
    }
    .bold-divider { 
        border: none; height: 3px; background-color: #28a745; 
        margin-top: 20px; margin-bottom: 20px; opacity: 0.3;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- Helper Functions ---
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    return sorted(cat_ref.to_dict().get("data", []), key=lambda x: x.get('order', 0)) if cat_ref.exists else []

def get_site_status(cat_name):
    safe_id = cat_name.replace("/", "_").replace(" ", "_")
    
    # Check specific milestones for Full Marathon Start
    if cat_name == "Full Marathon Start":
        milestone_doc = db.collection("site_statuses").document("full_start").get()
        if milestone_doc.exists:
            data = milestone_doc.to_dict()
            milestones = [
                "Staff on Site", "Volunteers on Site", "Announcers on Site", 
                "Timers on Site", "Set up of Start Line is Finished", 
                "Full Marathon Start is 100%-awaiting Go Ahead"
            ]
            completed_count = sum(1 for m in milestones if data.get(m, False))
            
            # HARD OVERRIDE: Must be 6/6 to be ready
            is_ready = (completed_count == 6)
            return {
                "completed": is_ready, 
                "timestamp": f"{completed_count}/6 Milestones" if not is_ready else "READY"
            }
    
    # Default fallback for other categories
    doc = db.collection("settings").document(f"status_{safe_id}").get()
    return doc.to_dict() if doc.exists else {"completed": False, "timestamp": "No Data"}

# --- MAIN DASHBOARD VIEW ---
st.title("🎛️ Race Operations: Master Dashboard")

@st.fragment(run_every=5)
def render_dashboard():
    categories = get_categories()
    if not categories:
        st.info("No locations found.")
        return

    cols = st.columns(len(categories))
    for i, cat_dict in enumerate(categories):
        cat_name = cat_dict['name']
        status_data = get_site_status(cat_name)
        
        is_ready = status_data.get("completed", False)
        status_color = "#28a745" if is_ready else "#ff4b4b"
        status_text = "GO" if is_ready else "NO GO"
        
        with cols[i]:
            st.markdown(
                f"""
                <div class="status-card" style="border-color: {status_color};">
                    <p style="font-size: 14px; margin-bottom: 5px;">LOCATION</p>
                    <h3 style="margin-top: 0;">{cat_name}</h3>
                    <div class="bold-divider"></div>
                    <h1 style="color: {status_color} !important; font-size: 64px; font-weight: 900;">
                        {status_text}
                    </h1>
                    <p style="font-size: 14px; opacity: 0.8; font-weight: bold;">{status_data.get('timestamp')}</p>
                </div>
                """, 
                unsafe_allow_html=True
            )

render_dashboard()
