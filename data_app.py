import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="PG Manager", layout="wide")

# ---------------- RESET ----------------
def reset_form():
    for key in list(st.session_state.keys()):
        if key.startswith(("floor_", "room_", "share_", "tb_", "ab_", "price_", "dep_")):
            del st.session_state[key]

    keys = ["name", "location", "owner_number"]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

# ---------------- LOGIN ----------------
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

# ---------------- GOOGLE SHEETS ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").sheet1

st.title("🏠 PG Manager - Quick Entry")

# ---------------- LOAD DATA ----------------
data = sheet.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
    df.columns = df.columns.str.lower().str.strip()

def normalize_header(h):
    return h.lower().strip()

# ---------------- PG ID ----------------
def generate_pg_id(df):
    if df.empty or "pg_id" not in df.columns:
        return "PG001"

    nums = []
    for i in df["pg_id"].dropna():
        try:
            nums.append(int(str(i).replace("PG", "")))
        except:
            pass

    return f"PG{max(nums)+1:03d}" if nums else "PG001"

# ---------------- ROOMS ----------------
if "rooms" not in st.session_state:
    st.session_state.rooms = [{
        "floor": 1,
        "room_no": "",
        "sharing": "2 Sharing",
        "total_beds": 2,
        "available_beds": 1,
        "price": 6000,
        "deposit": 2000
    }]

st.subheader("🛏 Rooms")

updated_rooms = []

for i, r in enumerate(st.session_state.rooms):

    col1, col2 = st.columns(2)

    floor = col1.number_input("Floor", 0, 20, value=r["floor"], key=f"floor_{i}")

    # ✅ AUTO ROOM FIX
    auto_room = f"{floor}01"
    if r["room_no"] == "" or r["room_no"].endswith("01"):
        room_val = auto_room
    else:
        room_val = r["room_no"]

    room_no = col2.text_input("Room No", value=room_val, key=f"room_{i}")

    col3, col4, col5 = st.columns(3)

    sharing = col3.selectbox(
        "Sharing",
        ["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"],
        index=["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"].index(r["sharing"]),
        key=f"share_{i}"
    )

    max_beds = int(sharing.split()[0])

    total_beds = col4.number_input("Beds", 1, max_beds, value=r["total_beds"], key=f"tb_{i}")
    available_beds = col5.number_input("Available", 0, total_beds, value=r["available_beds"], key=f"ab_{i}")

    if available_beds > total_beds:
        st.error("Available beds > total beds")

    col6, col7 = st.columns(2)

    # ✅ ₹500 STEP FIX
    price = col6.number_input("Price", min_value=0, step=500, value=r["price"], key=f"price_{i}")
    deposit = col7.number_input("Deposit", min_value=0, step=500, value=r["deposit"], key=f"dep_{i}")

    if st.button("❌ Remove", key=f"del_{i}"):
        if len(st.session_state.rooms) > 1:
            st.session_state.rooms.pop(i)
            st.rerun()

    updated_rooms.append({
        "floor": floor,
        "room_no": room_no,
        "sharing": sharing,
        "total_beds": total_beds,
        "available_beds": available_beds,
        "price": price,
        "deposit": deposit
    })

st.session_state.rooms = updated_rooms

if st.button("➕ Add Room"):
    st.session_state.rooms.append({
        "floor": 1,
        "room_no": "",
        "sharing": "2 Sharing",
        "total_beds": 2,
        "available_beds": 1,
        "price": 6000,
        "deposit": 2000
    })
    st.rerun()

# ---------------- SUMMARY ----------------
st.subheader("📊 Summary")

total_rooms = len(st.session_state.rooms)
total_beds = sum(r["total_beds"] for r in st.session_state.rooms)
available = sum(r["available_beds"] for r in st.session_state.rooms)

st.info(f"Rooms: {total_rooms} | Beds: {total_beds} | Available: {available}")

# ---------------- QUICK FORM ----------------
with st.form("pg_form"):

    col1, col2 = st.columns(2)

    name = col1.text_input("PG Name", key="name")
    location = col2.text_input("Location", key="location")

    owner_number = st.text_input("Owner Number", key="owner_number")

    col3, col4 = st.columns(2)

    gender = col3.selectbox("Gender", ["Male", "Female"])
    room_type = col4.selectbox("Room Type", ["AC", "Non AC"])

    # ✅ Laundry added
    laundry = st.selectbox("Laundry", ["Yes", "No"], index=0)

    preview = st.form_submit_button("👁 Preview")
    save = st.form_submit_button("💾 Save")

# ---------------- DEFAULT ----------------
food_type = "Veg"

# ---------------- PREVIEW ----------------
if preview:
    st.json({
        "PG": name,
        "Location": location,
        "Rooms": st.session_state.rooms
    })
    st.session_state.preview = True

# ---------------- SAVE ----------------
if save:

    if "preview" not in st.session_state:
        st.error("Click Preview first")
        st.stop()

    if not name or not location or not owner_number:
        st.error("Fill required fields")
        st.stop()

    seen = set()
    for r in st.session_state.rooms:
        key = (r["floor"], r["room_no"])
        if key in seen:
            st.error("Duplicate room found")
            st.stop()
        seen.add(key)

    pg_id = generate_pg_id(df)
    headers = sheet.row_values(1)

    for room in st.session_state.rooms:

        row_data = {
            "pg_id": pg_id,
            "pg_name": name,
            "location": location,
            "owner_number": owner_number,

            "floor": room["floor"],
            "room_no": room["room_no"],
            "sharing_type": room["sharing"],
            "total_beds": room["total_beds"],
            "available_beds": room["available_beds"],
            "price": room["price"],
            "deposit": room["deposit"],

            "food_type": food_type,
            "laundry": laundry,
            "room_type": room_type,
            "gender": gender,

            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        final_row = [row_data.get(normalize_header(h), "") for h in headers]
        sheet.append_row(final_row)

    st.success(f"✅ Saved {pg_id}")

    st.session_state.rooms = [{
        "floor": 1,
        "room_no": "",
        "sharing": "2 Sharing",
        "total_beds": 2,
        "available_beds": 1,
        "price": 6000,
        "deposit": 2000
    }]

    reset_form()

    if "preview" in st.session_state:
        del st.session_state.preview

    st.rerun()