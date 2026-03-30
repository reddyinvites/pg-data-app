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

    name = st.text_input("PG Name")
    location = st.text_input("Location")

    owner_name = st.text_input("Owner Name")
    owner_number = st.text_input("Owner Number")

    # -------- SHARING --------
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

        share_type = col1.selectbox("Type", ["1 Sharing","2 Sharing","3 Sharing","4 Sharing"],
                                   index=["1 Sharing","2 Sharing","3 Sharing","4 Sharing"].index(s["type"]),
                                   key=f"type_{i}")

        price = col2.number_input("Price", value=s["price"], key=f"price_{i}")
        deposit = col3.number_input("Deposit", value=s["deposit"], key=f"dep_{i}")

        col4, col5 = st.columns(2)
        total_beds = col4.number_input("Total Beds", value=s["total_beds"], key=f"tb_{i}")
        available_beds = col5.number_input("Available Beds", value=s["available_beds"], key=f"ab_{i}")

        updated.append({
            "type": share_type,
            "price": price,
            "deposit": deposit,
            "total_beds": total_beds,
            "available_beds": available_beds
        })

    st.session_state.sharing_data = updated

    # -------- FACILITIES --------
    food_type = st.selectbox("Food Type", ["Veg","Non-Veg","Mixed"])
    laundry = st.selectbox("Laundry", ["Yes","No"])

    metro_dist = st.number_input("Metro Distance (meters)", 0)
    st.caption(f"{metro_dist/1000:.2f} km")

    bus_dist = st.number_input("Bus Distance (meters)", 0)
    rail_dist = st.number_input("Railway Distance (meters)", 0)

    nearby_places = st.text_input("Nearby Places")

    # -------- RATINGS --------
    clean = st.slider("Cleanliness", 1, 10)
    food = st.slider("Food", 1, 10)
    safety = st.slider("Safety", 1, 10)
    value = st.slider("Value", 1, 10)
    crowd = st.slider("Crowd", 1, 10)

    notes = st.text_area("Notes")

    save = st.form_submit_button("💾 Save")

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
        metro_dist,
        bus_dist,
        rail_dist,
        nearby_places,
        clean,
        food,
        safety,
        value,
        crowd,
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

    if not df.empty:
        df.columns = df.columns.str.lower()
    else:
        st.warning("No data")

except Exception as e:
    st.error("Sheet error")
    st.write(e)
    df = pd.DataFrame()

# -------- DISPLAY --------
if not df.empty:

    for i in df.index:

        with st.expander(f"🏠 {df.loc[i,'name']} ({df.loc[i,'location']})"):

            row = df.loc[i]

            st.write(f"⭐ Rating: {row.get('rating','')}")
            st.write(f"🍽 Food: {row.get('food','')}/10")
            st.write(f"🧼 Clean: {row.get('cleanliness','')}/10")
            st.write(f"🛡 Safety: {row.get('safety','')}/10")
            st.write(f"💰 Value: {row.get('value','')}/10")
            st.write(f"👥 Crowd: {row.get('crowd','')}/10")

            st.write(f"📍 Metro: {row.get('metro_dist','')} m")
            st.write(f"🚌 Bus: {row.get('bus_dist','')} m")
            st.write(f"🚆 Rail: {row.get('rail_dist','')} m")

            col1, col2 = st.columns(2)

            if col1.button("🗑 Delete", key=f"del_{i}_{row.get('name')}"):
                sheet.delete_rows(i+2)
                st.rerun()

            if col2.button("✏️ Edit", key=f"edit_{i}_{row.get('name')}"):
                st.session_state.edit_index = i