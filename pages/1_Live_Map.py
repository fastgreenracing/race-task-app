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
    # Using a key here ensures the name persists during the session
    staff_name = st.text_input("Name/Role (e.g., Ben DeWitt)", key="staff_name_input")
    tracking_on = st.toggle("Enable My Live Tracking")
    
    if tracking_on and staff_name:
        location = get_geolocation()
        if location:
            lat_val = location['coords']['latitude']
            lon_val = location['coords']['longitude']
            
            # IMPROVED INITIALS LOGIC
            name_clean = staff_name.strip()
            parts = name_clean.split()
            if len(parts) >= 2:
                # First letter of first word + first letter of last word
                initials = (parts[0][0] + parts[-1][0]).upper()
            elif len(name_clean) > 0:
                # Just the first two letters of the single word
                initials = name_clean[:2].upper()
            else:
                initials = "??"

            db.collection("staff_locations").document(name_clean).set({
                "name": name_clean,
                "initials": initials,
                "latitude": lat_val,
                "longitude": lon_val,
                "timestamp": firestore.SERVER_TIMESTAMP
            })
            st.success(f"Tracking active: {initials}")

# --- 1. COURSE OVERVIEW (CUSTOM GOOGLE MAP) ---
st.subheader("🗺️ Course Overview")
st.markdown('<div class="map-container">', unsafe_allow_html=True)
st.components.v1.html('<iframe src="https://www.google.com/maps/d/u/0/embed?mid=1_your_actual_map_id" width="100%" height="600" style="border:none;"></iframe>', height=600)
st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 2. STAFF TRACKER (PYDECK MAP) ---
@st.fragment(run_every=30)
def show_staff_map():
    st.subheader("🏃 Live Staff Positions")
    locations_ref = db.collection("staff_locations").stream()
    loc_data = []
    
    for doc in locations_ref:
        d = doc.to_dict()
        if "latitude" in d and "longitude" in d:
            loc_data.append({
                "name": d["name"],
                "initials": d.get("initials", "??"), 
                "latitude": d["latitude"], 
                "longitude": d["longitude"]
            })
    
    if loc_data:
        df = pd.DataFrame(loc_data)
        
        # Calculate view state based on staff locations
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

        text_layer = pdk.Layer(
            "TextLayer",
            data=df,
            get_position="[longitude, latitude]",
            get_text="initials",
            get_size=24,
            get_color="[0, 0, 0, 255]",
            get_alignment_baseline="'bottom'",
            get_pixel_offset="[0, -15]"
        )

        # FIXED MAP STYLE: Removed Mapbox-specific URL to avoid authentication errors
        st.pydeck_chart(pdk.Deck(
            layers=[icon_layer, text_layer],
            initial_view_state=view_state,
            map_style=None, # This uses the default base map
            tooltip={"text": "{name}"}
        ))
    else:
        st.info("No staff currently tracking.")

show_staff_map()
