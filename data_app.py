import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="PG Data Collector", layout="wide")

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

    cleanliness = st.slider("Cleanliness", 1, 10)
    food_quality = st.slider("Food Quality", 1, 10)

    crowd = st.selectbox("Crowd", ["Employees", "Students", "Mixed"])

    contact = st.text_input("Contact Number")
    notes = st.text_area("Extra Notes")

    preview_btn = st.form_submit_button("👁 Preview")
    save_btn = st.form_submit_button("💾 Save")


# -------- PREVIEW --------
if preview_btn:

    clean_notes = " | ".join(
        [n.strip() for n in notes.split("\n") if n.strip()]
    )

    rating = round((cleanliness + food_quality) / 2, 1)

    st.session_state.preview = {
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
if "preview" in st.session_state:
    st.subheader("🔍 Preview")
    st.json(st.session_state.preview)


# -------- SAVE --------
if save_btn:

    if "preview" not in st.session_state:
        st.error("⚠️ Click Preview first")
    else:

        d = st.session_state.preview

        row = [
            d["name"],
            d["price"],
            d["location"],
            d["food"],
            d["room"],
            d["cleanliness"],
            d["food_quality"],
            d["rating"],
            d["crowd"],
            d["contact"],
            d["notes"],
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]

        sheet.append_row(row, value_input_option="USER_ENTERED")

        st.success("✅ Saved!")

        del st.session_state.preview

        st.rerun()


# -------- LOAD DATA --------
st.subheader("📊 PG Database")

data = sheet.get_all_records()
df = pd.DataFrame(data)

# ✅ VERY IMPORTANT FIX (NO KEYERROR EVER)
df.columns = df.columns.str.strip().str.lower()


# -------- SEARCH + FILTER --------
st.subheader("🔍 Search & Filter")

search = st.text_input("Search PG")

location_filter = st.selectbox(
    "Filter Location",
    ["All", "ameerpet", "madhapur", "hitech city", "sr nagar"]
)

if not df.empty:

    if search:
        df = df[df.apply(lambda r: search.lower() in str(r).lower(), axis=1)]

    if location_filter != "All":
        df = df[df["location"] == location_filter]

    st.dataframe(df, use_container_width=True)


# -------- EDIT / DELETE --------
st.subheader("✏️ Edit / Delete")

def safe_get(row, key):
    return row[key] if key in row else ""

if not df.empty:

    index = st.selectbox("Select Row", df.index)

    row_data = df.loc[index]

    st.write("Selected:", safe_get(row_data, "name"))

    # -------- DELETE --------
    if st.button("🗑 Delete"):
        sheet.delete_rows(index + 2)
        st.success("Deleted!")
        st.rerun()

    # -------- EDIT --------
    new_name = st.text_input("Edit Name", safe_get(row_data, "name"))

    if st.button("💾 Update"):

        updated_row = [
            new_name,
            safe_get(row_data, "price"),
            safe_get(row_data, "location"),
            safe_get(row_data, "food"),
            safe_get(row_data, "room"),
            safe_get(row_data, "cleanliness"),
            safe_get(row_data, "food_quality"),
            safe_get(row_data, "rating"),
            safe_get(row_data, "crowd"),
            safe_get(row_data, "contact"),
            safe_get(row_data, "notes"),
            safe_get(row_data, "created_at")
        ]

        sheet.update(f"A{index+2}:L{index+2}", [updated_row])

        st.success("Updated!")
        st.rerun()