import streamlit as st
import pandas as pd
import os
import datetime

from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, ColumnsAutoSizeMode

st.title("📅 Scan History by Date")

DATA_DIR = "data"
IMAGE_DIR = "images"

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
df = df.sort_values("Timestamp", ascending=False)

st.subheader(f"Scans on {selected_date}")
st.markdown(f"**Total scans:** {len(df)}")

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_selection(selection_mode="single", use_checkbox=True)
gb.configure_side_bar()
gb.configure_pagination(
    enabled=True,
    paginationAutoPageSize=False,
    paginationPageSize=10
)

gridOptions = gb.build()

data = AgGrid(
    df,
    gridOptions=gridOptions,
    enable_enterprise_modules=True,
    update_mode=GridUpdateMode.SELECTION_CHANGED,
    columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS,
    height=350,   # ← IMPORTANT
    fit_columns_on_grid_load=True
)

selected_row = data["selected_rows"]

if selected_row:
    barcode = str(selected_row[0]["Barcode_ID"])
    timestamp = selected_row[0]["Timestamp"]
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

    images_found.sort()

    if images_found:
        for img_path in images_found:
            filename = os.path.basename(img_path)

            st.image(img_path, caption=filename)

            with open(img_path, "rb") as f:
                st.download_button(
                    label=f"⬇️ Download {filename}",
                    data=f,
                    file_name=filename,
                    mime="image/png" if filename.lower().endswith(".png") else "image/jpeg",
                    key=filename  # IMPORTANT: unique key
                )

            st.divider()
    else:
        st.info("No image available for this Barcode ID.")
