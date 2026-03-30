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

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp"], scope
)
client = gspread.authorize(creds)
sheet = client.open_by_key(
    "1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q"
).sheet1

st.title("🏠 PG Manager")

# -------- SHARING (OUTSIDE FORM) --------
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

    st.markdown(f"### Sharing {i+1}")

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
        "Total Beds",
        min_value=1,
        max_value=max_beds,
        value=min(s["total_beds"], max_beds),
        key=f"tb_{i}"
    )

    available_beds = col5.number_input(
        "Available Beds",
        min_value=0,
        max_value=total_beds,
        value=min(s["available_beds"], total_beds),
        key=f"ab_{i}"
    )

    if col6.button("❌ Remove", key=f"del_{i}"):
        if len(st.session_state.sharing_data) > 1:
            st.session_state.sharing_data.pop(i)
            st.rerun()
        else:
            st.warning("At least one sharing required")

    updated.append({
        "type": share_type,
        "price": price,
        "deposit": deposit,
        "total_beds": total_beds,
        "available_beds": available_beds
    })

st.session_state.sharing_data = updated

# ➕ Add Sharing
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

    st.subheader("Basic Info")

    name = st.text_input("PG Name")
    location = st.text_input("Location")

    owner_name = st.text_input("Owner Name")
    owner_number = st.text_input("Owner Number")

    food_type = st.selectbox("Food Type", ["Veg","Non-Veg","Mixed"])
    laundry = st.selectbox("Laundry", ["Yes","No"])

    st.subheader("Distance")

    metro_dist = st.number_input("Metro Distance (meters)", 0)
    st.caption(f"{metro_dist/1000:.2f} km")

    bus_dist = st.number_input("Bus Distance (meters)", 0)
    rail_dist = st.number_input("Railway Distance (meters)", 0)

    nearby_places = st.text_input("Nearby Places")

    st.subheader("Ratings")

    clean = st.slider("Cleanliness", 1, 10)
    food_rating = st.slider("Food", 1, 10)
    safety = st.slider("Safety", 1, 10)
    value = st.slider("Value", 1, 10)
    crowd = st.slider("Crowd", 1, 10)

    notes = st.text_area("Notes")

    preview_btn = st.form_submit_button("👁 Preview")
    save_btn = st.form_submit_button("💾 Save")

# -------- PREVIEW --------
if preview_btn:

    rating = round((clean + food_rating + safety + value + crowd)/5,1)

    preview_data = {
        "name": name,
        "location": location,
        "sharing": st.session_state.sharing_data,
        "rating": rating,
        "notes": notes
    }

    st.subheader("🔍 Preview")
    st.json(preview_data)

    st.session_state.preview = preview_data

# -------- SAVE --------
if save_btn:

    if "preview" not in st.session_state:
        st.error("⚠️ Click Preview first")
        st.stop()

    rating = round((clean + food_rating + safety + value + crowd)/5,1)

    row = [
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
    ]

    sheet.append_row(row)
    st.success("Saved!")
    del st.session_state.preview
    st.rerun()

# -------- LOAD --------
st.subheader("📊 PG Table")

try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)

    if df.empty:
        st.warning("No data found")
        st.stop()

    df.columns = df.columns.str.lower().str.strip()

except Exception as e:
    st.error("Sheet error")
    st.write(e)
    st.stop()

# -------- TABLE --------
show_df = df[["name","location","food_type","laundry","metro_dist","rating"]]
st.dataframe(show_df, use_container_width=True)

# -------- ACTIONS --------
st.subheader("⚙️ Actions")

selected = st.selectbox("Select PG", df.index)

if selected not in df.index:
    st.stop()

row = df.loc[selected]

col1, col2 = st.columns(2)

if col1.button("🗑 Delete Selected"):
    sheet.delete_rows(selected + 2)
    st.success("Deleted")
    st.rerun()

if col2.button("✏️ Edit Selected"):
    st.session_state.edit_index = selected