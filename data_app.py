import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="PG Data Collector")

st.title("📝 PG Data Collection")

# -------- CONNECT GOOGLE SHEETS --------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds_dict = st.secrets["gcp"]

creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").sheet1


# ---------------- FORM ----------------
with st.form("pg_form"):

    name = st.text_input("PG Name")

    location = st.selectbox(
        "Location",
        ["ameerpet", "madhapur", "hitech city", "sr nagar"]
    )

    price = st.number_input("Price (₹)", 3000, 15000, step=500)

    food = st.selectbox("Food Available", ["Yes", "No"])
    room = st.selectbox("Room Type", ["AC", "Non-AC"])

    cleanliness = st.slider("Cleanliness (1-10)", 1, 10)
    food_quality = st.slider("Food Quality (1-10)", 1, 10)

    crowd = st.selectbox("Crowd Type", ["Employees", "Students", "Mixed"])

    contact = st.text_input("Contact Number")
    notes = st.text_area("Extra Notes")

    submit = st.form_submit_button("💾 Save PG")


# ---------------- SAVE ----------------
if submit:

    if name.strip() == "":
        st.error("⚠️ Please enter PG name")
    else:

        clean_notes = " | ".join(
            [n.strip() for n in notes.split("\n") if n.strip()]
        )

        row = [
            name.strip(), price, location, food, room,
            cleanliness, food_quality, crowd, contact.strip(), clean_notes
        ]

        sheet.append_row(row)

        st.success("✅ PG Saved Successfully!")


# ---------------- SHOW DATA ----------------
st.subheader("📊 Saved PG Data")

data = sheet.get_all_records()

if data:
    st.dataframe(data)
else:
    st.info("No data available yet")
