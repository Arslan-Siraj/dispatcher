import streamlit as st
import cv2
import numpy as np
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase
import csv
import datetime
import winsound
import pyttsx3
import os
from glob import glob
import pandas as pd
import av
import geocoder
from PIL import Image
import piexif
from app_helper import show_app_dev_info

# --------------------------------------------------
# Streamlit setup
# --------------------------------------------------
st.set_page_config(page_title="Packed Product Entry", layout="centered")
show_app_dev_info()

st.title("📦 Packed Product – Manual Barcode Entry")

# --------------------------------------------------
# Directories
# --------------------------------------------------
DATA_DIR = "data"
IMAGE_DIR = "images"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

VALID_PREFIX = "SPXID06"

# --------------------------------------------------
# GPS
# --------------------------------------------------
def get_gps_location():
    try:
        g = geocoder.ip("me")
        if g.ok:
            return g.latlng
    except:
        pass
    return [24.8607, 67.0011]  # fallback

WAREHOUSE_LAT, WAREHOUSE_LON = get_gps_location()

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

def format_gps_display(lat, lon):
    return (
        f"Latitude: {lat:.6f}",
        f"Longitude: {lon:.6f}",
    )

# --------------------------------------------------
# Load all previously scanned barcodes (global)
# --------------------------------------------------
if "scanned_codes" not in st.session_state:
    scanned = {}
    for f in glob(os.path.join(DATA_DIR, "*.csv")):
        with open(f, "r") as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:
                    scanned[row[0]] = row[1]
    st.session_state["scanned_codes"] = scanned

scanned_codes = st.session_state["scanned_codes"]

# --------------------------------------------------
# Camera Processor
# --------------------------------------------------
class CameraProcessor(VideoProcessorBase):
    def __init__(self):
        self.frame = None

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        self.frame = img
        return frame

# --------------------------------------------------
# UI – Manual Entry
# --------------------------------------------------
st.subheader("📝 Manual Barcode Entry")

VALID_PREFIX = "SPXID06"

barcode_input = st.text_input(
    "Enter Barcode ID",
    value=VALID_PREFIX,
    key="barcode_input"
)

# Enforce prefix (auto-fix if user deletes/changes it)
if not barcode_input.startswith(VALID_PREFIX):
    barcode_input = VALID_PREFIX
    st.session_state["barcode_input"] = VALID_PREFIX

barcode_id = barcode_input.strip()
barcode_suffix = barcode_id[len(VALID_PREFIX):]

capture_btn = st.button("📸 Capture & Save")

# --------------------------------------------------
# Camera
# --------------------------------------------------
ctx = webrtc_streamer(
    key="manual-camera",
    video_processor_factory=CameraProcessor,
    media_stream_constraints={"video": True, "audio": False},
    rtc_configuration={
        "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
    },
)

# --------------------------------------------------
# Capture Logic
# --------------------------------------------------
if capture_btn:
    engine = pyttsx3.init()

    if not barcode_id:
        st.warning("Please enter Barcode ID")
        engine.say("Please enter barcode")
        engine.runAndWait()

    elif not barcode_id.startswith(VALID_PREFIX):
        winsound.Beep(800, 800)
        st.error("Invalid Barcode Prefix")
        engine.say("Invalid code")
        engine.runAndWait()

    elif barcode_id in scanned_codes:
        winsound.Beep(1000, 1500)
        st.error("Duplicate Barcode")
        engine.say("Duplicate code found")
        engine.runAndWait()

    elif ctx.video_processor and ctx.video_processor.frame is not None:
        img = ctx.video_processor.frame.copy()

        now = datetime.datetime.now()
        timestamp = now.isoformat()
        display_time = now.strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.date.today().isoformat()

        today_csv = os.path.join(DATA_DIR, f"{today}.csv")
        today_image_dir = os.path.join(IMAGE_DIR, today)
        os.makedirs(today_image_dir, exist_ok=True)

        # Save CSV
        with open(today_csv, "a", newline="") as f:
            csv.writer(f).writerow([barcode_id, timestamp])

        scanned_codes[barcode_id] = timestamp
        st.session_state["scanned_codes"] = scanned_codes

        # Overlay info (GREEN)
        GREEN = (0, 255, 0)
        x, y = 10, 30

        cv2.putText(img, f"ID: {barcode_id}", (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, GREEN, 3)

        cv2.putText(img, f"Time: {display_time}", (x, y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, GREEN, 3)

        lat_str, lon_str = format_gps_display(WAREHOUSE_LAT, WAREHOUSE_LON)

        cv2.putText(img, lat_str, (x, y + 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, GREEN, 3)
        cv2.putText(img, lon_str, (x, y + 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, GREEN, 3)

        # Save image with EXIF GPS
        img_name = f"{barcode_id}_{now.strftime('%H%M%S')}.png"
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        exif_bytes = create_gps_exif(WAREHOUSE_LAT, WAREHOUSE_LON)
        pil_img.save(os.path.join(today_image_dir, img_name), exif=exif_bytes)

        winsound.Beep(1200, 300)
        engine.say("Added to the list")
        engine.runAndWait()

        st.success("Saved successfully ✅")

    else:
        st.error("Camera not ready yet")

# --------------------------------------------------
# Today Table
# --------------------------------------------------
st.subheader(f"✅ Scanned Barcodes ({datetime.date.today().isoformat()})")

today_csv = os.path.join(DATA_DIR, f"{datetime.date.today().isoformat()}.csv")

if os.path.exists(today_csv):
    df = pd.read_csv(today_csv, names=["Barcode_ID", "Timestamp"])
    if not df.empty:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], errors="coerce")
        df = df.dropna().sort_values("Timestamp", ascending=False)
        df.insert(0, "No.", range(1, len(df) + 1))
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No barcode scanned today.")
else:
    st.info("No barcode scanned today.")
