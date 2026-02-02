# Barcode Scanner App

A Streamlit-based web application for scanning barcodes using your camera. It stores scanned barcodes in a CSV file with timestamps, saves photos of new scans, and alerts if a barcode is already scanned.

## Features

- Real-time barcode scanning via webcam
- Stores barcodes in `barcodes.csv` with timestamps
- Saves images of new scans in the `images/` folder
- Beeps and announces via text-to-speech if a barcode is already scanned
- Displays scanned barcodes in the web interface

## Requirements

- Python 3.7+
- Webcam access

## Installation

### Using pip (venv)

1. Clone the repository:
   ```
   git clone https://github.com/Arslan-Siraj/dispatcher.git
   cd dispatcher
   ```

2. Create a virtual environment:
   ```
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - On Windows: `.\.venv\Scripts\activate`
   - On macOS/Linux: `source .venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

### Using conda

1. Clone the repository:
   ```
   git clone https://github.com/Arslan-Siraj/dispatcher.git
   cd dispatcher
   ```

2. Create the conda environment:
   ```
   conda env create -f environment.yml
   ```

3. Activate the environment:
   ```
   conda activate dispatcher
   ```

## Usage

Run the application:
```
streamlit run app.py
```

Open the provided URL in your browser, allow camera access, and start scanning barcodes.

## Files

- `app.py`: Main application file
- `barcodes.csv`: CSV file storing scanned barcodes and timestamps
- `images/`: Folder containing saved images of scans
- `requirements.txt`: List of Python dependencies

## Dependencies

- streamlit
- opencv-python
- numpy
- pyzbar
- streamlit-webrtc
- pyttsx3

## License

[Add your license here]