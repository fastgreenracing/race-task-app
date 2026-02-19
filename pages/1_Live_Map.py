import streamlit as st
from google.cloud import firestore
import json
from streamlit_js_eval import get_geolocation
import pandas as pd

# 1. Setup Database (Same as your app.py)
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Firestore credentials not found in secrets.")
    st.stop()

st.title("📍 Staff Live Tracker")

# 2. Staff Login / Identification
st.sidebar.header("Staff Check-In")
staff_name = st.sidebar.text_input("Enter Your Name/Role (e.g., Lead Bike)")
tracking_on = st.sidebar.toggle("Enable Live Tracking")

if tracking_on and staff_name:
    # This grabs the GPS coordinates from the phone's browser
    location = get_geolocation()
    
    if location:
        lat = location['coords']['latitude']
        lon = location['coords']['longitude']
        
        # Save to Firestore
        db.collection("staff_locations").document(staff_name).set({
            "name": staff_name,
            "latitude": lat,
            "longitude": lon,
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        st.sidebar.success(f"Tracking active for {staff_name}")
        st.sidebar.write(f"Last Lat/Lon: {lat}, {lon}")
    else:
        st.sidebar.warning("Please allow location access in your browser.")

# 3. The Master Map (For you and leads to see everyone)
st.subheader("Live Race Map")

# Pull all staff locations from Firestore
locations_ref = db.collection("staff_locations").stream()
loc_data = []

for doc in locations_ref:
    d = doc.to_dict()
    loc_data.append({"name": d["name"], "latitude": d["latitude"], "longitude": d["longitude"]})

if loc_data:
    df = pd.DataFrame(loc_data)
    st.map(df) # Automatically plots all lat/lon points
    st.table(df) # Shows names and coordinates below the map
else:
    st.info("No staff currently tracking.")
