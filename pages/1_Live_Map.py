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

# CSS for styling
st.markdown("""
    <style>
    .map-container {
        border: 3px solid black;
        border-radius: 25px;
        overflow: hidden;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📍 Unified Race Command Map")

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
            st.warning("Waiting for GPS signal... Make sure location is enabled.")

# --- MAIN DISPLAY ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Course Overview (Custom Map)")
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    # Replace the URL below with your actual Google My Maps embed link
    st.components.v1.html('<iframe src="https://www.google.com/maps/d/u/0/embed?mid=YOUR_MAP_ID_HERE" width="100%" height="500" style="border:none;"></iframe>', height=500)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    @st.fragment(run_every=30)
    def show_staff_list():
        st.subheader("Active Personnel")
        locations_ref = db.collection("staff_locations").stream()
        loc_data = []
        for doc in locations_ref:
            d = doc.to_dict()
            # CRITICAL FIX: Map needs 'latitude' and 'longitude' lowercase keys
            loc_data.append({
                "Staff": d["name"], 
                "latitude": d.get("latitude"), 
                "longitude": d.get("longitude")
            })
        
        if loc_data:
            df = pd.DataFrame(loc_data)
            # Drop any rows that have missing GPS data to prevent errors
            df = df.dropna(subset=['latitude', 'longitude'])
            
            if not df.empty:
                # mini-map for staff clusters
                st.map(df, size=20, color="#28a745", use_container_width=True)
                # table for quick reference
                st.dataframe(df[["Staff"]], use_container_width=True, hide_index=True)
            else:
                st.info("Staff connected, but no GPS coordinates received yet.")
        else:
            st.info("No staff active. Use the sidebar to check in.")

    show_staff_list()
