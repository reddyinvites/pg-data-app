import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import urllib.parse

st.set_page_config(page_title="PG Data Collector Pro", layout="wide")

# -------- LOGIN --------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 Admin Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u == st.secrets["auth"]["username"] and p == st.secrets["auth"]["password"]:
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid credentials")

def logout():
    st.session_state.logged_in = False
    st.rerun()

if not st.session_state.logged_in:
    login()
    st.stop()

st.sidebar.success("Admin")
st.sidebar.button("Logout", on_click=logout)

st.title("🚀 PG Data Collector PRO")

# -------- GOOGLE SHEETS --------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
client = gspread.authorize(creds)
sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").sheet1

# -------- FORM --------
with st.form("pg_form"):

    st.subheader("🏠 Basic Info")
    name = st.text_input("PG Name")
    location = st.selectbox("Location", ["ameerpet", "madhapur", "hitech city", "sr nagar"])
    price = st.number_input("Price", 3000, 20000)

    st.subheader("🛏 Room Details")
    sharing = st.selectbox("Sharing", ["2 Sharing", "3 Sharing", "4 Sharing"])
    total_beds = st.number_input("Total Beds", 1, 200)
    available_beds = st.number_input("Available Beds", 0, 200)
    deposit = st.number_input("Deposit", 0, 50000)

    st.subheader("🍽 Food Details")
    food = st.selectbox("Food Available", ["Yes", "No"])
    food_type = st.selectbox("Veg/Non-Veg", ["Veg", "Non-Veg", "Both"])
    food_timing = st.text_input("Food Timings")

    st.subheader("🧼 Hygiene")
    cleaning = st.selectbox("Cleaning", ["Daily", "Alternate", "Weekly"])
    laundry = st.selectbox("Laundry", ["Yes", "No"])
    washroom = st.selectbox("Washroom", ["Attached", "Common"])

    st.subheader("📍 Location Intelligence")
    metro = st.number_input("Metro Distance (meters)", 0, 5000)
    nearby = st.text_input("Nearby (hospital, gym, store)")

    st.subheader("⭐ Ratings")
    clean_rating = st.slider("Cleanliness", 1, 10)
    food_rating = st.slider("Food", 1, 10)
    safety_rating = st.slider("Safety", 1, 10)
    value_rating = st.slider("Value", 1, 10)
    crowd_rating = st.slider("Crowd Quality", 1, 10)

    st.subheader("👥 Crowd")
    crowd = st.selectbox("Crowd Type", ["Employees", "Students", "Mixed"])

    st.subheader("📞 Contact")
    contact = st.text_input("Phone")
    owner = st.text_input("Owner Name")
    notes = st.text_area("Extra Notes")

    preview_btn = st.form_submit_button("Preview")
    save_btn = st.form_submit_button("Save")

# -------- PREVIEW --------
if preview_btn:
    if not name or not contact:
        st.error("Name & Contact required")
    else:
        rating = round((clean_rating + food_rating + safety_rating + value_rating + crowd_rating) / 5, 1)

        st.session_state.preview = {
            "name": name,
            "price": price,
            "location": location,
            "sharing": sharing,
            "available": available_beds,
            "rating": rating,
            "contact": contact
        }

# -------- SHOW PREVIEW --------
if "preview" in st.session_state:
    st.json(st.session_state.preview)

# -------- SAVE --------
if save_btn:
    if "preview" not in st.session_state:
        st.error("Preview first")
    else:
        r = st.session_state.preview

        row = [
            name, price, location, sharing,
            total_beds, available_beds, deposit,
            food, food_type, food_timing,
            cleaning, laundry, washroom,
            metro, nearby,
            clean_rating, food_rating, safety_rating, value_rating, crowd_rating,
            crowd, contact, owner, notes,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        sheet.append_row(row)
        st.success("Saved!")
        del st.session_state.preview
        st.rerun()

# -------- LOAD --------
st.subheader("📊 Database")

data = sheet.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
    df.columns = df.columns.str.lower()

# -------- FILTER --------
search = st.text_input("Search")
loc = st.selectbox("Filter", ["All", "ameerpet", "madhapur", "hitech city", "sr nagar"])

if not df.empty:

    if search:
        df = df[df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

    if loc != "All":
        df = df[df["location"].str.lower() == loc.lower()]

    st.dataframe(df)

# -------- WHATSAPP BUTTON --------
st.subheader("📲 Contact PG")

if not df.empty:
    i = st.selectbox("Select PG", df.index)
    row = df.loc[i]

    msg = f"Hi, I am interested in {row['name']} PG"
    url = f"https://wa.me/{row['contact']}?text={urllib.parse.quote(msg)}"

    st.markdown(f"[👉 Chat on WhatsApp]({url})")

# -------- DELETE --------
if not df.empty:
    if st.button("Delete Selected"):
        sheet.delete_rows(i+2)
        st.success("Deleted")
        st.rerun()