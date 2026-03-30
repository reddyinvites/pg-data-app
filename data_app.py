import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import json

st.set_page_config(page_title="PG Manager", layout="wide")

# -------- LOGIN --------
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

# -------- GOOGLE SHEETS --------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").sheet1

st.title("🏠 PG Manager")

# -------- LOAD DATA --------
data = sheet.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
    df.columns = df.columns.str.lower().str.strip()

# -------- PG ID GENERATOR --------
def generate_pg_id(df):
    if df.empty or "pg_id" not in df.columns:
        return "PG001"
    
    ids = df["pg_id"].dropna().astype(str)
    nums = []

    for i in ids:
        if i.startswith("PG"):
            try:
                nums.append(int(i.replace("PG","")))
            except:
                pass

    next_id = max(nums)+1 if nums else 1
    return f"PG{str(next_id).zfill(3)}"

# -------- SHARING --------
if "sharing_data" not in st.session_state:
    st.session_state.sharing_data = [{
        "type": "2 Sharing",
        "price": 6000,
        "deposit": 2000,
        "total_beds": 2,
        "available_beds": 1
    }]

st.subheader("🛏 Sharing Details")

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

    total_beds = col4.number_input(
        "Total Beds", 1, max_beds,
        value=min(s["total_beds"], max_beds),
        key=f"tb_{i}"
    )

    available_beds = col5.number_input(
        "Available Beds", 0, total_beds,
        value=min(s["available_beds"], total_beds),
        key=f"ab_{i}"
    )

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

# -------- FORM --------
with st.form("pg_form"):

    name = st.text_input("PG Name")
    location = st.text_input("Location")
    owner_name = st.text_input("Owner Name")
    owner_number = st.text_input("Owner Number")

    food_type = st.selectbox("Food Type", ["Veg","Non-Veg","Mixed"])
    laundry = st.selectbox("Laundry", ["Yes","No"])

    metro_dist = st.number_input("Metro Distance (m)", 0)
    bus_dist = st.number_input("Bus Distance (m)", 0)
    rail_dist = st.number_input("Rail Distance (m)", 0)

    nearby_places = st.text_input("Nearby Places")

    clean = st.slider("Cleanliness", 1, 10)
    food_rating = st.slider("Food", 1, 10)
    safety = st.slider("Safety", 1, 10)
    value = st.slider("Value", 1, 10)
    crowd = st.slider("Crowd", 1, 10)

    notes = st.text_area("Notes")

    preview = st.form_submit_button("👁 Preview")
    save = st.form_submit_button("💾 Save")

# -------- PREVIEW --------
if preview:
    rating = round((clean+food_rating+safety+value+crowd)/5,1)

    st.subheader("Preview")
    st.json({
        "name": name,
        "location": location,
        "rating": rating,
        "sharing": st.session_state.sharing_data
    })

    st.session_state.preview = True

# -------- SAVE --------
if save:

    if "preview" not in st.session_state:
        st.error("⚠️ Click Preview first")
        st.stop()

    pg_id = generate_pg_id(df)

    rating = round((clean+food_rating+safety+value+crowd)/5,1)

    sheet.append_row([
        pg_id,
        name,
        location,
        owner_name,
        owner_number,
        json.dumps(st.session_state.sharing_data),
        food_type,
        laundry,
        metro_dist,
        bus_dist,
        rail_dist,
        nearby_places,
        clean,
        food_rating,
        safety,
        value,
        crowd,
        rating,
        notes,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ])

    st.success(f"✅ Saved with ID {pg_id}")
    del st.session_state.preview
    st.rerun()

# -------- TABLE --------
st.subheader("📊 PG Table")

if df.empty:
    st.warning("No data found")
else:
    required = ["pg_id","name","location","food_type","laundry","rating"]
    available = [c for c in required if c in df.columns]

    if not available:
        st.error("No matching columns")
        st.write("Available:", df.columns.tolist())
    else:
        st.dataframe(df[available], use_container_width=True)

# -------- ACTIONS --------
st.subheader("⚙️ Actions")

if not df.empty:

    selected = st.selectbox("Select PG", df.index)

    row = df.loc[selected]

    col1, col2 = st.columns(2)

    if col1.button("🗑 Delete"):
        sheet.delete_rows(selected+2)
        st.rerun()

    if col2.button("✏️ Edit"):
        st.session_state.edit_index = selected

# -------- EDIT --------
if "edit_index" in st.session_state:

    i = st.session_state.edit_index
    row = df.loc[i]

    st.subheader("✏️ Edit PG")

    new_name = st.text_input("PG Name", value=row.get("name",""))
    new_location = st.text_input("Location", value=row.get("location",""))

    if st.button("💾 Update"):

        sheet.update(f"A{i+2}:T{i+2}", [[
            row.get("pg_id",""),
            new_name,
            new_location,
            row.get("owner_name",""),
            row.get("owner_number",""),
            row.get("sharing_json",""),
            row.get("food_type",""),
            row.get("laundry",""),
            row.get("metro_dist",0),
            row.get("bus_dist",0),
            row.get("rail_dist",0),
            row.get("nearby_places",""),
            row.get("cleanliness",0),
            row.get("food_rating",0),
            row.get("safety",0),
            row.get("value",0),
            row.get("crowd",0),
            row.get("rating",0),
            row.get("notes",""),
            row.get("timestamp","")
        ]])

        st.success("Updated")
        del st.session_state.edit_index
        st.rerun()