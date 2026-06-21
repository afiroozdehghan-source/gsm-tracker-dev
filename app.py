import streamlit as st
import requests
from datetime import datetime
import pytz
import pandas as pd

# --- CONFIGURATION ---
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzsELZ5ilySgdnmFns1QjXAfuaL12UBadbOdklF1mkIiKsdYe8AL--uWO5rn2xaXJAMxg/exec" 

USER_CREDENTIALS = {
    "alireza": "admin2026",
    "keno": "keno123",
    "pitse": "pitse123",
    "tshidiso":"tshidiso123",
    "john": "admin123",
    "thabang": "thabang123",
    "khanyisani": "khanyisani123",
    "tshepo": "tshepo123",
    "thabiso": "thabiso123",
    "tiisetso": "tiisetso123",
    "dennis": "dennis123",
    "terrence": "terrence123",
    "malcom": "malcom123"
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
            if u in USER_CREDENTIALS and USER_CREDENTIALS[u] == p:
                st.session_state["logged_in"] = True
                st.session_state["username"] = u
                st.rerun()
            else:
                st.error("Invalid Credentials")
    st.stop()

# --- تابع دریافت زنده دیتای بافر از گوگل شیت ---
@st.cache_data(ttl=1) 
def fetch_live_buffer(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# خواندن زنده کارهای باز کارگاه از کلود
live_tasks = fetch_live_buffer(WEBAPP_URL)

# --- APP INTERFACE ---
st.title("📶 GSM Systems Tracker")
st.write(f"Technician: **{st.session_state['username'].capitalize()}**")

# ایجاد و مدیریت کلیدهای حافظه برای تمام فیلدها
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

# کادر اسکن بارکد
barcode = st.text_input("Scan Barcode (Place cursor here and scan)", key="barcode_input")

# گزینه‌های فعالیت، وضعیت و یادداشت‌ها
activity = st.radio("Activity", ["Screen Test", "Repair", "Soak Test"], horizontal=True, key="activity_input")
status = st.selectbox("Status", ["Started", "Passed", "Failed", "BER"], key="status_input")
comment = st.text_input("Notes", key="notes_input")

# دکمه ثبت
submit = st.button("Submit to Cloud", type="primary", on_click=clear_all_fields)

# 🛠️ نمایش پیغام ثبت موفقیت‌آمیز دقیقاً زیر دکمه (حتی پس از رفرش شدن صفحه)
if "success_msg" in st.session_state:
    st.success(st.session_state["success_msg"])
    st.toast(st.session_state["success_msg"])
    del st.session_state["success_msg"] # پاک کردن از حافظه برای فرم بعدی

# پردازش اطلاعات پس از فشردن دکمه سابمیت
if submit:
    target_barcode = st.session_state.get("barcode_to_submit", "").upper().strip()
    target_activity = st.session_state.get("activity_to_submit", "Screen Test")
    target_status = st.session_state.get("status_to_submit", "Started")
    target_comment = st.session_state.get("notes_to_submit", "")
    
    if target_barcode:
        current_tech = st.session_state["username"].capitalize()
        is_error = False
        
        # پیدا کردن اینکه آیا این قطعه در حال حاضر کارِ بازی در کلود دارد یا خیر
        existing_job = next((item for item in live_tasks if 
                             str(item.get("Unit_Barcode", "")).upper().strip() == target_barcode), None)
        
        # --- سیستم کنترل خطای زنده، سه قفله و کاملاً کالیبره شده ---
        if target_status == "Started":
            if existing_job:
                st.error(f"❌ Error: Unit {target_barcode} is ALREADY ACTIVE! Started by {existing_job.get('Technician', 'someone')} for '{existing_job.get('Activity_Type', 'an activity')}'. Finish that first!")
                is_error = True
        else:
            if not existing_job:
                st.error(f"❌ CRITICAL ERROR: No active 'Started' log found for unit {target_barcode}. You must start the task first!")
                is_error = True
            else:
                opened_activity = str(existing_job.get("Activity_Type", "")).lower().strip()
                current_activity = target_activity.lower().strip()
                if opened_activity != current_activity:
                    st.error(f"❌ CRITICAL ERROR: Unit {target_barcode} is currently open for '{existing_job.get('Activity_Type', '')}'. You cannot submit a completion status for '{target_activity}'!")
                    is_error = True
        # -------------------------------------------------------------------------------------
        
        # ارسال نهایی به کلود در صورت نبود خطای منطقی
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
                "Technician_Comment": target_comment  
            }
            
            with st.spinner("Syncing to cloud database..."):
                try:
                    response = requests.post(WEBAPP_URL, json=payload, timeout=10)
                    if response.status_code == 200:
                        # ذخیره پیغام در حافظه سشن قبل از رفرش تا بعد از رفرش نمایش داده شود
                        st.session_state["success_msg"] = f"✅ Data successfully synced! Unit: {target_barcode} ({target_activity} -> {target_status})"
                        st.cache_data.clear() 
                        st.rerun()
                    else:
                        st.error("⚠️ Connection successful but Cloud rejected the data.")
                except Exception as e:
                    st.error(f"Error connecting to Cloud: {e}")
    else:
        st.error("Barcode is required! Please scan a unit first.")

# --- مانیتورینگ زنده کارگاه (نمایش شیک جدول کارهای فعال) ---
st.markdown("---")
st.subheader("⏳ Live Workshop Monitor (Active Tasks from Cloud)")

if not live_tasks:
    st.info("No active units currently in progress. All clear in the workshop!")
else:
    df_display = pd.DataFrame(live_tasks)
    if not df_display.empty and "Unit_Barcode" in df_display.columns:
        df_display = df_display[["Unit_Barcode", "Technician", "Activity_Type", "Start_Time"]]
        df_display.columns = ["Unit Barcode", "Technician", "Current Activity", "Started At"]
        st.dataframe(df_display, use_container_width=True)
    else:
        st.info("No active units currently in progress. All clear in the workshop!")
