import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

st.set_page_config(page_title="PG Data Collector", layout="wide")

# -------- LOGIN SYSTEM --------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    st.title("🔐 Admin Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if (
            username == st.secrets["auth"]["username"]
            and password == st.secrets["auth"]["password"]
        ):
            st.session_state.logged_in = True
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

def logout():
    st.session_state.logged_in = False
    st.rerun()

if not st.session_state.logged_in:
    login()
    st.stop()

# -------- SIDEBAR --------
st.sidebar.success("Logged in as Admin")
st.sidebar.button("🚪 Logout", on_click=logout)

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

    if not name.strip():
        st.error("⚠️ PG Name is required")
    elif not contact.strip():
        st.error("⚠️ Contact is required")
    else:
        clean_notes = " | ".join(
            [n.strip() for n in notes.split("\n") if n.strip()]
        )

        rating = round((cleanliness + food_quality) / 2, 1)

        st.session_state.preview = {
            "name": name.strip(),
            "price": price,
            "location": location.lower(),
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

if not df.empty:
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
        df = df[df["location"].str.lower() == location_filter.lower()]

    st.dataframe(df, use_container_width=True)


# -------- EDIT / DELETE --------
st.subheader("✏️ Edit / Delete")

if not df.empty:

    index = st.selectbox("Select Row", df.index)
    row_data = df.loc[index]

    st.write("Selected:", row_data.get("name", ""))

    # DELETE
    if st.button("🗑 Delete"):
        sheet.delete_rows(index + 2)
        st.success("Deleted!")
        st.rerun()

    # -------- FULL EDIT --------
    st.markdown("### ✏️ Edit PG Details")

    new_name = st.text_input("Name", row_data.get("name", ""))
    new_price = st.number_input("Price", value=int(row_data.get("price", 3000)))
    new_location = st.selectbox(
        "Location",
        ["ameerpet", "madhapur", "hitech city", "sr nagar"],
        index=["ameerpet", "madhapur", "hitech city", "sr nagar"].index(
            row_data.get("location", "ameerpet")
        )
    )
    new_food = st.selectbox("Food", ["Yes", "No"],
                           index=["Yes", "No"].index(row_data.get("food", "Yes")))
    new_room = st.selectbox("Room", ["AC", "Non-AC"],
                           index=["AC", "Non-AC"].index(row_data.get("room", "AC")))

    new_contact = st.text_input("Contact", row_data.get("contact", ""))
    new_notes = st.text_area("Notes", row_data.get("notes", ""))

    if st.button("💾 Update"):

        if not new_name.strip():
            st.error("Name required")
        else:

            updated_row = [
                new_name,
                new_price,
                new_location.lower(),
                new_food,
                new_room,
                row_data.get("cleanliness", ""),
                row_data.get("food_quality", ""),
                row_data.get("rating", ""),
                row_data.get("crowd", ""),
                new_contact,
                new_notes,
                row_data.get("timestamp", "")
            ]

            sheet.update(f"A{index+2}:L{index+2}", [updated_row])

            st.success("Updated!")
            st.rerun()