import streamlit as st
from google.cloud import firestore
import json

# DB Connection
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

# Filter for THIS specific site
SITE_LOCATION = "Full Marathon Start"

st.set_page_config(page_title=SITE_LOCATION)

st.title(f"📍 {SITE_LOCATION} Checklist")

# Reuse your task display logic here, but filter the query:
# tasks_query = db.collection("race_tasks").where("category", "==", SITE_LOCATION)...
