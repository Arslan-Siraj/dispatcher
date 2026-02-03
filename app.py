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

st.set_page_config(page_title="Barcode Scanner", layout="centered")
st.title("📦 Packed Product Barcode Scanner")

if 'scanned_codes' not in st.session_state:
    scanned_codes = {}
    try:
        with open('barcodes.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:
                    scanned_codes[row[0]] = row[1]
    except FileNotFoundError:
        pass
    st.session_state["scanned_codes"] = scanned_codes
else:
    scanned_codes = st.session_state["scanned_codes"]


class BarcodeScanner(VideoTransformerBase):
    def transform(self, frame):
        img = frame.to_ndarray(format="bgr24")
        barcodes = pyzbar.decode(img)

        for barcode in barcodes:
            x, y, w, h = barcode.rect
            barcode_data = barcode.data.decode("utf-8")
            barcode_type = barcode.type

            if barcode_data in scanned_codes:
                winsound.Beep(1000, 1500)
                time.sleep(0.2)
                winsound.Beep(1000, 1500)
                engine = pyttsx3.init()
                engine.say(f"Duplicate code found")
                engine.runAndWait()
            else:
                timestamp = datetime.datetime.now().isoformat()
                scanned_codes[barcode_data] = timestamp
                st.session_state["scanned_codes"] = scanned_codes
                with open('barcodes.csv', 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow([barcode_data, timestamp])
                os.makedirs("images", exist_ok=True)
                cv2.imwrite(f"images/{barcode_data}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png", img)
                engine = pyttsx3.init()
                engine.say("Added to the list")
                engine.runAndWait()

            # Draw bounding box
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


webrtc_streamer(
    key="barcode-scanner",
    video_transformer_factory=BarcodeScanner,
    media_stream_constraints={"video": True, "audio": False},
)

st.subheader("✅ Scanned Barcodes")
if scanned_codes:
    for code, ts in scanned_codes.items():
        st.write(f"{code} - {ts}")
else:
    st.info("No barcode scanned yet.")

