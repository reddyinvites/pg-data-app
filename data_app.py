import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="PG Manager", layout="wide")

# ---------------- RESET ----------------
def reset_form():
    for key in list(st.session_state.keys()):
        if key.startswith(("floor_", "room_", "share_", "tb_", "ab_", "price_", "dep_", "last_floor_")):
            del st.session_state[key]

    for k in ["name", "owner_number"]:
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

st.title("🏠 PG Manager - Smart Entry")

# ---------------- LOAD ----------------
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


# ---------------- ROOM NUMBER ----------------
def generate_room_number(floor, rooms):
    floor_rooms = [r for r in rooms if r["floor"] == floor]

    nums = []
    for r in floor_rooms:
        try:
            nums.append(int(str(r["room_no"])[-2:]))
        except:
            pass

    next_num = max(nums) + 1 if nums else 1
    return f"{floor}{next_num:02d}"


# ---------------- ROOMS ----------------
if "rooms" not in st.session_state:
    st.session_state.rooms = [{
        "floor": 1,
        "room_no": "101",
        "sharing": "2 Sharing",
        "total_beds": 2,
        "available_beds": 1,
        "price": 6000,
        "deposit": 2000
    }]

st.subheader("🛏 Rooms")

for i in range(len(st.session_state.rooms)):
    r = st.session_state.rooms[i]

    with st.container():
        st.markdown(f"### Room {i+1}")
        st.divider()

        col1, col2 = st.columns(2)

        floor = col1.number_input("Floor", 0, 20, value=r["floor"], key=f"floor_{i}")

        room_key = f"room_{i}"
        last_floor_key = f"last_floor_{i}"

        if room_key not in st.session_state:
            st.session_state[room_key] = r["room_no"]
            st.session_state[last_floor_key] = floor

        if st.session_state.get(last_floor_key) != floor:
            new_room = generate_room_number(floor, st.session_state.rooms)

            if st.session_state[room_key] == r["room_no"]:
                st.session_state[room_key] = new_room

            st.session_state[last_floor_key] = floor

        room_no = col2.text_input("Room No", key=room_key)

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

        col6, col7 = st.columns(2)

        price = col6.number_input("Price", min_value=0, step=500, value=r["price"], key=f"price_{i}")
        deposit = col7.number_input("Deposit", min_value=0, step=500, value=r["deposit"], key=f"dep_{i}")

        if st.button("❌ Remove Room", key=f"del_{i}"):
            if len(st.session_state.rooms) > 1:
                st.session_state.rooms.pop(i)
                st.rerun()

        st.session_state.rooms[i] = {
            "floor": floor,
            "room_no": st.session_state[room_key],
            "sharing": sharing,
            "total_beds": total_beds,
            "available_beds": available_beds,
            "price": price,
            "deposit": deposit
        }

# ADD ROOM
if st.button("➕ Add Room"):
    last_floor = st.session_state.rooms[-1]["floor"]
    new_room = generate_room_number(last_floor, st.session_state.rooms)

    st.session_state.rooms.append({
        "floor": last_floor,
        "room_no": new_room,
        "sharing": "2 Sharing",
        "total_beds": 2,
        "available_beds": 1,
        "price": 6000,
        "deposit": 2000
    })
    st.rerun()


# ---------------- SUMMARY ----------------
st.subheader("📊 Summary")

st.info(
    f"Rooms: {len(st.session_state.rooms)} | "
    f"Beds: {sum(r['total_beds'] for r in st.session_state.rooms)} | "
    f"Available: {sum(r['available_beds'] for r in st.session_state.rooms)}"
)


# ---------------- FORM ----------------
with st.form("pg_form"):

    col1, col2 = st.columns(2)

    name = col1.text_input("PG Name", key="name")
    owner_number = col2.text_input("Owner Number", key="owner_number")

    area = st.selectbox("Area", ["Gachibowli", "Kondapur", "Madhapur", "Hitech City"])

    locality = st.text_input("Locality")

    location = f"{area} - {locality}"

    col3, col4 = st.columns(2)

    gender = col3.selectbox("Gender", ["Male", "Female", "Co-Living"])
    room_type = col4.selectbox("Room Type", ["AC", "Non AC"])

    laundry = st.selectbox("Laundry", ["Yes", "No"])

    st.subheader("🍽 Ratings")

    food_rating = st.slider("Food", 0, 10, 7)
    cleanliness = st.slider("Cleanliness", 0, 10, 7)
    safety = st.slider("Safety", 0, 10, 8)

    save = st.form_submit_button("💾 Save")


# ---------------- SAVE ----------------
if save:

    if not name or not owner_number:
        st.error("Fill required fields")
        st.stop()

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
            "gender": gender,
            "room_type": room_type,
            "laundry": laundry,
            "food_rating": food_rating,
            "cleanliness": cleanliness,
            "safety": safety,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        final_row = [row_data.get(normalize_header(h), "") for h in headers]
        sheet.append_row(final_row)

    st.success(f"✅ Saved {pg_id}")

    reset_form()
    st.session_state.rooms = [{
        "floor": 1,
        "room_no": "101",
        "sharing": "2 Sharing",
        "total_beds": 2,
        "available_beds": 1,
        "price": 6000,
        "deposit": 2000
    }]

    st.rerun()