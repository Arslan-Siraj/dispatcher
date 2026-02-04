# DispatcherApp

**DispatcherApp** is a Streamlit-based application for real-time barcode scanning and tracking of packed products. It is designed for warehouses and logistics environments to simplify inventory tracking, ensure data integrity, and provide geolocation metadata for each scanned item.

---

## Features

- **Real-time Barcode Scanning**  
  Uses the device camera to scan barcodes in real time.

- **Duplicate Detection**  
  Automatically checks scanned barcodes to prevent duplicates.

- **Invalid Barcode Validation**  
  Ensures only barcodes with the correct prefix are accepted.

- **GPS Location Logging**  
  Captures the latitude and longitude of the scanning location and embeds it in saved images as EXIF metadata.

- **Image Capture**  
  Automatically saves an image of each scanned barcode with overlaid metadata.

- **Scanned Codes History**  
  Tracks and displays scanned barcodes for the current day, with timestamps.

- **User Feedback**  
  Provides visual alerts and audio feedback for invalid or duplicate scans using `pyttsx3` and system beeps.

- **Sidebar Branding**  
  Displays your company logo and app version at the bottom of the sidebar.

---

## Installation

1. Download from GithubActions:
