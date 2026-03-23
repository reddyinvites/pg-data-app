import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="PG Admin Panel")

st.title("📝 PG Data Admin Panel")

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


# -------- LOAD EXISTING DATA --------
data = sheet.get_all_records()
df = pd.DataFrame(data) if data else pd.DataFrame()


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

    # 🔴 VALIDATION
    if not name or not contact:
        st.error("⚠️ Name & Contact required!")
    elif len(contact) != 10 or not contact.isdigit():
        st.error("⚠️ Enter valid 10-digit phone number")
    else:

        name = name.title()
        location = location.title()

        # 🔥 DUPLICATE CHECK
        existing_names = df["name"].str.lower().tolist() if not df.empty else []
        if name.lower() in existing_names:
            st.error("⚠️ PG already exists!")
        else:

            # ⭐ AUTO RATING
            rating = round((cleanliness + food_quality) / 2, 1)

            # 🧹 CLEAN NOTES
            clean_notes = " | ".join(
                [n.strip() for n in notes.split("\n") if n.strip()]
            )

            # 🕒 TIMESTAMP
            created_at = datetime.now().strftime("%Y-%m-%d %H:%M")

            # 📦 FINAL ROW (ORDER IMPORTANT)
            row = [
                name,
                price,
                location,
                food,
                room,
                cleanliness,
                food_quality,
                rating,
                crowd,
                contact,
                clean_notes,
                created_at
            ]

            # 👀 PREVIEW
            st.write("Preview:", row)

            # 💾 SAVE
            sheet.append_row(row)

            st.success("✅ PG Saved Successfully!")
            st.experimental_rerun()


# ---------------- SHOW DATA ----------------
st.subheader("📊 PG Database")

if not df.empty:

    expected_cols = [
        "name","price","location","food","room",
        "cleanliness","food_quality","rating",
        "crowd","contact","notes","created_at"
    ]

    df = df[expected_cols]

    st.dataframe(df)

else:
    st.info("No data yet")