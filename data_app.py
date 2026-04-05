import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="PG Manager", layout="wide")

# ---------------- GOOGLE SHEETS ----------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").sheet1

st.title("🏠 PG Manager - Smart Entry")

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
    all_rooms = st.session_state.saved_rooms

    nums = []
    for r in all_rooms:
        if r["floor"] == floor:
            try:
                nums.append(int(str(r["room_no"])[-2:]))
            except:
                pass

    next_num = max(nums) + 1 if nums else 1
    return f"{floor}{next_num:02d}"


# ---------------- ROOMS ----------------
st.subheader("🛏 Rooms")

# ---------- TABLE ----------
if st.session_state.saved_rooms:

    st.markdown("### ✅ Added Rooms")

    for i, r in enumerate(st.session_state.saved_rooms):

        col1, col2, col3, col4, col5 = st.columns([2,2,2,1,1])

        col1.write(f"**Room {r['room_no']}**")
        col2.write(r["sharing"])
        col3.write(f"₹{r['price']}")

        # EDIT
        if col4.button("✏️", key=f"edit_{i}"):
            st.session_state.current_room = r
            st.session_state.edit_index = i
            st.rerun()

        # DELETE
        if col5.button("❌", key=f"del_{i}"):
            st.session_state.saved_rooms.pop(i)
            st.rerun()


# ---------- FORM ----------
st.markdown("### ✏️ Room Entry")

r = st.session_state.current_room

col1, col2 = st.columns(2)

floor = col1.number_input("Floor", 0, 20, value=r["floor"])

room_no = col2.text_input("Room No", value=r["room_no"])

col3, col4, col5 = st.columns(3)

sharing = col3.selectbox(
    "Sharing",
    ["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"],
    index=["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"].index(r["sharing"])
)

max_beds = int(sharing.split()[0])

total_beds = col4.number_input("Beds", 1, max_beds, value=r["total_beds"])
available_beds = col5.number_input("Available", 0, total_beds, value=r["available_beds"])

col6, col7 = st.columns(2)

price = col6.number_input("Price", 0, step=500, value=r["price"])
deposit = col7.number_input("Deposit", 0, step=500, value=r["deposit"])


# ---------- ADD / UPDATE ----------
if st.button("💾 Save Room"):

    new_data = {
        "floor": floor,
        "room_no": room_no,
        "sharing": sharing,
        "total_beds": total_beds,
        "available_beds": available_beds,
        "price": price,
        "deposit": deposit
    }

    # EDIT MODE
    if st.session_state.edit_index is not None:
        st.session_state.saved_rooms[st.session_state.edit_index] = new_data
        st.session_state.edit_index = None

    # NEW ROOM
    else:
        st.session_state.saved_rooms.append(new_data)

    # RESET FORM
    new_room_no = next_room_number(floor)

    st.session_state.current_room = {
        "floor": floor,
        "room_no": new_room_no,
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


# ---------------- SAVE TO GOOGLE SHEET ----------------
if st.button("🚀 Final Save to Google Sheet"):

    headers = sheet.row_values(1)

    for room in st.session_state.saved_rooms:

        row = [
            room["floor"],
            room["room_no"],
            room["sharing"],
            room["total_beds"],
            room["available_beds"],
            room["price"],
            room["deposit"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        sheet.append_row(row)

    st.success("✅ All Rooms Saved!")