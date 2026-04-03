import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

st.set_page_config(page_title="PG Manager", layout="wide")

-------- RESET FORM --------

def reset_form():
for key in list(st.session_state.keys()):
if key.startswith(("type_", "price_", "dep_", "tb_", "ab_")):
del st.session_state[key]

keys_to_clear = ["name","location","owner_name","owner_number","nearby_places","notes"]
for k in keys_to_clear:
if k in st.session_state:
del st.session_state[k]

-------- LOGIN --------

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

-------- GOOGLE SHEETS --------

scope = [
"https://spreadsheets.google.com/feeds",
"https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").sheet1

st.title("🏠 PG Manager")

-------- LOAD --------

data = sheet.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
df.columns = df.columns.str.lower().str.strip()

-------- HEADER FIX --------

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

-------- PG ID --------

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

-------- SHARING --------

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

-------- FORM --------

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

-------- PREVIEW --------

if preview:
rating = round((clean+food_rating+safety+value+crowd)/5,1)
st.json({"name": name, "location": location, "rating": rating})
st.session_state.preview = True

-------- SAVE --------

if save:

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

RESET

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

-------- TABLE --------

st.subheader("📊 PG Table")

if df.empty:
st.warning("No data")
else:
cols = ["pg_id","pg_name","location","food_type","room_type","gender","laundry","rating"]
available = [c for c in cols if c in df.columns]
st.dataframe(df[available], use_container_width=True)

-------- ACTIONS --------

st.subheader("⚙️ Actions")

if not df.empty:
selected = st.selectbox("Select PG", df.index)

col1, col2 = st.columns(2)

if col1.button("🗑 Delete"):
sheet.delete_rows(selected+2)
st.rerun()

if col2.button("✏️ Edit"):
st.session_state.edit_index = selected

-------- EDIT --------

if "edit_index" in st.session_state:

i = st.session_state.edit_index
row = df.loc[i]

st.subheader("✏️ Edit PG")

new_name = st.text_input("PG Name", row.get("pg_name",""))
new_location = st.text_input("Location", row.get("location",""))
new_owner = st.text_input("Owner Name", row.get("owner_name",""))
new_number = st.text_input("Owner Number", row.get("owner_number",""))

new_food = st.selectbox("Food", ["Veg","Non-Veg","Mixed"])
new_laundry = st.selectbox("Laundry", ["Yes","No"])
new_room = st.selectbox("Room Type", ["AC","Non AC","Mixed"])

existing_gender = row.get("gender","Male")
if existing_gender not in ["Male","Female"]:
existing_gender = "Male"

new_gender = st.selectbox("Gender", ["Male","Female"],
index=["Male","Female"].index(existing_gender)
)

new_metro = st.number_input("Metro", int(row.get("metro (m)",0)))
new_bus = st.number_input("Bus", int(row.get("bus (m)",0)))
new_rail = st.number_input("Rail", int(row.get("rail (m)",0)))

new_near = st.text_input("Nearby", row.get("nearby places",""))

new_clean = st.slider("Clean", 1, 10, int(row.get("clean",1)))
new_food_rating = st.slider("Food Rating", 1, 10, int(row.get("food",1)))
new_safety = st.slider("Safety", 1, 10, int(row.get("safety",1)))
new_value = st.slider("Value", 1, 10, int(row.get("value",1)))
new_crowd = st.slider("Crowd", 1, 10, int(row.get("crowd",1)))

new_notes = st.text_area("Notes", row.get("notes",""))

if st.button("💾 Update"):

rating = round((new_clean+new_food_rating+new_safety+new_value+new_crowd)/5,1)    

sheet.update(f"A{i+2}:V{i+2}", [[    
    row["pg_id"], new_name, new_location,    
    new_owner, new_number,    
    row.get("sharing_json",""),    
    new_food, new_laundry,    
    new_room, new_gender,    
    new_metro, new_bus, new_rail,    
    new_near,    
    new_clean, new_food_rating, new_safety,    
    new_value, new_crowd,    
    rating, new_notes,    
    row.get("timestamp","")    
]])    

st.success("Updated")    
del st.session_state.edit_index    
st.rerun()