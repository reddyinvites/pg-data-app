import streamlit as st
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

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp_service_account"], scope
)

client = gspread.authorize(creds)
sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").sheet1

# ---------------- SESSION ----------------
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

# ---------------- SAFE RESET ----------------
def reset_form():
    keys = ["floor","room_no","sharing","total_beds","available_beds","price","deposit"]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]

# INIT DEFAULT VALUES
if "floor" not in st.session_state:
    st.session_state.floor = 1
    st.session_state.room_no = "101"
    st.session_state.sharing = "2 Sharing"
    st.session_state.total_beds = 2
    st.session_state.available_beds = 1
    st.session_state.price = 6000
    st.session_state.deposit = 2000

# ---------------- ROOMS ----------------
st.subheader("🛏 Rooms")

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

# ---------------- FORM ----------------
st.markdown("### ✏️ Room Entry")

col1, col2 = st.columns(2)

floor = col1.number_input("Floor", 0, 20, key="floor")

# AUTO ROOM NUMBER (only when not editing)
if st.session_state.edit_index is None:
    st.session_state.room_no = next_room_number(floor)

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

    if st.session_state.edit_index is not None:
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

pg_name = col1.text_input("PG Name")
owner = col2.text_input("Owner Number")

area = st.selectbox("Area", ["Gachibowli", "Kondapur", "Madhapur", "Hitech City"])
locality = st.text_input("Locality")

col3, col4 = st.columns(2)

gender = col3.selectbox("Gender", ["Male", "Female", "Co-Living"])
room_type = col4.selectbox("Room Type", ["AC", "Non AC"])

laundry = st.selectbox("Laundry", ["Yes", "No"])

st.subheader("⭐ Ratings")

food = st.slider("Food", 0, 10, 7)
clean = st.slider("Cleanliness", 0, 10, 7)
safety = st.slider("Safety", 0, 10, 8)

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