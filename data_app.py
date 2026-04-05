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

# ---------------- RESET FORM ----------------
def reset_form():
    st.session_state.floor = 1
    st.session_state.room_no = next_room_number(1)
    st.session_state.sharing = "2 Sharing"
    st.session_state.total_beds = 2
    st.session_state.available_beds = 1
    st.session_state.price = 6000
    st.session_state.deposit = 2000

# INIT
if "floor" not in st.session_state:
    reset_form()

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

        # EDIT
        if col4.button("✏️", key=f"edit_{i}"):

            st.session_state.edit_index = i

            st.session_state.floor = r["floor"]
            st.session_state.room_no = r["room_no"]
            st.session_state.sharing = r["sharing"]
            st.session_state.total_beds = r["total_beds"]
            st.session_state.available_beds = r["available_beds"]
            st.session_state.price = r["price"]
            st.session_state.deposit = r["deposit"]

            st.rerun()

        # DELETE
        if col5.button("❌", key=f"del_{i}"):

            st.session_state.saved_rooms.pop(i)

            if st.session_state.edit_index == i:
                st.session_state.edit_index = None

            st.rerun()

# MODE
if st.session_state.edit_index is not None:
    st.warning("✏️ Editing Room")
else:
    st.success("➕ Add New Room")

# ---------------- ROOM FORM ----------------
st.markdown("### ✏️ Room Entry")

col1, col2 = st.columns(2)

floor = col1.number_input("Floor", 0, 20, key="floor")
room_no = col2.text_input("Room No", key="room_no")

col3, col4, col5 = st.columns(3)

sharing = col3.selectbox(
    "Sharing",
    ["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"],
    key="sharing"
)

max_beds = int(sharing.split()[0])

total_beds = col4.number_input("Beds", 1, max_beds, key="total_beds")
available_beds = col5.number_input("Available", 0, total_beds, key="available_beds")

col6, col7 = st.columns(2)

price = col6.number_input("Price", 0, step=500, key="price")
deposit = col7.number_input("Deposit", 0, step=500, key="deposit")

# BUTTON
btn = "💾 Update Room" if st.session_state.edit_index is not None else "➕ Add Room"

if st.button(btn):

    new_data = {
        "floor": floor,
        "room_no": room_no,
        "sharing": sharing,
        "total_beds": total_beds,
        "available_beds": available_beds,
        "price": price,
        "deposit": deposit
    }

    if st.session_state.edit_index is not None and \
       st.session_state.edit_index < len(st.session_state.saved_rooms):

        st.session_state.saved_rooms[st.session_state.edit_index] = new_data
    else:
        st.session_state.saved_rooms.append(new_data)

    st.session_state.edit_index = None

    reset_form()
    st.rerun()

# ---------------- SUMMARY ----------------
st.subheader("📊 Summary")

st.info(
    f"Rooms: {len(st.session_state.saved_rooms)} | "
    f"Beds: {sum(r['total_beds'] for r in st.session_state.saved_rooms)} | "
    f"Available: {sum(r['available_beds'] for r in st.session_state.saved_rooms)}"
)

# ---------------- PG DETAILS ----------------
st.subheader("🏢 PG Details")

col1, col2 = st.columns(2)

pg_name = col1.text_input("PG Name", key="pg_name")
owner = col2.text_input("Owner Number", key="owner")

area = st.selectbox("Area", ["Gachibowli", "Kondapur", "Madhapur", "Hitech City"], key="area")
locality = st.text_input("Locality", key="locality")

col3, col4 = st.columns(2)

gender = col3.selectbox("Gender", ["Male", "Female", "Co-Living"], key="gender")
room_type = col4.selectbox("Room Type", ["AC", "Non AC"], key="room_type")

laundry = st.selectbox("Laundry", ["Yes", "No"], key="laundry")

st.subheader("⭐ Ratings")

food = st.slider("Food", 0, 10, 7, key="food")
clean = st.slider("Cleanliness", 0, 10, 7, key="clean")
safety = st.slider("Safety", 0, 10, 8, key="safety")

# ---------------- SAVE ----------------
if st.button("🚀 Final Save"):

    if not pg_name or not owner:
        st.error("Fill required fields")
    else:

        headers = sheet.row_values(1)

        for r in st.session_state.saved_rooms:

            row_data = {
                "pg_name": pg_name,
                "location": f"{area} - {locality}",
                "owner_number": owner,
                "floor": r["floor"],
                "room_no": r["room_no"],
                "sharing_type": r["sharing"],
                "total_beds": r["total_beds"],
                "available_beds": r["available_beds"],
                "price": r["price"],
                "deposit": r["deposit"],
                "gender": gender,
                "room_type": room_type,
                "laundry": laundry,
                "food_rating": food,
                "cleanliness": clean,
                "safety": safety,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

            final_row = [row_data.get(h.lower(), "") for h in headers]
            sheet.append_row(final_row)

        st.success("✅ Saved Successfully!")

        st.session_state.saved_rooms = []
        st.session_state.edit_index = None

        reset_form()
        st.rerun()