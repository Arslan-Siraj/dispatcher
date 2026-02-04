import streamlit as st
import cv2
import numpy as np
from pyzbar import pyzbar
from streamlit_webrtc import webrtc_streamer
import csv
import datetime
import winsound
import pyttsx3
import os
from glob import glob
import pandas as pd
from streamlit_webrtc import VideoProcessorBase
import av
import geocoder
from PIL import Image
import piexif
import base64
from app_helper import show_app_dev_info

# Streamlit setup (must be first Streamlit command)
st.set_page_config(page_title="Barcode Scanner", layout="centered")

show_app_dev_info()

st.title("📦 Packed Product Barcode Scanner")

DATA_DIR = "data"
IMAGE_DIR = "images"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

# Get GPS location
def get_gps_location():
    try:
        g = geocoder.ip('me')
        if g.ok:
            return g.latlng
        else:
            return [24.8607, 67.0011]  # fallback
    except:
        return [24.8607, 67.0011]  # fallback

WAREHOUSE_LAT, WAREHOUSE_LON = get_gps_location()

# Create GPS EXIF data
def create_gps_exif(lat, lon):
    def to_dms(coord):
        d = int(coord)
        m = int((coord - d) * 60)
        s = (coord - d - m/60) * 3600
        return [(d, 1), (m, 1), (int(s * 100), 100)]
    
    gps_ifd = {
        piexif.GPSIFD.GPSLatitudeRef: 'N' if lat >= 0 else 'S',
        piexif.GPSIFD.GPSLatitude: to_dms(abs(lat)),
        piexif.GPSIFD.GPSLongitudeRef: 'E' if lon >= 0 else 'W',
        piexif.GPSIFD.GPSLongitude: to_dms(abs(lon)),
    }
    exif_dict = {"GPS": gps_ifd}
    return piexif.dump(exif_dict)

# Format GPS display
def format_gps_display(lat, lon):
    def to_dms_str(coord, is_lat):
        abs_coord = abs(coord)
        d = int(abs_coord)
        m = int((abs_coord - d) * 60)
        s = (abs_coord - d - m/60) * 3600
        dir = 'N' if coord >= 0 and is_lat else 'S' if is_lat else 'E' if coord >= 0 else 'W'
        return f"{coord:.6f} / {dir} {d}° {m}' {s:.3f}''"
    
    lat_str = f"Latitude: {to_dms_str(lat, True)}"
    lon_str = f"Longitude: {to_dms_str(lon, False)}"
    return lat_str, lon_str

# Track current date (auto-rerun on day change)
today_str = datetime.date.today().isoformat()

if "current_day" not in st.session_state:
    st.session_state["current_day"] = today_str

if st.session_state["current_day"] != today_str:
    st.session_state["current_day"] = today_str
    st.rerun()

# Load ALL previous barcodes (global duplicate check)
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

# Barcode scanner
VALID_PREFIX = "SPXID06"

class BarcodeScanner(VideoProcessorBase):
    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
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

            # Timestamp
            now = datetime.datetime.now()
            timestamp = now.isoformat()
            display_time = now.strftime("%Y-%m-%d %H:%M:%S")

            # Metadata text
            prefix_text = f"Prefix: {VALID_PREFIX}"
            time_text = f"Time: {display_time}"
            gps_text = f"GPS: {WAREHOUSE_LAT}, {WAREHOUSE_LON}"

            # ❌ INVALID PREFIX
            if not barcode_data.startswith(VALID_PREFIX):
                winsound.Beep(800, 800)
                engine = pyttsx3.init()
                engine.say("Please scan it again")
                engine.runAndWait()

                cv2.rectangle(img, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(img, "INVALID CODE", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                continue

            # 🔁 DUPLICATE
            if barcode_data in scanned_codes:
                winsound.Beep(1000, 1500)
                engine = pyttsx3.init()
                engine.say("Duplicate code found")
                engine.runAndWait()
            else:
                scanned_codes[barcode_data] = timestamp
                st.session_state["scanned_codes"] = scanned_codes

                with open(today_csv, "a", newline="") as csvfile:
                    csv.writer(csvfile).writerow([barcode_data, timestamp])

                # Overlay metadata BEFORE saving image
                GREEN = (0, 255, 0)

                # Fixed position: top-left corner to avoid cutting off
                base_x = 10
                base_y = 30

                cv2.putText(
                    img, f"ID: {barcode_data}",
                    (base_x, base_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, GREEN, 3
                )

                cv2.putText(
                    img, f"Time: {display_time}",
                    (base_x, base_y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, GREEN, 3
                )

                lat_str, lon_str = format_gps_display(WAREHOUSE_LAT, WAREHOUSE_LON)
                cv2.putText(
                    img, lat_str,
                    (base_x, base_y + 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, GREEN, 3
                )
                cv2.putText(
                    img, lon_str,
                    (base_x, base_y + 90),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, GREEN, 3
                )

                img_name = f"{barcode_data}_{now.strftime('%H%M%S')}.png"
                # Save with GPS EXIF
                pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                exif_bytes = create_gps_exif(WAREHOUSE_LAT, WAREHOUSE_LON)
                pil_img.save(os.path.join(today_image_dir, img_name), exif=exif_bytes)

                winsound.Beep(1200, 300)
                engine = pyttsx3.init()
                engine.say("Added to the list")
                engine.runAndWait()

            # Draw bounding box + barcode text
            cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img, f"{barcode_data} ({barcode_type})",
                        (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 255, 0), 2)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

# Streamlit interface
webrtc_streamer(
    key="barcode-scanner",
    video_processor_factory=BarcodeScanner,
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
    media_stream_constraints={"video": True, "audio": False},
)

# Display scanned codes (today only)
st.subheader(f"✅ Scanned Barcodes ({today_str})")

today_csv = os.path.join(DATA_DIR, f"{today_str}.csv")

if os.path.exists(today_csv):
    df_today = pd.read_csv(today_csv, names=["Barcode_ID", "Timestamp"])

    if not df_today.empty:
        df_today["Timestamp"] = pd.to_datetime(df_today["Timestamp"], errors="coerce")
        df_today = df_today.dropna(subset=["Timestamp"])
        df_today = df_today.sort_values("Timestamp", ascending=False)
        df_today = df_today.head(20)
        df_today.insert(0, "No.", range(1, len(df_today) + 1))

        st.dataframe(df_today, use_container_width=True, hide_index=True)
    else:
        st.info("No barcode scanned today.")
else:
    st.info("No barcode scanned today.")
