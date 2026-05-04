# --- SIDEBAR: ADMIN ---
with st.sidebar:
    st.header("🔐 Access Control")
    if not st.session_state.get("authenticated"):
        pwd = st.text_input("Admin Password", type="password")
        if st.button("Login"):
            if pwd == ADMIN_PASSWORD:
                st.session_state.authenticated = True; st.rerun()
            else: st.error("Incorrect Password")
    else:
        st.success("Admin Mode Active")
        if st.button("Logout"): st.session_state.authenticated = False; st.rerun()
        
        current_cats = get_categories()
        
        # 🚥 1. LIVE STATUS
        st.divider()
        st.subheader("🚥 Live Status Control")
        for c in current_cats:
            c_data = get_cat_data(c['name'])
            with st.expander(f"Status: {c['name']}"):
                new_s = st.toggle("Ready (GO)", value=c_data.get("completed", False), key=f"sb_t_{c['name']}")
                new_n = st.text_input("Note", value=c_data.get("note", ""), key=f"sb_n_{c['name']}")
                if st.button("Save", key=f"sb_btn_{c['name']}"):
                    set_cat_status(c['name'], new_s, new_n); st.rerun()

        # 📁 2. CATEGORY ADMIN
        st.divider()
        st.subheader("📁 Manage Categories")
        with st.expander("Move / Rename / Delete"):
            for i, cat in enumerate(current_cats):
                col_name, col_up, col_down, col_del = st.columns([4, 1, 1, 1])
                col_name.write(f"**{cat['name']}**")
                
                if col_up.button("🔼", key=f"cat_up_{i}") and i > 0:
                    current_cats[i], current_cats[i-1] = current_cats[i-1], current_cats[i]
                    save_categories(current_cats); st.rerun()
                
                if col_down.button("🔽", key=f"cat_down_{i}") and i < len(current_cats)-1:
                    current_cats[i], current_cats[i+1] = current_cats[i+1], current_cats[i]
                    save_categories(current_cats); st.rerun()
                
                if col_del.button("🗑️", key=f"cat_del_{i}"):
                    current_cats.pop(i)
                    save_categories(current_cats); st.rerun()
                
                new_c_name = st.text_input("Rename:", value=cat['name'], key=f"ren_c_{i}")
                if new_c_name != cat['name'] and st.button(f"Confirm Rename", key=f"cren_{i}"):
                    old = cat['name']
                    cat['name'] = new_c_name
                    save_categories(current_cats)
                    for t in db.collection("race_tasks").where("category", "==", old).stream():
                        db.collection("race_tasks").document(t.id).update({"category": new_c_name})
                    st.rerun()

        # 📝 3. TASK ADMIN
        st.divider()
        st.subheader("📝 Manage Tasks")
        with st.expander("Move / Edit / Delete Existing"):
            if current_cats:
                sel_cat = st.selectbox("Category", [c['name'] for c in current_cats], key="mt_cat")
                tasks = [t for t in db.collection("race_tasks").where("category", "==", sel_cat).order_by("sort_order").stream()]
                for i, t in enumerate(tasks):
                    td = t.to_dict()
                    c_up, c_down, c_del = st.columns([1,1,1])
                    if c_up.button("🔼", key=f"tup_{t.id}") and i > 0:
                        db.collection("race_tasks").document(t.id).update({"sort_order": i-1})
                        db.collection("race_tasks").document(tasks[i-1].id).update({"sort_order": i}); st.rerun()
                    if c_down.button("🔽", key=f"tdown_{t.id}") and i < len(tasks)-1:
                        db.collection("race_tasks").document(t.id).update({"sort_order": i+1})
                        db.collection("race_tasks").document(tasks[i+1].id).update({"sort_order": i}); st.rerun()
                    if c_del.button("🗑️", key=f"tdel_{t.id}"):
                        db.collection("race_tasks").document(t.id).delete(); st.rerun()
                    new_title = st.text_input("Edit Title:", value=td['title'], key=f"edt_{t.id}")
                    if st.button("Save Title", key=f"savt_{t.id}"):
                        db.collection("race_tasks").document(t.id).update({"title": new_title}); st.rerun()
                    st.divider()

        with st.expander("➕ Add New Task"):
            if current_cats:
                nt_cat = st.selectbox("Category Select", [c['name'] for c in current_cats], key="ant_cat")
                nt_title = st.text_input("New Task Title", key="ant_title")
                if st.button("Add Task"):
                    db.collection("race_tasks").add({"category": nt_cat, "title": nt_title, "completed": False, "sort_order": 99}); st.rerun()
