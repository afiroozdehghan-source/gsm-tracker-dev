import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

# --- CONFIGURATION ---
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbyCGq2smaWEEP3rMGNtLRVi3Ye9HRl4EnUkhKtOwRHGo7J3mk3XIEfNmDxG4xlQ8Gcm/exec" 

# ساختار اطلاعات کاربران و پروژه‌ها
USER_DATA = {
    "alireza": {"password": "admin2026", "project": "All", "role": "admin"},
    "john": {"password": "admin123", "project": "All", "role": "admin"},
    "keno": {"password": "keno123", "project": "Vodacom", "role": "tech"},
    "pitse": {"password": "pitse123", "project": "Vodacom", "role": "tech"},
    "tshidiso": {"password": "tshidiso123", "project": "Vodacom", "role": "tech"},
    "thabang": {"password": "thabang123", "project": "Vodacom", "role": "tech"},
    "khanyisani": {"password": "khanyisani123", "project": "Vodacom", "role": "tech"},
    "tshepo": {"password": "tshepo123", "project": "Vodacom", "role": "tech"},
    "dennis": {"password": "dennis123", "project": "Vodacom", "role": "tech"},
    "terrence": {"password": "terrence123", "project": "Vodacom", "role": "tech"},
    "malcom": {"password": "malcom123", "project": "Vodacom", "role": "tech"},
    "thabiso": {"password": "thabiso123", "project": "Infinity", "role": "tech"},
    "tiisetso": {"password": "tiisetso123", "project": "Infinity", "role": "tech"}
}

st.set_page_config(page_title="GSM Systems Cloud", page_icon="📶")

# --- LOGIN LOGIC ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("📶 GSM Systems Cloud Login")
    with st.form("login"):
        u = st.text_input("Username").lower()
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if u in USER_DATA and USER_DATA[u]["password"] == p:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.session_state["project"] = USER_DATA[u]["project"]
                st.session_state["role"] = USER_DATA[u]["role"]
                st.rerun()
            else:
                st.error("Invalid Credentials")
    st.stop()

# --- FETCH DATA ---
@st.cache_data(ttl=1) 
def fetch_live_buffer(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

live_tasks = fetch_live_buffer(WEBAPP_URL)

# --- APP INTERFACE ---
st.title("📶 GSM Systems Tracker")
st.write(f"User: **{st.session_state['username'].capitalize()}** | Project: **{st.session_state['project']}**")

# مدیریت حافظه فیلدها
if "barcode_input" not in st.session_state:
    st.session_state["barcode_input"] = ""
if "activity_input" not in st.session_state:
    st.session_state["activity_input"] = "Screen Test"
if "status_input" not in st.session_state:
    st.session_state["status_input"] = "Started"
if "notes_input" not in st.session_state:
    st.session_state["notes_input"] = ""

def clear_all_fields():
    st.session_state["barcode_to_submit"] = st.session_state["barcode_input"]
    st.session_state["activity_to_submit"] = st.session_state["activity_input"]
    st.session_state["status_to_submit"] = st.session_state["status_input"]
    st.session_state["notes_to_submit"] = st.session_state["notes_input"]
    
    st.session_state["barcode_input"] = ""
    st.session_state["activity_input"] = "Screen Test"
    st.session_state["status_input"] = "Started"
    st.session_state["notes_input"] = ""

# فرم ثبت
barcode = st.text_input("Scan Barcode (Place cursor here and scan)", key="barcode_input")
activity = st.radio("Activity", ["Screen Test", "Repair", "Soak Test"], horizontal=True, key="activity_input")
status = st.selectbox("Status", ["Started", "Passed", "Failed", "BER"], key="status_input")
comment = st.text_input("Notes", key="notes_input")

submit = st.button("Submit to Cloud", type="primary", on_click=clear_all_fields)

if "success_msg" in st.session_state:
    st.success(st.session_state["success_msg"])
    st.toast(st.session_state["success_msg"])
    del st.session_state["success_msg"]

# پردازش ثبت
if submit:
    target_barcode = st.session_state.get("barcode_to_submit", "").upper().strip()
    target_activity = st.session_state.get("activity_to_submit", "Screen Test")
    target_status = st.session_state.get("status_to_submit", "Started")
    target_comment = st.session_state.get("notes_to_submit", "")
    
    if target_barcode:
        current_tech = st.session_state["username"].capitalize()
        is_error = False
        
        # چک کردن کارهای فعال (بر اساس پروژه)
        existing_job = next((item for item in live_tasks if str(item.get("Unit_Barcode", "")).upper().strip() == target_barcode), None)
        
        if target_status == "Started":
            if existing_job:
                st.error(f"❌ Error: Unit {target_barcode} is ALREADY ACTIVE in {existing_job.get('Project', 'a project')}!")
                is_error = True
        else:
            if not existing_job:
                st.error(f"❌ CRITICAL ERROR: Unit {target_barcode} is not active. Start it first!")
                is_error = True
        
        if not is_error:
            sa_tz = pytz.timezone('Africa/Johannesburg')
            now_sa = datetime.now(sa_tz)
            
            payload = {
                "Timestamp": now_sa.strftime("%Y-%m-%d %H:%M:%S"),
                "Date": now_sa.strftime("%Y-%m-%d"),
                "Time": now_sa.strftime("%H:%M:%S"),
                "Technician": current_tech,
                "Unit_Barcode": target_barcode,
                "Activity_Type": target_activity,  
                "Status": target_status,          
                "Technician_Comment": target_comment,
                "Project": st.session_state["project"] # ارسال پروژه به کلود
            }
            
            with st.spinner("Syncing..."):
                try:
                    response = requests.post(WEBAPP_URL, json=payload, timeout=10)
                    if response.status_code == 200:
                        st.session_state["success_msg"] = f"✅ Success! Unit: {target_barcode} ({target_activity})"
                        st.cache_data.clear() 
                        st.rerun()
                    else:
                        st.error("⚠️ Connection successful but Cloud rejected the data.")
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        st.error("Barcode is required!")

# --- MONITORING ---
st.markdown("---")
st.subheader("⏳ Live Workshop Monitor")

# فیلتر کردن لیست برای نمایش
if st.session_state["role"] == "admin":
    display_tasks = live_tasks
else:
    # فیلتر بر اساس پروژه کاربر
    display_tasks = [t for t in live_tasks if t.get("Project") == st.session_state["project"]]

if not display_tasks:
    st.info(f"No active units for {st.session_state['project']} project.")
else:
    df_display = pd.DataFrame(display_tasks)
    # نمایش ستون‌ها با اضافه کردن Project برای ادمین‌ها
    cols_to_show = ["Unit_Barcode", "Technician", "Project", "Activity_Type", "Start_Time"]
    df_display = df_display[cols_to_show]
    df_display.columns = ["Unit Barcode", "Technician", "Project", "Current Activity", "Started At"]
    st.dataframe(df_display, use_container_width=True)
