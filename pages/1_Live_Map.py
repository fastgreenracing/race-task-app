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

# --- CSS for a Unified Look ---
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
            lat = location['coords']['latitude']
            lon = location['coords']['longitude']
            
            db.collection("staff_locations").document(staff_name).set({
                "name": staff_name,
                "latitude": lat,
                "longitude": lon,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success(f"Tracking active: {staff_name}")

# --- MAIN DISPLAY: THE UNIFIED VIEW ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Live Course & Staff Overlay")
    # This is your custom route map
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    st.components.v1.html('<iframe src="https://www.google.com/maps/d/u/0/embed?mid=1S9N_M4Vp4_Q0P0o6H1_v8B_k8B_k8B" width="100%" height="500" style="border:none;"></iframe>', height=500)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    @st.fragment(run_every=30)
    def show_staff_list():
        st.subheader("Active Personnel")
        locations_ref = db.collection("staff_locations").stream()
        loc_data = []
        for doc in locations_ref:
            d = doc.to_dict()
            loc_data.append({"Staff": d["name"], "Lat": d["latitude"], "Lon": d["longitude"]})
        
        if loc_data:
            df = pd.DataFrame(loc_data)
            st.dataframe(df[["Staff"]], use_container_width=True, hide_index=True)
            # Small mini-map for staff clusters
            st.map(df, size=20, color="#28a745", use_container_width=True)
        else:
            st.info("No staff active.")

    show_staff_list()
