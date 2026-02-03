import streamlit as st
import pandas as pd
import os

st.title("🔢 Scan History by Barcode ID")

DATA_DIR = "data"

barcode = st.text_input(
    "Enter Barcode ID",
    placeholder="SPXID062253688982"
)

if not barcode:
    st.info("Enter a Barcode ID to search.")
    st.stop()

records = []

for file in os.listdir(DATA_DIR):
    if file.endswith(".csv"):
        date = file.replace(".csv", "")
        df = pd.read_csv(
            os.path.join(DATA_DIR, file),
            names=["Barcode_ID", "Timestamp"]
        )
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df[df["Barcode_ID"].str.contains(barcode, case=False, na=False)]
        if not df.empty:
            df["Date"] = date
            records.append(df)

if not records:
    st.warning("No scans found for this Barcode ID.")
    st.stop()

result = pd.concat(records)
result = result.sort_values("Timestamp", ascending=False)

st.subheader(f"Results for {barcode}")
st.dataframe(result, use_container_width=True)
