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

    keys = ["name", "location", "owner_name", "owner_number", "nearby_places", "notes"]
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

st.title("🏠 PG Manager")

# ---------------- LOAD DATA ----------------
data = sheet.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
    df.columns = df.columns.str.lower().str.strip()

# ---------------- HEADER ----------------
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

st.subheader("🏢 Floors & Rooms")

updated_rooms = []

for i, r in enumerate(st.session_state.rooms):

    st.markdown(f"### 🛏 Room {i+1}")

    col1, col2 = st.columns(2)

    floor = col1.number_input("Floor", 0, 20, value=r["floor"], key=f"floor_{i}")

    # ✅ Auto room number
    default_room = f"{floor}01" if r["room_no"] == "" else r["room_no"]
    room_no = col2.text_input("Room No", value=default_room, key=f"room_{i}")

    col3, col4, col5 = st.columns(3)

    sharing = col3.selectbox(
        "Sharing",
        ["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"],
        index=["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"].index(r["sharing"]),
        key=f"share_{i}"
    )

    max_beds = int(sharing.split()[0])

    total_beds = col4.number_input(
        "Total Beds", 1, max_beds,
        value=min(r["total_beds"], max_beds),
        key=f"tb_{i}"
    )

    available_beds = col5.number_input(
        "Available Beds", 0, total_beds,
        value=min(r["available_beds"], total_beds),
        key=f"ab_{i}"
    )

    # ✅ Validation
    if available_beds > total_beds:
        st.error(f"❌ Room {room_no}: Available beds can't exceed total beds")

    col6, col7 = st.columns(2)

    price = col6.number_input("Price", value=r["price"], key=f"price_{i}")
    deposit = col7.number_input("Deposit", value=r["deposit"], key=f"dep_{i}")

    if st.button("❌ Remove Room", key=f"del_room_{i}"):
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
        "price": 5000,
        "deposit": 2000
    })
    st.rerun()

# ---------------- SUMMARY ----------------
st.subheader("📊 Summary")

total_rooms = len(st.session_state.rooms)
total_beds = sum(r["total_beds"] for r in st.session_state.rooms)
available = sum(r["available_beds"] for r in st.session_state.rooms)

st.info(f"Rooms: {total_rooms} | Beds: {total_beds} | Available: {available}")

# ---------------- FORM ----------------
with st.form("pg_form"):

    name = st.text_input("PG Name", key="name")
    location = st.text_input("Location", key="location")
    owner_name = st.text_input("Owner Name", key="owner_name")
    owner_number = st.text_input("Owner Number", key="owner_number")

    food_type = st.selectbox("Food Type", ["Veg", "Non-Veg", "Mixed"])
    laundry = st.selectbox("Laundry", ["Yes", "No"])

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

# ---------------- PREVIEW ----------------
if preview:
    rating = round((clean + food_rating + safety + value + crowd) / 5, 1)
    st.json({
        "PG Name": name,
        "Location": location,
        "Rooms": st.session_state.rooms,
        "Rating": rating
    })
    st.session_state.preview = True

# ---------------- SAVE ----------------
if save:

    if "preview" not in st.session_state:
        st.error("Click Preview first")
        st.stop()

    # ✅ Duplicate check
    rooms_seen = set()
    for r in st.session_state.rooms:
        key = (r["floor"], r["room_no"])

        if key in rooms_seen:
            st.error(f"❌ Duplicate Room Found: Floor {r['floor']} Room {r['room_no']}")
            st.stop()

        rooms_seen.add(key)

    pg_id = generate_pg_id(df)
    rating = round((clean + food_rating + safety + value + crowd) / 5, 1)

    headers = sheet.row_values(1)

    for room in st.session_state.rooms:

        # ✅ Empty room check
        if not room["room_no"]:
            st.error("Room number required")
            st.stop()

        row_data = {
            "pg_id": pg_id,
            "pg_name": name,
            "location": location,
            "owner_name": owner_name,
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

    st.success(f"✅ Saved {pg_id} with {len(st.session_state.rooms)} rooms")

    # RESET
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