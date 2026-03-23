import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="PG Data Collector")

st.title("📝 PG Data Collection")

# -------- GOOGLE SHEETS CONNECT --------
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


# -------- FORM --------
with st.form("pg_form"):

    name = st.text_input("PG Name")

    location = st.selectbox(
        "Location",
        ["ameerpet", "madhapur", "hitech city", "sr nagar"]
    )

    price = st.number_input("Price (₹)", 3000, 20000, step=500)

    food = st.selectbox("Food Available", ["Yes", "No"])
    room = st.selectbox("Room Type", ["AC", "Non-AC"])

    cleanliness = st.slider("Cleanliness (1-10)", 1, 10)
    food_quality = st.slider("Food Quality (1-10)", 1, 10)

    crowd = st.selectbox("Crowd Type", ["Employees", "Students", "Mixed"])

    contact = st.text_input("Contact Number")
    notes = st.text_area("Extra Notes")

    preview_btn = st.form_submit_button("👁 Preview")
    save_btn = st.form_submit_button("💾 Save")


# -------- PREVIEW --------
if preview_btn:

    if name.strip() == "":
        st.error("⚠️ Enter PG name")
    else:

        clean_notes = " | ".join(
            [n.strip() for n in notes.split("\n") if n.strip()]
        )

        rating = round((cleanliness + food_quality) / 2, 1)

        st.session_state.preview_data = {
            "name": name.strip(),
            "price": price,
            "location": location,
            "food": food,
            "room": room,
            "cleanliness": cleanliness,
            "food_quality": food_quality,
            "rating": rating,
            "crowd": crowd,
            "contact": contact.strip(),
            "notes": clean_notes
        }

# -------- SHOW PREVIEW --------
if "preview_data" in st.session_state:
    st.subheader("🔍 Preview")
    st.json(st.session_state.preview_data)


# -------- SAVE --------
if save_btn:

    if "preview_data" not in st.session_state:
        st.error("⚠️ Click Preview first")
    else:

        data = st.session_state.preview_data

        # ✅ EXACT ORDER MATCH WITH SHEET
        row = [
            data["name"],
            data["price"],
            data["location"],
            data["food"],
            data["room"],
            data["cleanliness"],
            data["food_quality"],
            data["rating"],
            data["crowd"],
            data["contact"],
            data["notes"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        sheet.append_row(row)

        st.success("✅ Saved to Google Sheets!")

        del st.session_state.preview_data


# -------- DISPLAY DATA --------
st.subheader("📊 PG Database")

data = sheet.get_all_records()

if data:
    st.dataframe(data)
else:
    st.info("No data yet")