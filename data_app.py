import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

st.set_page_config(page_title="PG Data Collector", layout="centered")

st.title("🏠 PG Data Collector (PRO)")

# -------- GOOGLE SHEETS CONNECT --------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    st.secrets["gcp"], scope
)
client = gspread.authorize(creds)

sheet = client.open_by_key("1y60dTYBKgkOi7J37jtGK4BkkmUoZF8yD4P5J3xA5q6Q").sheet1


# -------- DEFINE COLUMN ORDER (MASTER FIX) --------
columns = [
    "name","price","location","food","room",
    "cleanliness","food_quality","rating",
    "crowd","contact","notes","created_at"
]


# -------- LOAD DATA --------
data = sheet.get_all_records()
df = pd.DataFrame(data) if data else pd.DataFrame(columns=columns)


# -------- FORM --------
with st.form("pg_form"):

    name = st.text_input("PG Name")

    location = st.selectbox(
        "Location",
        ["ameerpet", "madhapur", "hitech city", "sr nagar"]
    )

    price = st.number_input("Price (₹)", 3000, 15000, step=500)

    food = st.selectbox("Food Available", ["Yes", "No"])
    room = st.selectbox("Room Type", ["AC", "Non-AC"])

    cleanliness = st.slider("Cleanliness", 1, 10)
    food_quality = st.slider("Food Quality", 1, 10)

    crowd = st.selectbox("Crowd", ["Employees", "Students", "Mixed"])

    contact = st.text_input("Contact Number")
    notes = st.text_area("Extra Notes")

    preview = st.form_submit_button("👁 Preview")
    submit = st.form_submit_button("💾 Save")


# -------- CLEAN NOTES --------
clean_notes = " | ".join(
    [n.strip() for n in notes.split("\n") if n.strip()]
)

# -------- AUTO RATING --------
rating = round((cleanliness + food_quality) / 2, 1)

# -------- PHONE VALIDATION --------
phone_valid = re.fullmatch(r"\d{10}", contact)

# -------- DUPLICATE CHECK --------
duplicate = False
if not df.empty and "contact" in df.columns:
    duplicate = contact in df["contact"].astype(str).values


# -------- PREVIEW --------
if preview:
    st.subheader("🔍 Preview")
    st.write({
        "Name": name,
        "Location": location,
        "Price": price,
        "Rating ⭐": rating,
        "Contact": contact,
        "Notes": clean_notes
    })


# -------- SAVE --------
if submit:

    if name.strip() == "":
        st.error("❌ Enter PG Name")

    elif not phone_valid:
        st.error("❌ Enter valid 10-digit phone number")

    elif duplicate:
        st.warning("⚠️ This contact already exists")

    else:

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # ✅ DICT → PERFECT COLUMN MATCH
        row_dict = {
            "name": name.strip().title(),
            "price": price,
            "location": location,
            "food": food,
            "room": room,
            "cleanliness": cleanliness,
            "food_quality": food_quality,
            "rating": rating,
            "crowd": crowd,
            "contact": contact,
            "notes": clean_notes,
            "created_at": created_at
        }

        # ✅ ORDER FIX (NO MISMATCH EVER)
        row = [row_dict[col] for col in columns]

        sheet.append_row(row, value_input_option="USER_ENTERED")

        st.success("✅ Saved Successfully!")

        # 🔥 INSTANT REFRESH
        st.rerun()


# -------- DISPLAY --------
st.subheader("📊 PG Database")

data = sheet.get_all_records()

if data:
    df = pd.DataFrame(data)
    df = df.reindex(columns=columns)  # ✅ FORCE ORDER
    st.dataframe(df, use_container_width=True)
else:
    st.info("No data yet")