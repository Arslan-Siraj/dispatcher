import streamlit as st
import pandas as pd
import os

st.title("🔢 Scan History by Barcode ID")
from app_helper import show_app_dev_info
show_app_dev_info()

DATA_DIR = "data"

VALID_PREFIX = "SPXID06"

# ---- Ensure prefix exists BEFORE widget creation ----
if "barcode_input" not in st.session_state:
    st.session_state.barcode_input = VALID_PREFIX
elif not st.session_state.barcode_input.startswith(VALID_PREFIX):
    st.session_state.barcode_input = VALID_PREFIX

# ---- Text input (prefix already visible) ----
barcode_input = st.text_input(
    "Enter Barcode ID",
    key="barcode_input",
    placeholder="2253688982"
)

barcode = barcode_input.strip()

# ---- Stop until user types suffix ----
if barcode == VALID_PREFIX:
    st.info("Please enter the barcode number after PXID06.")
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


IMAGE_DIR = "images"

st.subheader("🖼️ Proof")

images_found = []

if os.path.exists(IMAGE_DIR):
    for root, dirs, files in os.walk(IMAGE_DIR):
        for file in files:
            if (
                file.lower().endswith((".png", ".jpg", ".jpeg"))
                and file.startswith(f"{barcode}_")
            ):
                images_found.append(os.path.join(root, file))

# Sort images (optional, alphabetical = time-ordered)
images_found.sort()

if images_found:
    for img_path in images_found:
        filename = os.path.basename(img_path)

        st.image(
            img_path,
            caption=filename
        )

        with open(img_path, "rb") as f:
            st.download_button(
                label=f"⬇️ Download {filename}",
                data=f,
                file_name=filename,
                mime="image/png" if filename.lower().endswith(".png") else "image/jpeg"
            )

        st.divider()

else:
    st.info("No image available for this Barcode ID.")

