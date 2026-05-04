# --- MAIN DISPLAY ---
@st.fragment(run_every=5)
def show_tasks():
    is_admin = st.session_state.authenticated
    categories = get_categories()
    for cat_dict in categories:
        cat = cat_dict['name']
        st.markdown('<div class="bold-divider"></div>', unsafe_allow_html=True)
        c_data = get_cat_data(cat)
        col_name, col_status_group = st.columns([7, 3])
        with col_name: st.markdown(f"## <u>**{cat}**</u>", unsafe_allow_html=True)
        with col_status_group:
            is_go = c_data.get("completed", False)
            s_color = "#28a745" if is_go else "#ff4b4b" 
            st.markdown(f'<div style="text-align: center;"><p style="font-weight: bold; font-size: 20px;">STATUS</p><h2 style="color: {s_color}; font-size: 48px; font-weight: 900;">{"GO" if is_go else "NO GO"}</h2></div>', unsafe_allow_html=True)
        
        if c_data.get("note"): 
            st.info(f"**Note:** {c_data['note']} \n\n *Updated: {c_data.get('timestamp')}*")
        
        tasks_query = db.collection("race_tasks").where("category", "==", cat).order_by("sort_order").stream()
        for task in tasks_query:
            td = task.to_dict()
            t_cols = st.columns([1.5, 8.5])
            with t_cols[0]:
                # Unique key prevents widget state conflicts
                check = st.checkbox("", value=td.get("completed", False), key=f"w_{task.id}_{td.get('completed')}", disabled=(td.get("completed") and not is_admin), label_visibility="collapsed")
                if check != td.get("completed"):
                    db.collection("race_tasks").document(task.id).update({"completed": check})
                    st.rerun()
            with t_cols[1]: 
                st.markdown(f"### {td['title']}")

show_tasks()
