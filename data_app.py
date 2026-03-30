import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import urllib.parse
import json

st.set_page_config(page_title="PG Data App", layout="wide")

# -------- LOGIN --------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.markdown("## 👋 Welcome Admin")
    st.title("🔐 Admin Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        login_btn = st.form_submit_button("Login")

        if login_btn:
            # 🔥 HARD CODED LOGIN (NO SECRETS ISSUE)
            if username == "admin" and password == "1234":
                st.session_state.logged_in = True
                st.success("Login successful ✅")
                st.experimental_rerun()
            else:
                st.error("Invalid credentials ❌")

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

st.title("🏠 PG Data Collector")

# -------- FORM --------
with st.form("form"):

    st.subheader("Basic Info")
    name = st.text_input("PG Name")
    location = st.selectbox("Location", ["ameerpet", "madhapur", "hitech city", "sr nagar"])

    st.subheader("💰 Sharing & Pricing")

    if "sharing_data" not in st.session_state:
        st.session_state.sharing_data = [{"type": "2 Sharing", "price": 6000}]

    if st.form_submit_button("➕ Add Sharing"):
        st.session_state.sharing_data.append({"type": "3 Sharing", "price": 5000})

    updated_data = []

    for i, item in enumerate(st.session_state.sharing_data):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            share_type = st.selectbox(
                f"Sharing {i+1}",
                ["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"],
                index=["1 Sharing", "2 Sharing", "3 Sharing", "4 Sharing"].index(item["type"]),
                key=f"type_{i}"
            )

        with col2:
            price = st.number_input(
                f"Price {i+1}",
                3000, 20000,
                value=item["price"],
                key=f"price_{i}"
            )

        with col3:
            if st.form_submit_button("❌", key=f"del_{i}"):
                st.session_state.sharing_data.pop(i)
                st.experimental_rerun()

        updated_data.append({"type": share_type, "price": price})

    st.session_state.sharing_data = updated_data

    st.subheader("Details")
    beds = st.number_input("Available Beds", 0, 100)
    food = st.selectbox("Food Available", ["Yes", "No"])
    food_rating = st.slider("Food Rating", 1, 10)
    clean_rating = st.slider("Cleanliness", 1, 10)
    crowd = st.selectbox("Crowd", ["Employees", "Students", "Mixed"])
    contact = st.text_input("Phone")
    notes = st.text_area("Notes")

    save = st.form_submit_button("💾 Save")

# -------- SAVE --------
if save:
    if not name or not contact:
        st.error("Name & Contact required")
    else:
        rating = round((food_rating + clean_rating) / 2, 1)
        sharing_json = json.dumps(st.session_state.sharing_data)

        row = [
            name,
            location,
            sharing_json,
            beds,
            food,
            food_rating,
            clean_rating,
            rating,
            crowd,
            contact,
            notes,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        sheet.append_row(row)
        st.success("Saved successfully!")

# -------- LOAD DATA --------
st.subheader("📊 PG List")

data = sheet.get_all_records()
df = pd.DataFrame(data)

if not df.empty:
    df.columns = df.columns.str.lower()

# -------- FILTER --------
search = st.text_input("Search")
loc = st.selectbox("Filter Location", ["All", "ameerpet", "madhapur", "hitech city", "sr nagar"])

if not df.empty:

    if search:
        df = df[df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

    if loc != "All":
        df = df[df["location"].astype(str).str.lower() == loc.lower()]

    st.dataframe(df, use_container_width=True)

# -------- SHARING DISPLAY --------
st.subheader("💰 Sharing Details")

if not df.empty:
    i = st.selectbox("Select PG", df.index)
    row = df.loc[i]

    if "sharing_json" in row and row["sharing_json"]:
        try:
            sharing_data = json.loads(row["sharing_json"])
            for s in sharing_data:
                st.write(f"{s['type']} → ₹{s['price']}")
        except:
            st.warning("⚠️ Sharing data error")
    else:
        if "price" in row:
            st.write(f"💰 Price: ₹{row['price']}")
        else:
            st.info("No pricing data")

# -------- WHATSAPP --------
st.subheader("📲 Contact PG")

if not df.empty:
    msg = f"Hi, I am interested in {row.get('name', 'this PG')}"
    url = f"https://wa.me/{row.get('contact','')}?text={urllib.parse.quote(msg)}"
    st.markdown(f"[👉 Chat on WhatsApp]({url})")

# -------- DELETE --------
if not df.empty:
    if st.button("🗑 Delete Selected"):
        sheet.delete_rows(i + 2)
        st.success("Deleted!")
        st.experimental_rerun()