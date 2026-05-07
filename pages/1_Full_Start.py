import streamlit as st
from google.cloud import firestore
import json

# 1. Database Connection
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Firestore secrets not found.")
    st.stop()

st.set_page_config(page_title="Full Start Coordinator", layout="wide")

# --- THE "MASKING" THEME: HIDING THE GHOST BOX ---
st.markdown("""
    <style>
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
        font-family: "Times New Roman", Times, serif !important;
    }
    
    p, span, label, b, .stMarkdown {
        font-size: 16pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
    }

    h1 {
        font-size: 24pt !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* 1. THE MAIN MILESTONE CONTAINER */
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 1px solid #000000 !important;
        border-radius: 2px;
        padding: 2px 10px !important;
        margin-bottom: 4px !important;
        background: #FFFFFF;
        display: flex;
        align-items: center;
        overflow: visible !important; /* Vital for letting the checkmark float out */
    }
    
    /* 2. THE "NUCLEAR" HIDE: Shrink the container to nothing */
    [data-testid="stCheckbox"] {
        border: none !important;
        background: transparent !important;
        padding: 0 !important;
        margin: 0 !important;
        width: 5px !important; /* Shrinks the 'ghost box' to a tiny sliver */
        height: 5px !important;
        overflow: visible !important;
    }

    /* 3. STRIP THE INTERNAL CHECKBOX BOX */
    [data-testid="stCheckbox"] [role="checkbox"] {
        border: none !important;
        background: transparent !important;
        background-color: transparent !important;
        box-shadow: none !important;
        width: 1px !important;
        height: 1px !important;
    }

    /* 4. POSITION THE FLOATING CHECKMARK */
    /* We use scale and translation to move it outside the tiny container */
    [data-testid="stCheckbox"] { 
        transform: scale(2.8) translateX(5px) translateY(-2px); 
        z-index: 99;
    }

    /* Ensure check icon stays red and visible */
    [data-testid="stCheckbox"] svg {
        fill: #FF0000 !important;
    }

    .status-header {
        padding: 25px;
        border: 2px solid #000000;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

MILESTONES = [
    "Staff on Site", "Volunteers on Site", "Announcers on Site", 
    "Timers on Site", "Set up of Start Line is Finished", 
    "Full Marathon Start is 100%-awaiting Go Ahead"
]

@st.fragment(run_every=2)
def render():
    st.title("Full Marathon Start Checklist")
    doc_ref = db.collection("site_statuses").document("full_start_FINAL")
    data
