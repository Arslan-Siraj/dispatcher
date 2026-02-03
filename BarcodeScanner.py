import streamlit as st
import cv2
import numpy as np
from pyzbar import pyzbar
from streamlit_webrtc import webrtc_streamer, VideoTransformerBase
import csv
import datetime
import winsound
import pyttsx3
import os
import time
from glob import glob

# ----------------------------
# Streamlit setup
# ----------------------------
st.set_page_config(page_title="Barcode Scanner", layout="centered")
st.title("📦 Packed Product Barcode Scanner")

DATA_DIR = "data"
IMAGE_DIR = "images"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

# ----------------------------
# Track current date (auto-rerun on day change)
# ----------------------------
today_str = datetime.date.today().isoformat()

if "current_day" not in st.session_state:
    st.session_state["current_day"] = today_str

if st.session_state["current_day"] != today_str:
    # New day detected → reset view and rerun
    st.session_state["current_day"] = today_str
    st.rerun()

# ----------------------------
# Load ALL previous barcodes (global duplicate check)
# ----------------------------
if "scanned_codes" not in st.session_state:
    scanned_codes = {}

    for csv_file in glob(os.path.join(DATA_DIR, "*.csv")):
        with open(csv_file, "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    scanned_codes[row[0]] = row[1]

    st.session_state["scanned_codes"] = scanned_codes
else:
    scanned_codes = st.session_state["scanned_codes"]

# ----------------------------
# Barcode scanner
# ----------------------------
VALID_PREFIX = "SPXID06"


class BarcodeScanner(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        barcodes = pyzbar.decode(img)

        today = datetime.date.today().isoformat()
        today_csv = os.path.join(DATA_DIR, f"{today}.csv")
        today_image_dir = os.path.join(IMAGE_DIR, today)

        os.makedirs(today_image_dir, exist_ok=True)

        for barcode in barcodes:
            x, y, w, h = barcode.rect
            barcode_data = barcode.data.decode("utf-8")
            barcode_type = barcode.type

            # ❌ PREFIX CHECK (NEW)
            if not barcode_data.startswith(VALID_PREFIX):
                winsound.Beep(800, 800)

                engine = pyttsx3.init()
                engine.say("Please scan it again")
                engine.runAndWait()

                # Draw RED box for invalid barcode
                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(
                    img,
                    "INVALID CODE",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                )
                continue  # ⬅️ stop processing this barcode

            # 🔁 DUPLICATE CHECK
            if barcode_data in scanned_codes:
                winsound.Beep(1000, 1500)
                time.sleep(0.2)
                winsound.Beep(1000, 1500)

                engine = pyttsx3.init()
                engine.say("Duplicate code found")
                engine.runAndWait()
            else:
                timestamp = datetime.datetime.now().isoformat()

                # Save in memory
                scanned_codes[barcode_data] = timestamp
                st.session_state["scanned_codes"] = scanned_codes

                # Save CSV (per day)
                with open(today_csv, "a", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([barcode_data, timestamp])

                # Save image (per day)
                img_name = f"{barcode_data}_{datetime.datetime.now().strftime('%H%M%S')}.png"
                cv2.imwrite(os.path.join(today_image_dir, img_name), img)

                winsound.Beep(1200, 300)

                engine = pyttsx3.init()
                engine.say("Added to the list")
                engine.runAndWait()

            # ✅ VALID barcode → GREEN box
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                img,
                f"{barcode_data} ({barcode_type})",
                (x, y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )

        return img


# ----------------------------
# Camera
# ----------------------------
webrtc_streamer(
    key="barcode-scanner",
    video_transformer_factory=BarcodeScanner,
    media_stream_constraints={"video": True, "audio": False},
)

# ----------------------------
# Display scanned codes (session)
# ----------------------------
# ----------------------------
# Display scanned codes (today only)
# ----------------------------
import pandas as pd

st.subheader(f"✅ Scanned Barcodes ({today_str})")

today_csv = os.path.join(DATA_DIR, f"{today_str}.csv")

if os.path.exists(today_csv):
    df_today = pd.read_csv(
        today_csv,
        names=["Barcode_ID", "Timestamp"]
    )

    if not df_today.empty:
       # Parse and clean timestamps
        df_today["Timestamp"] = pd.to_datetime(df_today["Timestamp"], errors="coerce")
        df_today = df_today.dropna(subset=["Timestamp"])

        # Sort by time: latest first
        df_today = df_today.sort_values("Timestamp", ascending=False)

        # Keep only last 20 (optional)
        df_today = df_today.head(20)

        # Add row numbers AFTER sorting
        df_today.insert(0, "No.", range(1, len(df_today) + 1))

        st.dataframe(
            df_today,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No barcode scanned today.")
else:
    st.info("No barcode scanned today.")

