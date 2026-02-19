import streamlit as st
from google.cloud import firestore
import json
from streamlit_js_eval import get_geolocation
import pandas as pd
import pydeck as pdk

# 1. Database Connection
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Credentials not found.")
    st.stop()

st.set_page_config(page_title="Staff Live Map", page_icon="📍", layout="wide")

st.markdown("""
    <style>
    .map-container { border: 3px solid black; border-radius: 25px; overflow: hidden; margin-bottom: 30px; }
    </style>
    """, unsafe_allow_html=True)

st.title("📍 Race Command: Live Staff Tracker")

# --- SIDEBAR: STAFF TRACKING ---
with st.sidebar:
    st.header("Staff Check-In")
    staff_name = st.text_input("Name/Role (e.g., Ben DeWitt)", key="staff_name_input")
    tracking_on = st.toggle("Enable My Live Tracking")

# --- 1. COURSE OVERVIEW (CUSTOM GOOGLE MAP) ---
st.subheader("🗺️ Course Overview")
st.markdown('<div class="map-container">', unsafe_allow_html=True)
# Replace with your actual Google My Maps embed link
st.components.v1.html('<iframe src="https://www.google.com/maps/d/u/0/embed?mid=1_your_actual_map_id" width="100%" height="600" style="border:none;"></iframe>', height=600)
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 2. THE LIVE LOOP (Pings GPS and Updates Map) ---
@st.fragment(run_every=30)
def sync_and_show_map():
    # PART A: Update current user's location if tracking is on
    if tracking_on and staff_name:
        location = get_geolocation()
        if location:
            lat_val = location['coords']['latitude']
            lon_val = location['coords']['longitude']
            
            name_clean = staff_name.strip()
            db.collection("staff_locations").document(name_clean).set({
                "name": name_clean,
                "latitude": lat_val,
                "longitude": lon_val,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.sidebar.success(f"Last Ping: {datetime.now().strftime('%I:%M:%S %p')}")

    # PART B: Pull all staff and show the map
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
            zoom=12,
            pitch=0
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
        st.info("No staff currently tracking.")

sync_and_show_map()
