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

# --- PERSISTENCE LOGIC ---
# Initialize session state for the toggle if not already there
if "tracking_active" not in st.session_state:
    st.session_state.tracking_active = False

# --- NO-SLEEP INJECTION ---
st.components.v1.html(
    """
    <script>
    async function requestWakeLock() {
      try {
        const wakeLock = await navigator.wakeLock.request('screen');
      } catch (err) {}
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
    
    # We use a key to keep the name in the box during refreshes
    staff_name = st.text_input("Name/Role", key="staff_name_persistent")
    
    # The toggle now uses the session state to stay 'on'
    tracking_toggle = st.toggle(
        "Enable My Live Tracking", 
        value=st.session_state.tracking_active,
        key="tracking_on"
    )
    
    # Update our session state based on the toggle
    st.session_state.tracking_active = tracking_toggle

    if st.session_state.tracking_active and staff_name:
        st.success(f"Tracking Protocol: ACTIVE")
        st.caption("Keep this tab open for continuous pings.")
    else:
        st.info("Tracking is currently OFF.")

# --- 1. COURSE OVERVIEW ---
st.components.v1.html('<iframe src="https://www.google.com/maps/d/u/0/embed?mid=1_your_actual_map_id" width="100%" height="450" style="border-radius:25px; border:3px solid black;"></iframe>', height=450)

# --- 2. THE SYNC LOOP ---
@st.fragment(run_every=20)
def sync_and_show_map():
    # PART A: PUSH DATA
    if st.session_state.tracking_active and staff_name:
        loc = get_geolocation()
        
        if loc and "coords" in loc:
            lat = loc['coords']['latitude']
            lon = loc['coords']['longitude']
            
            # Save to Firestore
            db.collection("staff_locations").document(staff_name.strip()).set({
                "name": staff_name.strip(),
                "latitude": lat,
                "longitude": lon,
                "timestamp": firestore.SERVER_TIMESTAMP,
                "active": True # Flag to show they are currently transmitting
            })
            st.sidebar.write(f"📡 Last Ping: {datetime.now().strftime('%I:%M:%S %p')}")

    # PART B: PULL & DISPLAY
    locations_ref = db.collection("staff_locations").stream()
    loc_data = []
    
    for doc in locations_ref:
        d = doc.to_dict()
        if "latitude" in d and "longitude" in d:
            loc_data.append(d)
    
    if loc_data:
        df = pd.DataFrame(loc_data)
        
        # Determine map center
        avg_lat = df["latitude"].mean()
        avg_lon = df["longitude"].mean()

        st.pydeck_chart(pdk.Deck(
            layers=[
                pdk.Layer(
                    "ScatterplotLayer",
                    data=df,
                    get_position="[longitude, latitude]",
                    get_color="[40, 167, 69, 200]", # Fast Green
                    get_radius=180,
                    pickable=True
                )
            ],
            initial_view_state=pdk.ViewState(
                latitude=avg_lat,
                longitude=avg_lon,
                zoom=12
            ),
            map_style=None,
            tooltip={"text": "{name}"}
        ))
    else:
        st.info("Awaiting staff connection...")

sync_and_show_map()
