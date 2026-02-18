import streamlit as st
from google.cloud import firestore
import json

# Database Connection (Keep your existing connection code here)
key_dict = json.loads(st.secrets["textkey"])
db = firestore.Client.from_service_account_info(key_dict)

# --- ADMIN SETTINGS ---
ADMIN_PASSWORD = "fastgreen2026"

# (Include your get_categories, add_task, update_task_status functions here)

@st.fragment(run_every=5) # Tightened refresh to 5 seconds for race-day speed
def show_tasks():
    is_admin = st.session_state.get('admin_logged_in', False)
    categories = get_categories()
    
    for cat in categories:
        st.subheader(f"📍 {cat}")
        tasks = db.collection("race_tasks").where("category", "==", cat).stream()
        
        for task in tasks:
            td = task.to_dict()
            task_id = task.id
            db_status = td.get("completed", False)
            
            # --- THE FIX: SYNC STATE ---
            # This forces the local checkbox to match the database exactly
            check_key = f"state_{task_id}"
            st.session_state[check_key] = db_status

            # Dynamic Colors (Solid Hex for stability)
            bg_color = "#dcfce7" if db_status else "#fee2e2"
            border_color = "#22c55e" if db_status else "#ef4444"
            
            st.markdown(
                f"""<div style="background-color: {bg_color}; border: 2px solid {border_color}; 
                padding: 15px; border-radius: 10px; margin-bottom: 10px; color: black;">""", 
                unsafe_allow_html=True
            )
            
            cols = st.columns([1, 7, 2]) if is_admin else st.columns([1, 9])

            with cols[0]:
                is_disabled = db_status and not is_admin
                
                # Checkbox now pulls directly from the synced Session State
                check_val = st.checkbox(
                    "", 
                    value=st.session_state[check_key], 
                    key=f"widget_{task_id}", # Fixed widget key
                    disabled=is_disabled, 
                    label_visibility="collapsed"
                )
                
                # If the user/admin physically clicks, update the DB
                if check_val != db_status:
                    update_task_status(task_id, check_val)
                    st.rerun()
            
            with cols[1]:
                st.markdown(f"**{'✅' if db_status else '⏳'} {td['title']}**")
                if td.get("notes"):
                    st.info(f"📝 {td['notes']}")
                
                if is_admin:
                    with st.popover("Edit Notes"):
                        new_note = st.text_area("Notes:", value=td.get("notes", ""), key=f"note_{task_id}")
                        if st.button("Save", key=f"btn_{task_id}"):
                            update_note(task_id, new_note)
                            st.rerun()
            
            if is_admin:
                with cols[2]:
                    if st.button("Delete", key=f"del_{task_id}", type="secondary", use_container_width=True):
                        db.collection("race_tasks").document(task_id).delete()
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

show_tasks()
