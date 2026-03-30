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
                st.error("Invalid")

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

# -------- FORM --------
with st.form("pg_form"):

    st.subheader("🏠 Basic Info")
    name = st.text_input("PG Name")
    location = st.text_input("Location")

    st.subheader("👤 Owner")
    owner_name = st.text_input("Owner Name")
    owner_number = st.text_input("Owner Number")

    # -------- SHARING --------
    st.subheader("💰 Sharing Details")

    if "sharing_data" not in st.session_state:
        st.session_state.sharing_data = [{
            "type": "2 Sharing",
            "price": 6000,
            "deposit": 2000,
            "total_beds": 10,
            "available_beds": 3
        }]

    if st.form_submit_button("➕ Add Sharing"):
        st.session_state.sharing_data.append({
            "type": "3 Sharing",
            "price": 5000,
            "deposit": 2000,
            "total_beds": 10,
            "available_beds": 2
        })
        st.rerun()

    updated = []

    for i, s in enumerate(st.session_state.sharing_data):

        st.markdown(f"### 🛏 Sharing {i+1}")

        col1, col2, col3 = st.columns(3)

        with col1:
            share_type = st.selectbox("Type",
                ["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"],
                index=["1 Sharing","2 Sharing","3 Sharing","4 Sharing"].index(s["type"]),
                key=f"type_{i}"
            )

        with col2:
            price = st.number_input("Price", value=s["price"], key=f"price_{i}")

        with col3:
            deposit = st.number_input("Deposit", value=s["deposit"], key=f"dep_{i}")

        col4, col5, col6 = st.columns(3)

        with col4:
            total_beds = st.number_input("Total Beds", value=s["total_beds"], key=f"tb_{i}")

        with col5:
            available_beds = st.number_input("Available Beds", value=s["available_beds"], key=f"ab_{i}")

        with col6:
            if st.form_submit_button("❌ Remove", key=f"del_{i}"):
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

    # -------- FACILITIES --------
    st.subheader("📍 Facilities")

    food_type = st.selectbox("Food Type", ["Veg", "Non-Veg", "Mixed"])
    laundry = st.selectbox("Laundry", ["Yes", "No"])

    near_metro = st.checkbox("Near Metro")
    near_bus = st.checkbox("Near Bus Stop")
    near_rail = st.checkbox("Near Railway Station")

    nearby_places = st.text_input("Nearby Places")

    # -------- RATINGS --------
    st.subheader("⭐ Ratings")
    clean = st.slider("Cleanliness", 1, 10)
    food = st.slider("Food", 1, 10)
    safety = st.slider("Safety", 1, 10)
    value = st.slider("Value", 1, 10)
    crowd = st.slider("Crowd", 1, 10)

    notes = st.text_area("Notes")

    preview = st.form_submit_button("👁 Preview")
    save = st.form_submit_button("💾 Save")

# -------- PREVIEW --------
if preview:
    st.json({
        "name": name,
        "sharing": st.session_state.sharing_data,
        "food": food_type,
        "location_tags": {
            "metro": near_metro,
            "bus": near_bus,
            "rail": near_rail
        }
    })

# -------- SAVE --------
if save:
    rating = round((clean + food + safety + value + crowd)/5,1)

    row = [
        name,
        location,
        owner_name,
        owner_number,
        json.dumps(st.session_state.sharing_data),
        food_type,
        laundry,
        near_metro,
        near_bus,
        near_rail,
        nearby_places,
        rating,
        notes,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ]

    sheet.append_row(row)
    st.success("Saved!")
    st.rerun()

# -------- LOAD --------
st.subheader("📊 PG List")

try:
    data = sheet.get_all_records()
    df = pd.DataFrame(data)
    df.columns = df.columns.str.lower()
except:
    df = pd.DataFrame()

# -------- DISPLAY + CRUD --------
if not df.empty:

    for i in df.index:

        with st.expander(f"🏠 {df.loc[i,'name']} ({df.loc[i,'location']})"):

            st.write(df.loc[i])

            col1, col2 = st.columns(2)

            with col1:
                if st.button("🗑 Delete", key=f"del_{i}"):
                    sheet.delete_rows(i+2)
                    st.rerun()

            with col2:
                if st.button("✏️ Edit", key=f"edit_{i}"):
                    st.session_state.edit_index = i

# -------- EDIT --------
if "edit_index" in st.session_state:

    st.subheader("✏️ Edit PG")

    i = st.session_state.edit_index
    row = df.loc[i]

    new_name = st.text_input("Name", row["name"])
    new_location = st.text_input("Location", row["location"])
    new_food = st.selectbox("Food Type", ["Veg","Non-Veg","Mixed"])
    new_laundry = st.selectbox("Laundry", ["Yes","No"])

    if st.button("💾 Update"):

        updated_row = [
            new_name,
            new_location,
            row.get("owner_name",""),
            row.get("owner_number",""),
            row.get("sharing_json",""),
            new_food,
            new_laundry,
            row.get("near_metro",""),
            row.get("near_bus",""),
            row.get("near_rail",""),
            row.get("nearby_places",""),
            row.get("rating",""),
            row.get("notes",""),
            row.get("timestamp","")
        ]

        sheet.update(f"A{i+2}:N{i+2}", [updated_row])

        st.success("Updated!")
        del st.session_state.edit_index
        st.rerun()