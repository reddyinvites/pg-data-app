import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="PG Manager", layout="wide")
st.title("🏠 PG Manager - Smart Entry")

# ---------------- CONFIG ----------------
SHEET_ID = "1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ---------------- CACHE ----------------
@st.cache_resource
def get_client():
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        dict(st.secrets["gcp_service_account"]), scope
    )
    return gspread.authorize(creds)

@st.cache_resource
def get_sheets():
    client = get_client()
    sh = client.open_by_key(SHEET_ID)
    return sh.sheet1, sh.worksheet("Areas")

sheet, area_sheet = get_sheets()

# ---------------- PG ID ----------------
def generate_pg_id(sheet):
    try:
        col = sheet.col_values(1)
        ids = [c for c in col if str(c).startswith("PG")]

        if not ids:
            return "PG0001"

        nums = []
        for i in ids:
            try:
                nums.append(int(i.replace("PG","")))
            except:
                pass

        return f"PG{max(nums)+1:04d}"
    except:
        return "PG0001"

# ---------------- AREA DATA ----------------
@st.cache_data(ttl=60)
def load_area_data():
    data = area_sheet.get_all_values()
    m = {}

    for row in data:
        if len(row) < 2:
            continue
        a, l = row[0].strip(), row[1].strip()
        if a and l:
            m.setdefault(a, [])
            if l not in m[a]:
                m[a].append(l)

    return m

area_locality_map = load_area_data()
area_list = list(area_locality_map.keys())

# ---------------- SESSION ----------------
if "saved_rooms" not in st.session_state:
    st.session_state.saved_rooms = []

if "edit_index" not in st.session_state:
    st.session_state.edit_index = None

# DEFAULTS
if "floor" not in st.session_state:
    st.session_state.update({
        "floor":1,"room_no":"101","sharing":2,
        "total_beds":1,"available_beds":0,
        "price":6000,"deposit":2000
    })

# ---------------- ROOMS ----------------
st.subheader("🛏 Rooms")

for i, r in enumerate(st.session_state.saved_rooms):
    c1,c2,c3,c4,c5 = st.columns([2,2,2,1,1])
    c1.write(f"Room {r['room_no']}")
    c2.write(f"{r['sharing']} Sharing")
    c3.write(f"₹{r['price']}")

    if c4.button("✏️", key=f"edit{i}"):
        st.session_state.edit_index = i
        for k in r:
            st.session_state[k] = r[k]
        st.rerun()

    if c5.button("❌", key=f"del{i}"):
        st.session_state.saved_rooms.pop(i)
        st.rerun()

# ---------------- FORM ----------------
st.markdown("### ✏️ Room Entry")

c1,c2 = st.columns(2)
floor = c1.number_input("Floor",0,20,key="floor")

if st.session_state.edit_index is None:
    nums = [int(str(r["room_no"])[-2:]) for r in st.session_state.saved_rooms if r["floor"]==floor]
    st.session_state.room_no = f"{floor}{(max(nums)+1 if nums else 1):02d}"

room_no = c2.text_input("Room No",key="room_no")

c3,c4,c5 = st.columns(3)
sharing = c3.selectbox("Sharing",[1,2,3,4],format_func=lambda x:f"{x} Sharing",key="sharing")

if st.session_state.total_beds > sharing:
    st.session_state.total_beds = sharing

total_beds = c4.number_input("Beds",1,sharing,key="total_beds")

if st.session_state.available_beds > total_beds:
    st.session_state.available_beds = total_beds

available_beds = c5.number_input("Available",0,total_beds,key="available_beds")

c6,c7 = st.columns(2)
price = c6.number_input("Price",0,step=500,key="price")
deposit = c7.number_input("Deposit",0,step=500,key="deposit")

if st.button("💾 Save Room"):
    data = {
        "floor":floor,"room_no":room_no,"sharing":sharing,
        "total_beds":total_beds,"available_beds":available_beds,
        "price":price,"deposit":deposit
    }

    if st.session_state.edit_index is not None:
        st.session_state.saved_rooms[st.session_state.edit_index] = data
    else:
        st.session_state.saved_rooms.append(data)

    st.session_state.edit_index = None
    st.rerun()

st.markdown("---")

# ---------------- PG DETAILS ----------------
st.subheader("🏢 PG Details")

pg_name = st.text_input("PG Name")
owner = st.text_input("Owner Number")

area = st.selectbox("Area", area_list)
locality = st.selectbox("Locality", area_locality_map.get(area, []))

# ➕ ADD LOCALITY
with st.expander("➕ Add New Locality"):
    na = st.text_input("Area", key="na")
    nl = st.text_input("Locality", key="nl")

    if st.button("Add Locality"):
        if not na or not nl:
            st.error("Enter both")
        elif nl in area_locality_map.get(na, []):
            st.warning("Exists")
        else:
            area_sheet.append_row([na, nl])
            load_area_data.clear()
            st.success("Added!")
            st.rerun()

# ✏️ EDIT DELETE
with st.expander("✏️ Manage Localities"):
    ma = st.selectbox("Area", area_list, key="ma")
    locs = area_locality_map.get(ma, [])

    if locs:
        ml = st.selectbox("Locality", locs, key="ml")
        new = st.text_input("Edit", value=ml)

        cA,cB = st.columns(2)

        if cA.button("Update"):
            rows = area_sheet.get_all_values()
            for i,r in enumerate(rows,1):
                if len(r)>=2 and r[0]==ma and r[1]==ml:
                    area_sheet.update_cell(i,2,new)
                    break
            load_area_data.clear()
            st.rerun()

        if cB.button("Delete"):
            rows = area_sheet.get_all_values()
            for i,r in enumerate(rows,1):
                if len(r)>=2 and r[0]==ma and r[1]==ml:
                    area_sheet.delete_rows(i)
                    break
            load_area_data.clear()
            st.rerun()

gender = st.selectbox("Gender",["Male","Female","Co-Living"])
room_type = st.selectbox("Room Type",["AC","Non AC"])
laundry = st.selectbox("Laundry",["Yes","No"])
food_type = st.selectbox("Food Type",["Veg","Non Veg","Both"])

st.subheader("⭐ Ratings")
food = st.slider("Food",0,10,7)
clean = st.slider("Cleanliness",0,10,7)
safety = st.slider("Safety",0,10,8)

# ---------------- SAVE ----------------
if st.button("🚀 Final Save"):

    headers = sheet.row_values(1)
    pg_id = generate_pg_id(sheet)

    for r in st.session_state.saved_rooms:
        row = {
            "pg_id":pg_id,
            "pg_name":pg_name,
            "location":f"{area}-{locality}",
            "owner_number":owner,
            "floor":r["floor"],
            "room_no":r["room_no"],
            "sharing_type":f"{r['sharing']} Sharing",
            "total_beds":r["total_beds"],
            "available_beds":r["available_beds"],
            "price":r["price"],
            "deposit":r["deposit"],
            "gender":gender,
            "room_type":room_type,
            "laundry":laundry,
            "food_type":food_type,
            "food_rating":food,
            "cleanliness":clean,
            "safety":safety,
            "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        sheet.append_row([row.get(h.lower(),"") for h in headers])

    st.success("✅ Saved!")
    st.session_state.saved_rooms = []
    st.rerun()