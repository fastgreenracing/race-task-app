import streamlit as st
from google.cloud import firestore
import json
from streamlit_js_eval import get_geolocation
import pandas as pd
import pydeck as pdk
from datetime import datetime

# 1. Database Connection
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Credentials not found.")
    st.stop()

st.set_page_config(page_title="Staff Live Map", page_icon="📍", layout="wide")

# Persistent Ping Counter
if "ping_count" not in st.session_state:
    st.session_state.ping_count = 0

st.title("📍 Race Command: Live Staff Tracker")

# --- SIDEBAR: STAFF TRACKING ---
with st.sidebar:
    st.header("Staff Check-In")
    staff_name = st.text_input("Name/Role (e.g., Ben DeWitt)", key="staff_name_input")
    tracking_on = st.toggle("Enable My Live Tracking", key="tracking_toggle")
    
    if tracking_on and not staff_name:
        st.warning("Please enter your name to start tracking.")

# --- 1. COURSE OVERVIEW (GOOGLE MAP) ---
st.subheader("🗺️ Course Overview")
st.components.v1.html('<iframe src="https://www.google.com/maps/d/u/0/embed?mid=1_your_actual_map_id" width="100%" height="600" style="border-radius:25px; border:3px solid black;"></iframe>', height=600)

st.divider()

# --- 2. THE SYNC LOOP ---
@st.fragment(run_every=15) # Increased frequency to 15s to catch movement better
def sync_and_show_map():
    # PART A: PUSH GPS DATA
    if st.session_state.get("tracking_toggle") and staff_name:
        # This triggers the browser's native Geolocation API
        loc = get_geolocation()
        
        if loc and "coords" in loc:
            lat = loc['coords']['latitude']
            lon = loc['coords']['longitude']
            
            name_clean = staff_name.strip()
            db.collection("staff_locations").document(name_clean).set({
                "name": name_clean,
                "latitude": lat,
                "longitude": lon,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.session_state.ping_count += 1
            st.sidebar.success(f"Tracking Active! Pings: {st.session_state.ping_count}")
            st.sidebar.caption(f"Last update: {datetime.now().strftime('%I:%M:%S %p')}")
        else:
            st.sidebar.warning("Searching for GPS... Keep this tab open.")

    # PART B: PULL & DISPLAY ALL STAFF
    st.subheader("🏃 Live Staff Positions")
    locations_ref = db.collection("staff_locations").stream()
    loc_data = []
    
    for doc in locations_ref:
        d = doc.to_dict()
        if "latitude" in d and "longitude" in d:
            loc_data.append({
                "name": d["name"],
                "latitude": d["latitude"], 
                "longitude": d["longitude"]
            })
    
    if loc_data:
        df = pd.DataFrame(loc_data)
        
        view_state = pdk.ViewState(
            latitude=df["latitude"].mean(),
            longitude=df["longitude"].mean(),
            zoom=12
        )

        icon_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df,
            get_position="[longitude, latitude]",
            get_color="[40, 167, 69, 200]",
            get_radius=150,
            pickable=True
        )

        st.pydeck_chart(pdk.Deck(
            layers=[icon_layer],
            initial_view_state=view_state,
            map_style=None,
            tooltip={"text": "{name}"}
        ))
    else:
        st.info("Waiting for staff to check in...")

sync_and_show_map()
