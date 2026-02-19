import streamlit as st
from google.cloud import firestore
import json
from streamlit_js_eval import get_geolocation
import pandas as pd

# 1. Database Connection
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Credentials not found.")
    st.stop()

st.set_page_config(page_title="Staff Live Map", page_icon="📍", layout="wide")

# CSS for a clean, full-width look
st.markdown("""
    <style>
    .map-container {
        border: 3px solid black;
        border-radius: 25px;
        overflow: hidden;
        margin-bottom: 30px;
    }
    .stDataFrame {
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📍 Race Command: Full-Width Map View")

# --- SIDEBAR: STAFF TRACKING ---
with st.sidebar:
    st.header("Staff Check-In")
    staff_name = st.text_input("Name/Role (e.g., Lead Bike)")
    tracking_on = st.toggle("Enable My Live Tracking")
    
    if tracking_on and staff_name:
        location = get_geolocation()
        if location:
            lat_val = location['coords']['latitude']
            lon_val = location['coords']['longitude']
            
            db.collection("staff_locations").document(staff_name).set({
                "name": staff_name,
                "latitude": lat_val,
                "longitude": lon_val,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success(f"Tracking active: {staff_name}")
        else:
            st.warning("Searching for GPS... Ensure location is enabled on your phone.")

# --- 1. COURSE OVERVIEW (CUSTOM GOOGLE MAP) ---
st.subheader("🗺️ Course Overview & Key Points")
st.markdown('<div class="map-container">', unsafe_allow_html=True)
# Replace the URL below with your actual Google My Maps embed link
st.components.v1.html('<iframe src="https://www.google.com/maps/d/embed?mid=1UOQuxT6lSaKGXm2wmjVzeFwVuORY8Vk&hl=en&ehbc=2E312F" width="640" height="480"></iframe>', height=600)
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 2. STAFF TRACKER (LIVE POSITIONS) ---
@st.fragment(run_every=30)
def show_staff_map():
    st.subheader("🏃 Live Staff Positions")
    locations_ref = db.collection("staff_locations").stream()
    loc_data = []
    
    for doc in locations_ref:
        d = doc.to_dict()
        if "latitude" in d and "longitude" in d:
            loc_data.append({
                "Staff": d["name"], 
                "latitude": d["latitude"], 
                "longitude": d["longitude"]
            })
    
    if loc_data:
        df = pd.DataFrame(loc_data)
        
        # Large map for better visibility
        st.map(df, size=40, color="#28a745", use_container_width=True)
        
        # Reference list below the map
        with st.expander("Show Personnel Coordinates List"):
            st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No staff currently tracking. Use the sidebar to begin.")

show_staff_map()
