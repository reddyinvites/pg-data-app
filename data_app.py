import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="PG Data Collector", layout="centered")

st.title("📝 PG Data Collection")

file_name = "pg_data.csv"

# ---------------- CREATE FILE ----------------
if not os.path.exists(file_name):
    df = pd.DataFrame(columns=[
        "name","price","location","food","room",
        "cleanliness","food_quality","crowd","contact","notes"
    ])
    df.to_csv(file_name, index=False)

# ---------------- FORM ----------------
with st.form("pg_form"):

    st.subheader("Enter PG Details")

    name = st.text_input("PG Name")

    location = st.selectbox(
        "Location",
        ["ameerpet", "madhapur", "hitech city", "sr nagar"]
    )

    price = st.number_input(
        "Price (₹)",
        min_value=3000,
        max_value=15000,
        step=500
    )

    food = st.selectbox("Food Available", ["Yes", "No"])

    room = st.selectbox("Room Type", ["AC", "Non-AC"])

    cleanliness = st.slider("Cleanliness (1-10)", 1, 10)

    food_quality = st.slider("Food Quality (1-10)", 1, 10)

    crowd = st.selectbox(
        "Crowd Type",
        ["Employees", "Students", "Mixed"]
    )

    contact = st.text_input("Contact Number")

    notes = st.text_area("Extra Notes")

    submit = st.form_submit_button("💾 Save PG")

# ---------------- SAVE ----------------
if submit:

    if name == "":
        st.error("⚠️ Please enter PG name")
    else:
        new_data = {
            "name": name,
            "price": price,
            "location": location,
            "food": food,
            "room": room,
            "cleanliness": cleanliness,
            "food_quality": food_quality,
            "crowd": crowd,
            "contact": contact,
            "notes": notes
        }

        df = pd.read_csv(file_name)
        df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
        df.to_csv(file_name, index=False)

        st.success("✅ PG Saved Successfully!")

# ---------------- SHOW DATA ----------------
st.subheader("📊 Saved PG Data")

df = pd.read_csv(file_name)
st.dataframe(df)
