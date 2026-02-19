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

st.title("📍 Staff Live GPS Tracker")

# --- CUSTOM GOOGLE MAP EMBED (COURSE ROUTE) ---
st.subheader("🗺️ Course Route & Key Areas")
st.components.v1.html('<iframe src="https://www.google.com/maps/d/u/0/embed?mid=1S9N_M4Vp4_Q0P0o6H1_v8B_k8B_k8B" width="100%" height="480" style="border-radius:25px; border: 3px solid black;"></iframe>', height=500)

# --- STAFF TRACKING SECTION ---
with st.sidebar:
    st.header("Staff Check-In")
    staff_name = st.text_input("Name/Role (e.g., Lead Bike)")
    tracking_on = st.toggle("Enable My Live Tracking")
    
    if tracking_on and staff_name:
        location = get_geolocation()
        if location:
            lat = location['coords']['latitude']
            lon = location['coords']['longitude']
            
            # Update Firestore
            db.collection("staff_locations").document(staff_name).set({
                "name": staff_name,
                "latitude": lat,
                "longitude": lon,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success(f"Tracking active: {staff_name}")
        else:
            st.warning("Please allow GPS access in your browser settings.")

# 3. Live Map Display (Staff Icons)
@st.fragment(run_every=30)
def refresh_map():
    locations_ref = db.collection("staff_locations").stream()
    loc_data = []

    for doc in locations_ref:
        d = doc.to_dict()
        loc_data.append({
            "Staff": d["name"], 
            "latitude": d["latitude"], 
            "longitude": d["longitude"]
        })

    if loc_data:
        st.subheader("Current Personnel Locations")
        df = pd.DataFrame(loc_data)
        st.map(df, zoom=12, use_container_width=True)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No staff currently tracking. Waiting for check-ins...")

refresh_map()
