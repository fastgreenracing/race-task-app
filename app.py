import streamlit as st
from google.cloud import firestore
import json
from datetime import datetime
import pytz

# 1. Database Connection
# This uses the secrets you've configured in the Streamlit Cloud dashboard
if "textkey" in st.secrets:
    key_dict = json.loads(st.secrets["textkey"])
    db = firestore.Client.from_service_account_info(key_dict)
else:
    st.error("Firestore secrets not found. Please check your Streamlit Secrets configuration.")
    st.stop()

# 2. Page Config (MUST be the first Streamlit command)
st.set_page_config(
    page_title="Race Logistics", 
    page_icon="🏃", 
    layout="wide"
)

# 3. Initialize Session State
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- CSS FOR UI (BLACK & GREEN TERMINAL THEME) ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #000000;
        color: #28a745;
    }
    .main .block-container {
        background-color: #000000;
        padding: 3rem;
    }
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #28a745 !important;
    }
    .bold-divider { 
        border: none; height: 5px; background-color: #28a745; 
        margin-top: 50px; margin-bottom: 30px; border-radius: 5px; 
    }
    [data-testid="stVerticalBlock"] > div:has([data-testid="stCheckbox"]) {
        border: 2px solid #28a745 !important; 
        border-radius: 15px; padding: 20px !important; 
        margin-bottom: 15px !important; background-color: #111111;
    }
    [data-testid="stCheckbox"] { transform: scale(2.2); margin-left: 25px; margin-top: 10px; }
    [data-testid="stCheckbox"] div[role="checkbox"] { border: 2px solid #28a745 !important; background-color: transparent !important; }
    [data-testid="stCheckbox"] div[role="checkbox"][aria-checked="true"] { background-color: #28a745 !important; }
    [data-testid="stSidebar"] { background-color: #050505 !important; border-right: 1px solid #28a745; }
    .stTextInput input, .stSelectbox div {
        background-color: #111111 !important; color: #28a745 !important; border: 1px solid #28a745 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Fast Green Racing: Live Tracker")

# --- ADMIN SETTINGS & PERSISTENCE ---
ADMIN_PASSWORD = "fastgreen2026" 
TIMEZONE = "US/Pacific"

def get_now():
    return datetime.now(pytz.timezone(TIMEZONE)).strftime("%I:%M %p")

# --- DATA FUNCTIONS ---
def get_categories():
    cat_ref = db.collection("settings").document("categories").get()
    return sorted(cat_ref.to_dict().get("data", []), key=lambda x: x.get('order', 0)) if cat_ref.exists else []

def save_categories(cat_data_list):
    for i, cat in enumerate(cat_data_list): cat['order'] = i
    db.collection("settings").document("categories").set({"data": cat_data_list})

def get_cat_data(cat_name):
    safe_id = cat_name.replace("/", "_").replace(" ", "_")
    doc = db.collection("settings").document(f"status_{safe_id}").get()
    return doc.to_dict() if doc.exists else {"completed": False, "note": "", "timestamp": ""}

def set_cat_status(cat_name, status, note=None):
    safe_id = cat_name.replace("/", "_").replace(" ", "_")
    data = {"completed": status}
    if note is not None:
        data.update({"note": note, "timestamp": get_now()})
    db.collection("settings").document(f"status_{safe_id}").set(data, merge=True)

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
                    current_cats.pop(i); save_categories(current_cats); st.rerun()
                
                new_c_name = st.text_input("Rename:", value=cat['name'], key=f"ren_c_{i}")
                if new_c_name != cat['name'] and st.button(f"Confirm Rename", key=f"cren_{i}"):
                    old = cat['name']; cat['name'] = new_c_name; save_categories(current_cats)
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

# --- MAIN DISPLAY ---
@st.fragment(run_every=5)
def show_tasks():
    # Use .get() to avoid NameError/AttributeError if state isn't ready
    is_admin = st.session_state.get("authenticated", False)
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
                check = st.checkbox("", value=td.get("completed", False), key=f"w_{task.id}_{td.get('completed')}", disabled=(td.get("completed") and not is_admin), label_visibility="collapsed")
                if check != td.get("completed"):
                    db.collection("race_tasks").document(task.id).update({"completed": check}); st.rerun()
            with t_cols[1]: st.markdown(f"### {td['title']}")

# Trigger the main display function
show_tasks()
