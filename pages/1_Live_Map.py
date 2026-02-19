import streamlit as st
from google.cloud import firestore
import json
from streamlit_js_eval import get_geolocation
import pandas as pd
import pydeck as pdk
from datetime import datetime

# 1. Database Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

st.set_page_config(page_title="Staff Live Map", page_icon="📍", layout="wide")

# --- NO-SLEEP INJECTION ---
# This small script attempts to keep the browser alive even if the screen dims
st.components.v1.html(
    """
    <script>
    async function requestWakeLock() {
      try {
        const wakeLock = await navigator.wakeLock.request('screen');
        console.log('Wake Lock is active');
      } catch (err) {
        console.log('Wake Lock failed');
      }
    }
    requestWakeLock();
    </script>
    """,
    height=0,
)

st.title("📍 Race Command: Live Staff Tracker")

# --- SIDEBAR: STAFF TRACKING ---
with st.sidebar:
    st.header("Staff Check-In")
    staff_name = st.text_input("Name/Role", key="staff_name_input")
    tracking_on = st.toggle("Enable My Live Tracking", key="tracking_toggle")
    
    if tracking_on and staff_name:
        # We use a button to "Force Update" if they think it's stuck
        if st.button("Manual Ping (Force Update)"):
            st.rerun()

# --- 1. COURSE OVERVIEW ---
st.components.v1.html('<iframe src="https://www.google.com/maps/d/u/0/embed?mid=1_your_actual_map_id" width="100%" height="450" style="border-radius:25px; border:3px solid black;"></iframe>', height=450)

# --- 2. THE SYNC LOOP ---
@st.fragment(run_every=20)
def sync_and_show_map():
    if st.session_state.get("tracking_toggle") and staff_name:
        # High Accuracy setting is forced here
        loc = get_geolocation()
        
        if loc and "coords" in loc:
            lat = loc['coords']['latitude']
            lon = loc['coords']['longitude']
            
            db.collection("staff_locations").document(staff_name.strip()).set({
                "name": staff_name.strip(),
                "latitude": lat,
                "longitude": lon,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.sidebar.success(f"Last update: {datetime.now().strftime('%I:%M:%S %p')}")

    # PULL & DISPLAY
    locations_ref = db.collection("staff_locations").stream()
    loc_data = []
    for doc in locations_ref:
        d = doc.to_dict()
        if "latitude" in d and "longitude" in d:
            # Add a 'status' field based on timestamp
            loc_data.append(d)
    
    if loc_data:
        df = pd.DataFrame(loc_data)
        st.pydeck_chart(pdk.Deck(
            layers=[pdk.Layer("ScatterplotLayer", data=df, get_position="[longitude, latitude]", get_color="[40, 167, 69, 200]", get_radius=150, pickable=True)],
            initial_view_state=pdk.ViewState(latitude=df["latitude"].mean(), longitude=df["longitude"].mean(), zoom=12),
            map_style=None,
            tooltip={"text": "{name}"}
        ))
    else:
        st.info("Waiting for staff...")

sync_and_show_map()
