import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

st.set_page_config(page_title="PG Manager", layout="wide")

# -------- RESET FORM --------
def reset_form():
    for key in list(st.session_state.keys()):
        if key.startswith(("type_", "price_", "dep_", "tb_", "ab_")):
            del st.session_state[key]

    keys_to_clear = ["name","location","owner_name","owner_number","nearby_places","notes"]  
    for k in keys_to_clear:  
        if k in st.session_state:  
            del st.session_state[k]

# -------- PHONE VALIDATION (NEW ADDED) --------
def valid_phone(num):
    num = str(num).replace("+91","").strip()
    return num.isdigit() and len(num) == 10

# -------- LOGIN --------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 Admin Login")
    with st.form("login"):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")

        if st.form_submit_button("Login"):  
            if u == "admin" and p == "1234":  
                st.session_state.logged_in = True  
                st.rerun()  
            else:  
                st.error("Invalid credentials")

if not st.session_state.logged_in:
    login()
    st.stop()

# -------- GOOGLE SHEETS --------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").sheet1

st.title("🏠 PG Manager")

# -------- LOAD --------
data = sheet.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
    df.columns = df.columns.str.lower().str.strip()

# -------- HEADER FIX --------
def normalize_header(h):
    h = h.lower().strip()
    mapping = {
        "metro_dist": "metro (m)",
        "bus_dist": "bus (m)",
        "rail_dist": "rail (m)",
        "nearby_places": "nearby places",
        "cleanliness": "clean",
        "food_rating": "food"
    }
    return mapping.get(h, h)

# -------- PG ID --------
def generate_pg_id(df):
    if df.empty or "pg_id" not in df.columns:
        return "PG001"

    nums = []  
    for i in df["pg_id"].dropna():  
        try:  
            nums.append(int(str(i).replace("PG","")))  
        except:  
            pass  

    return f"PG{max(nums)+1:03d}" if nums else "PG001"

# -------- SHARING --------
if "sharing_data" not in st.session_state:
    st.session_state.sharing_data = [{
        "type": "2 Sharing",
        "price": 6000,
        "deposit": 2000,
        "total_beds": 2,
        "available_beds": 1
    }]

st.subheader("🛏 Sharing")

updated = []

for i, s in enumerate(st.session_state.sharing_data):

    col1, col2, col3 = st.columns(3)  

    share_type = col1.selectbox(
        "Type",
        ["1 Sharing","2 Sharing","3 Sharing","4 Sharing"],
        index=["1 Sharing","2 Sharing","3 Sharing","4 Sharing"].index(s["type"]),
        key=f"type_{i}"
    )

    max_beds = int(share_type.split()[0])

    price = col2.number_input("Price", value=s["price"], key=f"price_{i}")
    deposit = col3.number_input("Deposit", value=s["deposit"], key=f"dep_{i}")

    col4, col5, col6 = st.columns(3)

    total_beds = col4.number_input("Total Beds", 1, max_beds, value=min(s["total_beds"], max_beds), key=f"tb_{i}")
    available_beds = col5.number_input("Available Beds", 0, total_beds, value=min(s["available_beds"], total_beds), key=f"ab_{i}")

    if col6.button("❌ Remove", key=f"del_{i}"):
        if len(st.session_state.sharing_data) > 1:
            st.session_state.sharing_data.pop(i)
            st.rerun()

    updated.append({
        "type": share_type,
        "price": price,
        "deposit": deposit,
        "total_beds": total_beds,
        "available_beds": available_beds
    })

st.session_state.sharing_data = updated

if st.button("➕ Add Sharing"):
    st.session_state.sharing_data.append({
        "type": "2 Sharing",
        "price": 5000,
        "deposit": 2000,
        "total_beds": 2,
        "available_beds": 1
    })
    st.rerun()

# -------- FORM --------
with st.form("pg_form"):

    name = st.text_input("PG Name", key="name")  
    location = st.text_input("Location", key="location")  
    owner_name = st.text_input("Owner Name", key="owner_name")  
    owner_number = st.text_input("Owner Number", key="owner_number")  

    food_type = st.selectbox("Food Type", ["Veg","Non-Veg","Mixed"])  
    laundry = st.selectbox("Laundry", ["Yes","No"])  

    room_type = st.selectbox("Room Type", ["AC", "Non AC", "Mixed"])  
    gender = st.selectbox("Gender", ["Male", "Female"])  

    metro_dist = st.number_input("Metro (m)", 0)  
    bus_dist = st.number_input("Bus (m)", 0)  
    rail_dist = st.number_input("Rail (m)", 0)  

    nearby_places = st.text_input("Nearby Places", key="nearby_places")  

    clean = st.slider("Clean", 1, 10)  
    food_rating = st.slider("Food", 1, 10)  
    safety = st.slider("Safety", 1, 10)  
    value = st.slider("Value", 1, 10)  
    crowd = st.slider("Crowd", 1, 10)  

    notes = st.text_area("Notes", key="notes")  

    preview = st.form_submit_button("👁 Preview")  
    save = st.form_submit_button("💾 Save")

# -------- PREVIEW --------
if preview:
    rating = round((clean+food_rating+safety+value+crowd)/5,1)
    st.json({"name": name, "location": location, "rating": rating})
    st.session_state.preview = True

# -------- SAVE --------
if save:

    # ✅ PHONE VALIDATION ADDED HERE
    if not valid_phone(owner_number):
        st.error("❌ Invalid phone number (must be 10 digits)")
        st.stop()

    if "preview" not in st.session_state:
        st.error("Click Preview first")
        st.stop()

    pg_id = generate_pg_id(df)
    rating = round((clean+food_rating+safety+value+crowd)/5,1)

    headers = sheet.row_values(1)

    row_data = {
        "pg_id": pg_id,
        "pg_name": name,
        "location": location,
        "owner_name": owner_name,
        "owner_number": owner_number,
        "sharing_json": json.dumps(st.session_state.sharing_data),
        "food_type": food_type,
        "laundry": laundry,
        "room_type": room_type,
        "gender": gender,
        "metro (m)": metro_dist,
        "bus (m)": bus_dist,
        "rail (m)": rail_dist,
        "nearby places": nearby_places,
        "clean": clean,
        "food": food_rating,
        "safety": safety,
        "value": value,
        "crowd": crowd,
        "rating": rating,
        "notes": notes,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    final_row = [row_data.get(normalize_header(h), "") for h in headers]

    sheet.append_row(final_row)

    st.success(f"✅ Saved {pg_id}")

    # RESET
    st.session_state.sharing_data = [{
        "type": "2 Sharing",
        "price": 6000,
        "deposit": 2000,
        "total_beds": 2,
        "available_beds": 1
    }]

    reset_form()

    if "preview" in st.session_state:
        del st.session_state.preview

    st.rerun()