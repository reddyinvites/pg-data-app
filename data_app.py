import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="PG Manager", layout="wide")
st.title("🏠 PG Manager - Smart Entry")

# ---------------- GOOGLE SHEETS ----------------
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

try:
    creds = ServiceAccountCredentials.from_json_keyfile_dict(
        dict(st.secrets["gcp_service_account"]), scope
    )
    client = gspread.authorize(creds)

    sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").sheet1
    area_sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").worksheet("Areas")

except Exception as e:
    st.error("❌ Google Sheets connection failed")
    st.write(e)
    st.stop()

# ---------------- LOAD AREA DATA ----------------
data = area_sheet.get_all_values()
area_locality_map = {}

for row in data:
    if len(row) < 2:
        continue
    a, l = row[0].strip(), row[1].strip()
    if a and l:
        area_locality_map.setdefault(a, [])
        if l not in area_locality_map[a]:
            area_locality_map[a].append(l)

area_list = list(area_locality_map.keys())

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

# ---------------- RESET ----------------
def reset_form():
    for k in ["floor","room_no","sharing","total_beds","available_beds","price","deposit"]:
        if k in st.session_state:
            del st.session_state[k]

# INIT DEFAULTS
if "floor" not in st.session_state:
    st.session_state.update({
        "floor":1,"room_no":"101","sharing":"2 Sharing",
        "total_beds":2,"available_beds":1,"price":6000,"deposit":2000
    })

# ---------------- ROOMS ----------------
st.subheader("🛏 Rooms")

if st.session_state.saved_rooms:
    for i, r in enumerate(st.session_state.saved_rooms):
        c1,c2,c3,c4,c5 = st.columns([2,2,2,1,1])
        c1.write(f"Room {r['room_no']}")
        c2.write(r["sharing"])
        c3.write(f"₹{r['price']}")

        if c4.button("✏️", key=f"e{i}"):
            st.session_state.edit_index=i
            for k in r: st.session_state[k]=r[k]
            st.rerun()

        if c5.button("❌", key=f"d{i}"):
            st.session_state.saved_rooms.pop(i)
            st.rerun()

# ---------------- FORM ----------------
st.markdown("### ✏️ Room Entry")
c1,c2 = st.columns(2)

floor = c1.number_input("Floor",0,20,key="floor")

if st.session_state.edit_index is None:
    st.session_state.room_no = next_room_number(floor)

room_no = c2.text_input("Room No",key="room_no")

c3,c4,c5 = st.columns(3)
sharing = c3.selectbox("Sharing",["1 Sharing","2 Sharing","3 Sharing","4 Sharing"],key="sharing")

max_beds=int(sharing.split()[0])
total_beds=c4.number_input("Beds",1,max_beds,key="total_beds")
available_beds=c5.number_input("Available",0,total_beds,key="available_beds")

c6,c7 = st.columns(2)
price=c6.number_input("Price",0,step=500,key="price")
deposit=c7.number_input("Deposit",0,step=500,key="deposit")

if st.button("💾 Save Room"):
    data={
        "floor":floor,"room_no":room_no,"sharing":sharing,
        "total_beds":total_beds,"available_beds":available_beds,
        "price":price,"deposit":deposit
    }

    if st.session_state.edit_index is not None:
        st.session_state.saved_rooms[st.session_state.edit_index]=data
    else:
        st.session_state.saved_rooms.append(data)

    st.session_state.edit_index=None
    reset_form()
    st.rerun()

st.markdown("---")

# ---------------- PG DETAILS ----------------
st.subheader("🏢 PG Details")

c1,c2 = st.columns(2)
pg_name=c1.text_input("PG Name")
owner=c2.text_input("Owner Number")

# DROPDOWN
area = st.selectbox("Area", area_list, key="area")
localities = area_locality_map.get(area, [])
locality = st.selectbox("Locality", localities, key="locality")

# ➕ ADD
with st.expander("➕ Add New Locality"):
    na=st.text_input("Area",key="na")
    nl=st.text_input("Locality",key="nl")

    if st.button("Add"):
        if nl in area_locality_map.get(na,[]):
            st.warning("Exists!")
        else:
            area_sheet.append_row([na,nl])
            area_locality_map.setdefault(na,[]).append(nl)
            if na not in area_list: area_list.append(na)
            st.session_state.area=na
            st.session_state.locality=nl
            st.rerun()

# ✏️ DELETE
with st.expander("✏️ Manage Localities"):
    a=st.selectbox("Area",area_list,key="ma")
    locs=area_locality_map.get(a,[])

    if locs:
        l=st.selectbox("Locality",locs,key="ml")
        new=st.text_input("Edit",value=l)

        cA,cB=st.columns(2)

        if cA.button("Update"):
            rows=area_sheet.get_all_values()
            for i,r in enumerate(rows,1):
                if len(r)>=2 and r[0]==a and r[1]==l:
                    area_sheet.update_cell(i,2,new)
                    break
            area_locality_map[a][area_locality_map[a].index(l)]=new
            st.rerun()

        if cB.button("Delete"):
            rows=area_sheet.get_all_values()
            for i,r in enumerate(rows,1):
                if len(r)>=2 and r[0]==a and r[1]==l:
                    area_sheet.delete_rows(i)
                    break
            area_locality_map[a].remove(l)
            st.rerun()

# ---------------- EXTRA ----------------
c3,c4 = st.columns(2)
gender=c3.selectbox("Gender",["Male","Female","Co-Living"])
room_type=c4.selectbox("Room Type",["AC","Non AC"])
laundry=st.selectbox("Laundry",["Yes","No"])

st.subheader("⭐ Ratings")
food=st.slider("Food",0,10,7)
clean=st.slider("Clean",0,10,7)
safety=st.slider("Safety",0,10,8)

# ---------------- SAVE ----------------
if st.button("🚀 Final Save"):
    headers=sheet.row_values(1)

    for r in st.session_state.saved_rooms:
        row={
            "pg_name":pg_name,
            "location":f"{area}-{locality}",
            "owner_number":owner,
            "floor":r["floor"],
            "room_no":r["room_no"],
            "sharing_type":r["sharing"],
            "total_beds":r["total_beds"],
            "available_beds":r["available_beds"],
            "price":r["price"],
            "deposit":r["deposit"],
            "gender":gender,
            "room_type":room_type,
            "laundry":laundry,
            "food_rating":food,
            "cleanliness":clean,
            "safety":safety,
            "timestamp":datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        sheet.append_row([row.get(h.lower(),"") for h in headers])

    st.success("✅ Saved!")
    st.session_state.saved_rooms=[]
    reset_form()
    st.rerun()