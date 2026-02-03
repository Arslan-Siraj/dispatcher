import streamlit as st
import pandas as pd
import os
import datetime

st.title("📅 Scan History by Date")

DATA_DIR = "data"

selected_date = st.date_input(
    "Select scan date",
    value=datetime.date.today(),
    max_value=datetime.date.today()
)

csv_file = os.path.join(DATA_DIR, f"{selected_date}.csv")

if not os.path.exists(csv_file):
    st.info(f"No scans found for {selected_date}.")
    st.stop()

df = pd.read_csv(csv_file, names=["Barcode_ID", "Timestamp"])
df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
df = df.dropna(subset=["Timestamp"])

st.subheader(f"Scans on {selected_date}")
st.dataframe(df.sort_values("Timestamp", ascending=False), use_container_width=True)
st.markdown(f"**Total scans:** {len(df)}")
