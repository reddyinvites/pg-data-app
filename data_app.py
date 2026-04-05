import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="PG Manager", layout="wide")

st.title("🏠 PG Manager - Smart Entry")

# ---------------- GOOGLE SHEETS ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").sheet1

# ---------------- STATE ----------------
if "saved_rooms" not in st.session_state:
    st.session_state.saved_rooms = []

if "current_room" not in st.session_state:
    st.session_state.current_room = {
        "floor": 1,
        "room_no": "101",
        "sharing": "2 Sharing",
        "total_beds": 2,
        "available_beds": 1,
        "price": 6000,
        "deposit": 2000
    }

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None


# ---------------- ROOM NUMBER ----------------
def next_room_number(floor):
    nums = []
    for r in st.session_state.saved_rooms:
        if r["floor"] == floor:
            try:
                nums.append(int(str(r["room_no"])[-2:]))
            except:
                pass

    next_num = max(nums) + 1 if nums else 1
    return f"{floor}{next_num:02d}"


# ---------------- ROOMS ----------------
st.subheader("🛏 Rooms")

# TABLE
if st.session_state.saved_rooms:
    st.markdown("### ✅ Added Rooms")

    for i, r in enumerate(st.session_state.saved_rooms):
        col1, col2, col3, col4, col5 = st.columns([2,2,2,1,1])

        col1.write(f"Room {r['room_no']}")
        col2.write(r["sharing"])
        col3.write(f"₹{r['price']}")

        if col4.button("✏️", key=f"edit_{i}"):
            st.session_state.current_room = r.copy()
            st.session_state.edit_index = i
            st.rerun()

        if col5.button("❌", key=f"del_{i}"):
            st.session_state.saved_rooms.pop(i)
            st.rerun()


# FORM LABEL
if st.session_state.edit_index is not None:
    st.warning("✏️ Editing Room")
else:
    st.info("➕ Add New Room")

# FORM
st.markdown("### ✏️ Room Entry")

r = st.session_state.current_room

col1, col2 = st.columns(2)

floor = col1.number_input("Floor", 0, 20, value=r["floor"], key="floor_input")
room_no = col2.text_input("Room No", value=r["room_no"], key="room_input")

col3, col4, col5 = st.columns(3)

sharing = col3.selectbox(
    "Sharing",
    ["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"],
    index=["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"].index(r["sharing"]),
    key="sharing_input"
)

max_beds = int(sharing.split()[0])

total_beds = col4.number_input("Beds", 1, max_beds, value=r["total_beds"], key="beds_input")
available_beds = col5.number_input("Available", 0, total_beds, value=r["available_beds"], key="avail_input")

col6, col7 = st.columns(2)

price = col6.number_input("Price", 0, step=500, value=r["price"], key="price_input")
deposit = col7.number_input("Deposit", 0, step=500, value=r["deposit"], key="dep_input")


# ADD / UPDATE ROOM
if st.button("➕ Add Room"):

    new_data = {
        "floor": floor,
        "room_no": room_no,
        "sharing": sharing,
        "total_beds": total_beds,
        "available_beds": available_beds,
        "price": price,
        "deposit": deposit
    }

    if st.session_state.edit_index is not None:
        st.session_state.saved_rooms[st.session_state.edit_index] = new_data
        st.session_state.edit_index = None
    else:
        st.session_state.saved_rooms.append(new_data)

    # RESET FORM
    new_room = next_room_number(floor)

    st.session_state.current_room = {
        "floor": floor,
        "room_no": new_room,
        "sharing": "2 Sharing",
        "total_beds": 2,
        "available_beds": 1,
        "price": 6000,
        "deposit": 2000
    }

    st.rerun()


# ---------------- SUMMARY ----------------
st.subheader("📊 Summary")

total_rooms = len(st.session_state.saved_rooms)
total_beds = sum(r["total_beds"] for r in st.session_state.saved_rooms)
available = sum(r["available_beds"] for r in st.session_state.saved_rooms)

st.info(f"Rooms: {total_rooms} | Beds: {total_beds} | Available: {available}")


# ---------------- PG FORM ----------------
st.subheader("🏢 PG Details")

col1, col2 = st.columns(2)

name = col1.text_input("PG Name", key="pg_name_input")
owner_number = col2.text_input("Owner Number", key="owner_input")

area = st.selectbox("Area", ["Gachibowli", "Kondapur", "Madhapur", "Hitech City"], key="area_input")
locality = st.text_input("Locality", key="locality_input")

col3, col4 = st.columns(2)

gender = col3.selectbox("Gender", ["Male", "Female", "Co-Living"], key="gender_input")
room_type = col4.selectbox("Room Type", ["AC", "Non AC"], key="roomtype_input")

laundry = st.selectbox("Laundry", ["Yes", "No"], key="laundry_input")

st.subheader("⭐ Ratings")

food_rating = st.slider("Food", 0, 10, 7, key="food_input")
cleanliness = st.slider("Cleanliness", 0, 10, 7, key="clean_input")
safety = st.slider("Safety", 0, 10, 8, key="safety_input")


# ---------------- FINAL SAVE ----------------
if st.button("🚀 Final Save"):

    if not name or not owner_number:
        st.error("Fill required fields")
    else:

        headers = sheet.row_values(1)

        for room in st.session_state.saved_rooms:

            row_data = {
                "pg_name": name,
                "location": f"{area} - {locality}",
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

            final_row = [row_data.get(h.lower(), "") for h in headers]
            sheet.append_row(final_row)

        st.success("✅ All Data Saved!")

        # RESET FORM
        st.session_state.saved_rooms = []
        st.session_state.current_room = {
            "floor": 1,
            "room_no": "101",
            "sharing": "2 Sharing",
            "total_beds": 2,
            "available_beds": 1,
            "price": 6000,
            "deposit": 2000
        }

        # CLEAR PG FORM
        for key in ["pg_name_input","owner_input","area_input","locality_input",
                    "gender_input","roomtype_input","laundry_input",
                    "food_input","clean_input","safety_input"]:
            if key in st.session_state:
                del st.session_state[key]

        st.rerun()